import pandas as pd
import json

# Heap Sort for possibility matrix
def heapify(arr, n, i):
    smallest = i  # Initialize smallest as root
    l = 2 * i + 1  # left = 2*i + 1
    r = 2 * i + 2  # right = 2*i + 2

    if l < n and arr[i]["V"] > arr[l]["V"]:
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
T = [fmax / x for x in f] # периоды опроса каналов

T.sort()
f.sort()
f.reverse()

print(f'Частоты сигналов: {f}\nПериоды: {T}')

ticks = int(fmax / min(f)) # кол-во тактов синхронизации

possibility_matrix = []

channels_total = 0
for module in init_data["modules"]: # формирование матрицы потенциальных возможностей (МПВ)
    for i in range(module["quantity"]):
        possibility_matrix.append({
                "V": ticks / module["channels"],
                "lfree": ticks,
                "kfree": module["channels"],
                "ktotal": module["channels"],
                "TF": [0 for x in range(ticks)], # вектор занятости
                "Ra": [x for x in range(module["channels"])] # порядок каналов
        })
    channels_total += module["channels"] * module["quantity"]

heapSort(possibility_matrix) # сортировка МПВ

deltal = 1 # ??
l = 0
j = 0
newCycleFlag = True
while (True):
    if(newCycleFlag):
        n = 0
    deltal = T[j]
    # for i in range(ticks / deltal): # что-то с укладыванием в такты
        
    if (l + deltal) < ticks:
        if (possibility_matrix[0]["TF"][l] == 0):

            possibility_matrix[0]["TF"][l] = 1 # назначение j-сигнала на l-такт модуля
            ##### штраф
            l += deltal
        else:
            l += 1
            newCycleFlag = False
    else:
        if n == 1:
            print("Не вышло составить расписание")
            break
        else:
            l = 0
            n += 1
            newCycleFlag = False

    possibility_matrix[0]["lfree"] -= ticks / deltal
    possibility_matrix[0]["kfree"] -= 1
    possibility_matrix[0]["V"] = possibility_matrix[0]["lfree"] / possibility_matrix[0]["ktotal"]
    heapSort(possibility_matrix)

    j += 1

    if j == len(f)-1:
        break
    newCycleFlag = True




table_data = {"Номер канала": [x+1 for x in range(channels_total)],
              "Номер канала в модуле": [0 for x in range(channels_total)],
              "Модуль": [0 for x in range(channels_total)],
              "Частота сигнала на канал": [fmax for x in range(channels_total)],
              "Штраф": [0 for x in range(channels_total)]
              }



busy_table_data = {"Модуль/канал": ["" for x in range(channels_total)]}

for i in range(ticks):
    table_data[f'Такт {i+1}'] = [0 for x in range(channels_total)]
    busy_table_data[f'Такт {i+1}'] = [0 for x in range(channels_total)]

# просто смерть, а не цикл. смотреть на свой страх и риск
big_counter = 0
for module in init_data["modules"]: # идем по типам модулей
    for j in range(module["quantity"]): # идем по каждому модулю каждого типа
        for k in range(module["channels"]): # идем по каждому каналу каждого модуля
            table_data["Модуль"][big_counter] = i+j+1
            table_data["Номер канала в модуле"][big_counter] = k+1

            busy_table_data["Модуль/канал"][big_counter] = f"М{i+j+1}/К{k+1}"

            counter = 0
            reset = module["channels"]
            for m in range(ticks): # идем по каждому такту
                if counter >= reset or counter == 0:
                    busy_table_data[f'Такт {m+k+1}'][big_counter] = 1
                    counter = 0
                counter += 1
            big_counter += 1


table = pd.DataFrame(table_data)
busy_table = pd.DataFrame(busy_table_data)
print(table)
print(busy_table)

