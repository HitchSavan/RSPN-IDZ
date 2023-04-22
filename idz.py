import pandas as pd
import json

with open('init_data.json', encoding='utf-8') as json_file:
    init_data = json.load(json_file)

fmax = init_data["fmax"]
f = [fmax / x for x in init_data["fchannels"]]
T = [1 / x for x in f] # периоды опроса каналов

channels_total = 0
for i in range(len(init_data["modules"])):
    channels_total += init_data["modules"][i] * init_data["channels"][i]

table_data = {"Номер канала": [x+1 for x in range(channels_total)],
              "Номер канала в модуле": [0 for x in range(channels_total)],
              "Модуль": [0 for x in range(channels_total)],
              "Частота сигнала на канал": [fmax for x in range(channels_total)],
              "Штраф": [0 for x in range(channels_total)]
              }

busy_table_data = {"Модуль/канал": ["" for x in range(channels_total)]}

place = 0
for i in range(len(init_data["modules"])):
    for j in range(init_data["modules"][i]):
        for k in range(init_data["channels"][i]):
            table_data["Модуль"][place] = i+j+1
            table_data["Номер канала в модуле"][place] = k+1

            busy_table_data["Модуль/канал"][place] = f"М{i+j+1}/К{k+1}"

            place += 1

ticks = int(fmax / min(f)) # кол-во тактов синхронизации

for i in range(ticks):
    table_data[f'Такт {i+1}'] = [0 for x in range(channels_total)]
    busy_table_data[f'Такт {i+1}'] = [0 for x in range(channels_total)]

# просто смерть, а не цикл. смотреть на свой страх и риск
big_counter = 0
for i in range(len(init_data["modules"])): # идем по типам модулей
    for j in range(init_data["modules"][i]): # идем по каждому модулю каждого типа
        for k in range(init_data["channels"][i]): # идем по каждому каналу каждого модуля
            counter = 0
            reset = init_data["channels"][i]
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

f.sort()
f.reverse()


print(f'Частоты сигналов: {f}')

