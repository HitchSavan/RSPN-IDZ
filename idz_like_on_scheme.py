import pandas as pd
import numpy as np
import json
import sys
from xlsxwriter.utility import xl_rowcol_to_cell

# Heap Sort for possibility matrix
def heapify(arr, n, i, param):
    if param == "V":
        smallest = i  # Initialize smallest as root
        l = 2 * i + 1  # left = 2*i + 1
        r = 2 * i + 2  # right = 2*i + 2

        if l < n and arr[smallest][param] > arr[l][param]:
            smallest = l
        if r < n and arr[smallest][param] > arr[r][param]:
            smallest = r
        if smallest != i:
            (arr[i], arr[smallest]) = (arr[smallest], arr[i])  # swap
            heapify(arr, n, smallest, param)
    else:
        largest = i  # Initialize largest as root
        l = 2 * i + 1  # left = 2*i + 1
        r = 2 * i + 2  # right = 2*i + 2

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

input_file = 'init_data_example2.json'
input_file = 'init_data.json'

with open(input_file, encoding='utf-8') as json_file: # загрузка данных
    init_data = json.load(json_file)

fmax = init_data["fmax"]
f = []
for signal in init_data["signals"]:
    for i in range(signal["quantity"]):
        f.append(fmax / signal["f"])
T = [int(fmax / x) for x in f] # периоды опроса каналов

T.sort()
f.sort()
f.reverse()

print(f'Частоты сигналов: {f}\nПериоды: {T}')

ticks = int(fmax / min(f)) # кол-во тактов синхронизации
print(f'Количество тактов в кадре эксперимента: {ticks}')

# формирование матрицы потенциальных возможностей (МПВ)

sortparam = "kfree"
possibility_matrix = []

module_num = 0
channels_total = 0
for module in init_data["modules"]: 
    for i in range(module["quantity"]):
        possibility_matrix.append({
            "num": module_num,
            "V": ticks / module["channels"],
            "lfree": ticks,
            "kfree": module["channels"],
            "ktotal": module["channels"],
            "TF": [0 for x in range(ticks)], # вектор занятости
            "Ra": [x for x in range(module["channels"])] # порядок каналов
        })
        module_num += 1
    channels_total += module["channels"] * module["quantity"]

heapSort(possibility_matrix, sortparam) # сортировка МПВ
#possibility_matrix.sort(key=itemgetter('V', 'kfree'), reverse=True)

# создание таблицы расписания

table_data = {"Номер канала": [x+1 for x in range(channels_total)],
              "Номер канала в модуле": [0 for x in range(channels_total)],
              "Модуль": [0 for x in range(channels_total)],
              "Номер сигнала": [-1 for x in range(channels_total)]
              }

for i in range(ticks):
    table_data[f'Такт {i+1}'] = [0 for x in range(channels_total)]

table_data["Штраф 1"] = [0 for x in range(channels_total)]
table_data["Штраф 2"] = [0 for x in range(channels_total)]

# просто смерть, а не цикл. смотреть на свой страх и риск
big_counter = 0
i = 0
for module in init_data["modules"]: # идем по типам модулей
    for j in range(module["quantity"]): # идем по каждому модулю каждого типа
        for k in range(module["channels"]): # идем по каждому каналу каждого модуля
            table_data["Модуль"][big_counter] = i+j+1
            table_data["Номер канала в модуле"][big_counter] = k+1

            counter = 0
            reset = module["channels"]
            for m in range(ticks): # идем по каждому такту
                if counter >= reset or counter == 0:
                    counter = 0
                counter += 1
            big_counter += 1
    i += 1

table = pd.DataFrame(table_data)


# имплементация алгоритма с блок-схемы

deltal = 1 # ??
l = 0
j = 0
newCycleFlag = True
while (True):
    if (newCycleFlag):
        n = 0
    # deltal = T[j] # ??

    print(f'l={l}, deltal={deltal} ', sep=', ')
        
    if (l + deltal) <= T[j]:
        if (possibility_matrix[0]["TF"][l] == 0 and possibility_matrix[0]["kfree"] != 0):
            for i in range(int(ticks / T[j])):
                position = l + i * T[j]
                print(position, end=" ")
                possibility_matrix[0]["TF"][position] = 1 # назначение j-сигнала на l-такт модуля

                table.loc[(table['Номер канала в модуле'] == (possibility_matrix[0]["ktotal"] - possibility_matrix[0]["kfree"] + 1)) 
                          & (table['Модуль'] == (possibility_matrix[0]["num"] + 1)), [f'Такт {position + 1}']] = 1

            table.loc[(table['Номер канала в модуле'] == (possibility_matrix[0]["ktotal"] - possibility_matrix[0]["kfree"] + 1)) 
                      & (table['Модуль'] == (possibility_matrix[0]["num"] + 1)), [f'Номер сигнала']] = j+1

            if j != 0:
                p1 = [0 for x in T]
                p2 = [0 for x in T]
                for i in range(ticks):
                    if possibility_matrix[0]["TF"][i] == 1:
                        if table.loc[(table['Номер канала в модуле'] == (possibility_matrix[0]["ktotal"] - possibility_matrix[0]["kfree"] + 1)) 
                                    & (table['Модуль'] == (possibility_matrix[0]["num"] + 1)), [f'Такт {i + 1}']].iat[0, 0] == 1:
                            p1[i] += 1
                            p2[i] += min(T)/T[j]
                
                P1 = sum(p1) / (ticks * len(T))
                P2 = sum(p2) / (ticks * len(T))
            else:
                P1 = 0
                P2 = 0
            
            table.loc[(table['Номер канала в модуле'] == (possibility_matrix[0]["ktotal"] - possibility_matrix[0]["kfree"] + 1)) 
                    & (table['Модуль'] == (possibility_matrix[0]["num"] + 1)), [f'Штраф 1']] = P1
            table.loc[(table['Номер канала в модуле'] == (possibility_matrix[0]["ktotal"] - possibility_matrix[0]["kfree"] + 1)) 
                    & (table['Модуль'] == (possibility_matrix[0]["num"] + 1)), [f'Штраф 2']] = P2

            l += deltal

            print(f'{possibility_matrix[0]["TF"]}, Vb={possibility_matrix[0]["V"]}', end=", ")

            print(f'сигнал {j+1} записан в модуль {possibility_matrix[0]["num"] + 1} канал {possibility_matrix[0]["ktotal"] - possibility_matrix[0]["kfree"] + 1}')
        
            possibility_matrix[0]["lfree"] -= ticks / T[j]
            possibility_matrix[0]["kfree"] -= 1
            possibility_matrix[0]["V"] = possibility_matrix[0]["lfree"] / possibility_matrix[0]["kfree"] if possibility_matrix[0]["kfree"] != 0 else 0
            if possibility_matrix[0]["kfree"] == 0:
                possibility_matrix[0]["kfree"] = sys.maxsize # да, если каналов ноль, то каналов 9223372036854775807, так работает программирование
            print(f'Va={possibility_matrix[0]["V"]}')
            heapSort(possibility_matrix, sortparam)
            
            print(f'Следующий модуль номер {possibility_matrix[0]["num"] + 1} с количеством свободных каналов {possibility_matrix[0]["kfree"]}')

            j += 1

            if j == len(f):
                break
            newCycleFlag = True
        else:
            l += 1
            newCycleFlag = False # ???
    else:
        if n == 1:
            print(f"Не вышло составить расписание для сигнала {j+1}")
            break
        else:
            l = 0
            n += 1
            newCycleFlag = False

# отображение расписание
print(table)

# создание и форматирование эксель-файла
number_rows = len(table.index)
writer = pd.ExcelWriter('output.xlsx', engine='xlsxwriter')
table.to_excel(writer, index=False, sheet_name='report')

workbook = writer.book
worksheet = writer.sheets['report']

format1 = workbook.add_format({'bg_color': '#0FFC03'})
total_fmt = workbook.add_format({'bold': True, 'bg_color': '#5789E6'})

worksheet.conditional_format(1, 4, channels_total, 3+ticks, {'type': 'cell',
                                           'criteria': '>',
                                           'value': '0',
                                           'format': format1})

for column in range(4, 6+ticks):
    # Determine where we will place the formula
    cell_location = xl_rowcol_to_cell(number_rows+1, column)
    # Get the range to use for the sum formula
    start_range = xl_rowcol_to_cell(1, column)
    end_range = xl_rowcol_to_cell(number_rows, column)
    # Construct and write the formula
    formula = f'=SUM({start_range}:{end_range})'
    worksheet.write_formula(cell_location, formula, total_fmt)

# Add a total label
worksheet.write_string(number_rows+1, 3, "Штрафы", total_fmt)

writer.save()
'''

busy_table_data = {"Модуль/канал": ["" for x in range(channels_total)]}

for i in range(ticks):
    busy_table_data[f'Такт {i+1}'] = [0 for x in range(channels_total)]

# просто смерть, а не цикл. смотреть на свой страх и риск
big_counter = 0
for module in init_data["modules"]: # идем по типам модулей
    for j in range(module["quantity"]): # идем по каждому модулю каждого типа
        for k in range(module["channels"]): # идем по каждому каналу каждого модуля

            busy_table_data["Модуль/канал"][big_counter] = f"М{i+j+1}/К{k+1}"

            counter = 0
            reset = module["channels"]
            for m in range(ticks): # идем по каждому такту
                if counter >= reset or counter == 0:
                    busy_table_data[f'Такт {m+k+1}'][big_counter] = 1
                    counter = 0
                counter += 1
            big_counter += 1

busy_table = pd.DataFrame(busy_table_data)
# print(busy_table)

'''