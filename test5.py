import psutil

battary = psutil.sensors_battery()
pers = int(battary.percent)
print(f'Заряд батареи: {pers}%')

a=[4,5]
a