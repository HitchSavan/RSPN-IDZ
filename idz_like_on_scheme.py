import pandas as pd
import json
import sys
from xlsxwriter.utility import xl_rowcol_to_cell

# Пирамидальная сортировка (n log(n)) модулей, n - кол-во модулей
def heapify(arr, n, i, param):
    if param == "V":
        smallest = i  # сортируем по убыванию
        l = 2 * i + 1
        r = 2 * i + 2

        if l < n and arr[smallest][param] > arr[l][param]:
            smallest = l
        if r < n and arr[smallest][param] > arr[r][param]:
            smallest = r
        if smallest != i:
            (arr[i], arr[smallest]) = (arr[smallest], arr[i])  # swap
            heapify(arr, n, smallest, param)
    else: #если параметр не V сортируеми по возрастанию
        largest = i
        l = 2 * i + 1
        r = 2 * i + 2

        if l < n and arr[largest][param] < arr[l][param]:
            largest = l
        if r < n and arr[largest][param] < arr[r][param]:
            largest = r
        if largest != i:
            (arr[i], arr[largest]) = (arr[largest], arr[i])  # swap
            heapify(arr, n, largest, param)
 
def heapSort(arr, param):
    try:
        x = arr[0][param]
    except Exception as err:
        print("Сортировка МПВ не удалась - неправильный формат или матрица пуста")
    n = len(arr)
    for i in range(n // 2 - 1, -1, -1):
        heapify(arr, n, i, param)
    for i in range(n - 1, 0, -1):
        (arr[i], arr[0]) = (arr[0], arr[i])  # swap
        heapify(arr, i, 0, param)

# Функция составления расписания
def schedule_solver(init_data, freq_koeff = 1): #на входе данные и коэф 
    fmax = init_data["fmax"] * freq_koeff #макс частота по файлу * Кус
    f = []
    for signal in init_data["signals"]: #вычисление фактических частот 
        for i in range(signal["quantity"]): #от 0 до кол-ва этих сигоналов
            f.append(fmax / (signal["f"] * freq_koeff))
    T = [int(fmax / x) for x in f] # вычисление периодов опроса каналов

    T.sort() #сорт периодов
    f.sort() #сорт частот
    f.reverse() #частоты по убыванию

    print(f'Частоты сигналов: {f}\nПериоды: {T}') #вывод периодов и частот в консоль

    ticks = int(fmax / min(f)) # кол-во тактов синхронизации, целочисл
    i = 1 #если не степень 2, доходим доближайшей степени двойки с запасом, код влоб
    while i < ticks: #пока не больше того что у нас есть
        i *= 2 #добавляем степень двойки
    ticks = i 

    print(f'Количество тактов в кадре эксперимента: {ticks}') #выводим кол-во тактов

    # Формирование матрицы потенциальных возможностей (МПВ)
    sortparam = "V" 
    sortparam = "kfree"
    possibility_matrix = [] #массив модулей

    module_num = 0
    channels_total = 0
    for module in init_data["modules"]: #для кождого из типов модулей
        for i in range(module["quantity"]): #по их количеству
            possibility_matrix.append({ #добавляем новые элементы в пустой массив от явл словариком
                "num": module_num, #пордковый номер модуля
                "V": ticks / module["channels"], #весовая хар-ка модуля
                "lfree": ticks, #скок свободных тактов
                "kfree": module["channels"], #кол-во свободных каналов
                "ktotal": module["channels"], #сколько всего в модуле каналов
                "TF": [0 for x in range(ticks)], # вектор занятости 
                "Ra": [x for x in range(module["channels"])] # порядок каналов (не использовался)
            })
            module_num += 1 #счетчик порядкового номера модуля
        channels_total += module["channels"] * module["quantity"] #счетчик общего кол-ва каналов

    heapSort(possibility_matrix, sortparam) # сортировка МПВ по кол-ву совободных каналов, пирамидальная сортировка, начинается на 33 строчке
# с 6 по 33 стандартная сортировка "кучек"
    # Создание таблицы расписания, это словарик
    table_data = {"Номер канала": [x+1 for x in range(channels_total)], #формируем внешний вид таблицы экселя
                "Номер канала в модуле": [0 for x in range(channels_total)],
                "Модуль": [0 for x in range(channels_total)],
                "Номер сигнала": [-1 for x in range(channels_total)] #-1 значит там пока ничего не записано
                }

    for i in range(ticks): #добавляем столбцы с тактами
        table_data[f'Такт {i+1}'] = [0 for x in range(channels_total)] #по i от 0 до кол-ва тактов

    table_data["Штраф 1"] = [0 for x in range(channels_total)] #пока забиты нулями
    table_data["Штраф 2"] = [0 for x in range(channels_total)]

    # Просто смерть, а не цикл
    big_counter = 0 #текущая строчка
    i = 0
    for module in init_data["modules"]: # идем по типам модулей
        for j in range(module["quantity"]): # идем по каждому модулю каждого типа
            for k in range(module["channels"]): # идем по каждому каналу каждого модуля
                table_data["Модуль"][big_counter] = i+1 #в столбец модуля записываем его порядковый номер
                table_data["Номер канала в модуле"][big_counter] = k+1 #локальный номер модуля

                big_counter += 1
            i += 1

    table = pd.DataFrame(table_data) #табл перегоняем в датафрейм (формат табличный (условно))

    # Имплементация алгоритма с блок-схемы = заполнение МПВ и таблицы расписания
    deltal = 1 #погрешность датирования  в тактах (с ее слов она =1)
    l = 0 #текущий такт
    j = 0 #номер текущего игнала 
    newCycleFlag = True #флаг кот показывает надо ли обнулять n 
    success = False #возвращается если удалось составить расписание, нужно для строчки 244
    while (True): #бесконечный цикл

        if (newCycleFlag): #если на новом цикле, то n обнуляем, если нет то строка 187-190
            n = 0
            
        if (l + deltal) <= T[j]: #условие первого ромбика
            if (possibility_matrix[0]["TF"][l] == 0 and possibility_matrix[0]["kfree"] != 0): #проверка матрицы пот возможностей в массиве TF если на текущ такте 0 и при этом есть хоть один свободный канал, то мы назвачаем, см 184
                for i in range(int(ticks / T[j])): # назначение j-сигнала на l-такт модуля, смотрим сколько раз должны назначить сигнал
                    position = l + i * T[j] #текущая позиция такта * период (это шаг между тактами в строке)
                    possibility_matrix[0]["TF"][position] = 1 #в вектор занятости модуля указываем что он занят

                    table.loc[(table['Номер канала в модуле'] == (possibility_matrix[0]["ktotal"] - possibility_matrix[0]["kfree"] + 1)) #постновка 1 в таблице
                            & (table['Модуль'] == (possibility_matrix[0]["num"] + 1)), [f'Такт {position + 1}']] = 1 #и при этом номер модуля это номер текущего модуля, указываем конкретный такт, который занят. Этот цикл пробегает по всей строчке
                
                # Запись номера сигнала
                table.loc[(table['Номер канала в модуле'] == (possibility_matrix[0]["ktotal"] - possibility_matrix[0]["kfree"] + 1)) 
                        & (table['Модуль'] == (possibility_matrix[0]["num"] + 1)), [f'Номер сигнала']] = j+1 #в соотв колонку записываем порядковый номер сигнала
                
                # Расчет штрафов
                if j != 0: #если порядковый номер сигнала не равен 0 (для него штраф всегда 0)
                    p1 = [0 for x in range(ticks)] #это идем по псевдокоду с псевдометоды
                    p2 = [0 for x in range(ticks)]
                    for i in range(ticks):
                        if possibility_matrix[0]["TF"][i] == 1: # если вектор занятости занят
                            if table.loc[(table['Номер канала в модуле'] == (possibility_matrix[0]["ktotal"] - possibility_matrix[0]["kfree"] + 1)) 
                                        & (table['Модуль'] == (possibility_matrix[0]["num"] + 1)), [f'Такт {i + 1}']].iat[0, 0] == 1:
                                p1[i] += 1 
                                p2[i] += min(T)/T[j] # и так для каждого такта
                    
                    P1 = sum(p1) / (ticks * len(T)) #расчет больших P, сумма всех малышей р
                    P2 = sum(p2) / (ticks * len(T)) 
                else: #если работаем с первым сигналом штрафи равны нулю, пишу это ниже проверяй
                    P1 = 0 
                    P2 = 0
                            
                table.loc[(table['Номер канала в модуле'] == (possibility_matrix[0]["ktotal"] - possibility_matrix[0]["kfree"] + 1))  # запись штрафов в конкретные строчки
                        & (table['Модуль'] == (possibility_matrix[0]["num"] + 1)), [f'Штраф 1']] = P1
                table.loc[(table['Номер канала в модуле'] == (possibility_matrix[0]["ktotal"] - possibility_matrix[0]["kfree"] + 1)) 
                        & (table['Модуль'] == (possibility_matrix[0]["num"] + 1)), [f'Штраф 2']] = P2
                #дальше по блок схеме L плюс дельта L
                l += deltal 

                print(f'Сигнал {j+1} записан в модуль {possibility_matrix[0]["num"] + 1} канал {possibility_matrix[0]["ktotal"] - possibility_matrix[0]["kfree"] + 1}')
            
                # Изменение параметров МПВ
                possibility_matrix[0]["lfree"] -= ticks / T[j] #кол-во свободных тактов уменьшается на знач кол-ва тактов / на период сигнала
                possibility_matrix[0]["kfree"] -= 1 #кол-во своб каналов уменьшается на 1
                possibility_matrix[0]["V"] = possibility_matrix[0]["lfree"] / possibility_matrix[0]["kfree"] if possibility_matrix[0]["kfree"] != 0 else 0 #пересчитывается вес + проверка деления на 0
                if possibility_matrix[0]["kfree"] == 0: #если каналы закончились
                    possibility_matrix[0]["kfree"] = sys.maxsize # да, если каналов ноль, то каналов 9223372036854775807, так работает программирование

                # Пересортировка МПВ по кол-ву свободных каналов
                heapSort(possibility_matrix, sortparam) #чтобы мы забыли про модуль с 0 свобод каналов мы топим его чтобы мы его не трогали = костыль

                j += 1 #переключаемся на новый сигнал

                if j == len(f): #если j=кол-ву каналов то все зашибись и все назначили
                    success = True
                    break #выход из бесконечного цикла, УРА
                newCycleFlag = True
            else: #если такт синхронизации занят, сдвигаем на 1 и проверяем занят ли он
                l += 1
                newCycleFlag = False
        else:
            if n == 1:
                print(f"Не вышло составить расписание для сигнала {j+1}, увеличим частоту опроса в 2 раза")
                break
            else:
                l = 0 #если текущий такт меньше или равен периоду
                n += 1 
                newCycleFlag = False #выставляем флаг
    
    return (success, table, ticks, channels_total)


# Формат входных данных - JSON-файл
# "signals" и "modules" - массивы JSON-объектов
'''
{
    "fmax": максимальная частота сигналов,
    "signals": [
        {
            "f": делитель частоты сигнала (фактическая частота сигналов - fmax/f),
            "tau": параметр синхронизации сигнала,
            "quantity": количество сигналов с данной частотой
        },
        {
            "f": 32,
            "tau": 0,
            "quantity": 8
        }],
    "modules": [{
            "channels": количество каналов,
            "quantity": количество модулей с данным количеством каналов
        },
        {
            "channels": 2,
            "quantity": 2
        },
        {
            "channels": 4,
            "quantity": 3
        },
        {
            "channels": 8,
            "quantity": 2
        }]
}
'''

# тут начинается начало работы программы
if __name__ == '__main__':
    # Название файла со входными данными
    input_file = 'init_data.json'  

    with open(input_file, encoding='utf-8') as json_file: # загрузка данных
        init_data = json.load(json_file)

    # Попытка составить расписание, в случае неудачи - увеличивание частоты опроса в 2 раза
    freq_koeff = 1 #коэф кот умножается при неудаче на 2, 1й раз увеличивать не надо
    success = False 
    while success == False:
        (success, table, ticks, channels_total) = schedule_solver(init_data, freq_koeff) #составление расписания
        freq_koeff *= 2

    # Отображение расписания в консоль
    print(table)

    # Создание и форматирование эксель-файла
    number_rows = len(table.index) #кол-во строк
    writer = pd.ExcelWriter('DrozdovaTulkina.xlsx', engine='xlsxwriter') #конвертируем в эксель
    table.to_excel(writer, index=False, sheet_name='report')

    workbook = writer.book #эксельная книга
    worksheet = writer.sheets['report'] #названия активного листа

    format1 = workbook.add_format({'bg_color': '#EE82EE'}) #подсвечивание зеленым цветом
    total_fmt = workbook.add_format({'bold': True, 'bg_color': '#CD853F'}) #формат для штрафов (жирный шрифт и цвет фона)

    worksheet.conditional_format(1, 4, channels_total, 3+ticks, {'type': 'cell', #выбираем диапазон, ticks - такты
                                            'criteria': '>', #если больше
                                            'value': '0', #нуля
                                            'format': format1}) #применяем формат1

    for column in range(4, 6+ticks): #цикл по столбцам
        cell_location = xl_rowcol_to_cell(number_rows+1, column) #выбираем по ячейке в строке
        start_range = xl_rowcol_to_cell(1, column) #откуда докуда
        end_range = xl_rowcol_to_cell(number_rows, column)
        formula = f'=SUM({start_range}:{end_range})' #от  начала до конца
        worksheet.write_formula(cell_location, formula, total_fmt) #записывем формулу в ячейку cell_location с форматом жирного шрифта и синего фона

    worksheet.write_string(number_rows+1, 3, "Штрафы", total_fmt) # добавление легенды

    writer.close() #сохранение файла