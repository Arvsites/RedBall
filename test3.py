import time
from threading import Thread

flag = 1
def remind():
    time.sleep(1)
    global flag
    flag = 1
    print('boom')
    pass

yR = 800

n_boom = 0
n_color = 0

y_boom = 15
x_boom = 612
x_color = 315

array_zone = [0,100,200,300,400,500,600,700]

for i in array_zone:
    if i < x_boom:
        n_boom += 1
    else:
        break
for i in array_zone:
    if i < x_color:
        n_color += 1
    else:
        break

if n_color - n_boom >= 1:
    data = "1"
elif n_color - n_boom <= -1:
    data = "2"
else:
    data = "0"

if 700 * (100 - y_boom) / 100 <= yR:
    if flag == 1:
        flag = 0
        data = "3"
        th = Thread(target=remind, args=())
        # И запускаем его
        th.start()

    # функция для удара робота, чтоб не ударял много раз подряд




print(data, n_boom, n_color)
q =n_color - n_boom
print(700 * (100 - y_boom) / 100)
