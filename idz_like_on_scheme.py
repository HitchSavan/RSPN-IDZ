import pandas as pd
import json
from operator import itemgetter

# Heap Sort for possibility matrix
def heapify(arr, n, i):
    smallest = i  # Initialize smallest as root
    l = 2 * i + 1  # left = 2*i + 1
    r = 2 * i + 2  # right = 2*i + 2

    if l < n and arr[smallest]["V"] > arr[l]["V"]:
        smallest = l
    if r < n and arr[smallest]["V"] > arr[r]["V"]:
        smallest = r
    if smallest != i:
        (arr[i], arr[smallest]) = (arr[smallest], arr[i])  # swap
        heapify(arr, n, smallest)
 
def heapSort(arr):
    try:
        x = arr[0]["V"]
    except Exception as err:
        print("Сортировка МПВ не удалась - неправильный формат или матрица пуста")
    n = len(arr)
    for i in range(n // 2 - 1, -1, -1):
        heapify(arr, n, i)
    for i in range(n - 1, 0, -1):
        (arr[i], arr[0]) = (arr[0], arr[i])  # swap
        heapify(arr, i, 0)


with open('init_data.json', encoding='utf-8') as json_file: # загрузка данных
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

heapSort(possibility_matrix) # сортировка МПВ
#possibility_matrix.sort(key=itemgetter('V', 'kfree'), reverse=True)

# создание таблицы расписания

table_data = {"Номер канала": [x+1 for x in range(channels_total)],
              "Номер канала в модуле": [0 for x in range(channels_total)],
              "Модуль": [0 for x in range(channels_total)],
              "Частота сигнала на канал": [fmax for x in range(channels_total)],
              "Номер сигнала": [-1 for x in range(channels_total)],
              "Штраф 1": [0 for x in range(channels_total)],
              "Штраф 2": [0 for x in range(channels_total)]
              }

for i in range(ticks):
    table_data[f'Такт {i+1}'] = [0 for x in range(channels_total)]

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
                      & (table['Модуль'] == (possibility_matrix[0]["num"] + 1)), [f'Номер сигнала']] = j

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

            table.loc[(table['Номер канала в модуле'] == (possibility_matrix[0]["ktotal"] - possibility_matrix[0]["kfree"] + 1)) 
                    & (table['Модуль'] == (possibility_matrix[0]["num"] + 1)), [f'Штраф 1']] = P1
            table.loc[(table['Номер канала в модуле'] == (possibility_matrix[0]["ktotal"] - possibility_matrix[0]["kfree"] + 1)) 
                    & (table['Модуль'] == (possibility_matrix[0]["num"] + 1)), [f'Штраф 2']] = P2

            l += deltal

            print(f'{possibility_matrix[0]["TF"]}, Vb={possibility_matrix[0]["V"]}', end=", ")

            print(f'сигнал {j+1} записан в модуль {possibility_matrix[0]["num"] + 1} канал {possibility_matrix[0]["ktotal"] - possibility_matrix[0]["kfree"] + 1}')
        
            possibility_matrix[0]["lfree"] -= ticks / T[j]
            possibility_matrix[0]["kfree"] -= 1
            possibility_matrix[0]["V"] = possibility_matrix[0]["lfree"] / possibility_matrix[0]["ktotal"]
            print(f'Va={possibility_matrix[0]["V"]}')
            heapSort(possibility_matrix)
            #possibility_matrix.sort(key=itemgetter('V', 'kfree'), reverse=True)

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

print(table)

table.to_excel("output.xlsx")
'''
writer = pd.ExcelWriter('output.xlsx', engine='xlsxwriter')
table.to_excel(writer, 'Sheet1', index=False)
wb = writer.book
ws = writer.sheets['Sheet1']
ws.add_table('G2:V32', {'style': 'Table Style Medium 20'})
writer.save()
'''
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