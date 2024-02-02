# Библиотеки для установки: opencv-python, numpy, pyserial
import cv2
import numpy as np
import serial.tools.list_ports
import time


#________________________Начало_настройки_параметров_____________________________
cam = 0                             # 0 использование встроенной камеры, 1 web камеры
HSV_red_lower_1 = [0, 50, 50]       # Нижняя граница HSV для красного цвета 1
HSV_red_upper_1 = [10, 255, 255]    # Верхняя граница HSV для красного цвета 1
HSV_red_lower_2 = [170, 80, 50]     # Нижняя граница HSV для красного цвета 2
HSV_red_upper_2 = [180, 255, 255]   # Верхняя граница HSV для красного цвета 2
HSV_green_lower_1 = [35, 50, 50]    # Нижняя граница HSV для зеленого цвета
HSV_green_upper_1 = [60, 255, 255]  # Верхняя граница HSV для зеленого цвета
y_boom = 12                         # % от экрана, где будет проходит граница срабатывания удара
period = 0.03                        # Время в секундах того, как часто будет обрабатываться и высылаться координаты
#________________________Конец_настройки_параметров______________________________


# Serial соединение
ports = list(serial.tools.list_ports.comports())
arduino_port = None
for port in ports:
    if "Arduino" in port.description:
        arduino_port = port.device
        break
if arduino_port is not None:
    print(f"Arduino найден на порту {arduino_port}")
    arduino = serial.Serial(arduino_port, 115200)
    time.sleep(2)
else:
    print("Arduino не найден")

video_capture = cv2.VideoCapture(cam)
if not video_capture.isOpened():
    print("Не удалось открыть видеопоток")
    exit()

width = video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)
height = video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
fps = video_capture.get(cv2.CAP_PROP_FPS)

# Выводим параметры
print(f"Ширина кадра: {width}")
print(f"Высота кадра: {height}")
print(f"Частота кадров: {fps}")


while True:
    ret, frame = video_capture.read()
    if not ret:
        print("Не удалось захватить кадр")
        break
    hsv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Определение красного
    lower_red = np.array(HSV_red_lower_1)
    upper_red = np.array(HSV_red_upper_1)
    mask1 = cv2.inRange(hsv_image, lower_red, upper_red)
    lower_red = np.array(HSV_red_lower_2)
    upper_red = np.array(HSV_red_upper_2)
    mask2 = cv2.inRange(hsv_image, lower_red, upper_red)
    final_mask = mask1 + mask2
    masked_image = cv2.bitwise_and(frame, frame, mask=final_mask)
    contours, _ = cv2.findContours(final_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    max_area = 0
    max_contour = None
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > max_area:
            max_area = area
            max_contour = contour
    if max_contour is not None:
        (x, y, w, h) = cv2.boundingRect(max_contour)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        xR = x+w/2
        yR = y+h/2
        print("Центр красного: ", xR, yR)
    cv2.imshow('Video', frame)
    cv2.imshow('Masked Image R', masked_image)

    # Определение зеленого
    lower_green = np.array(HSV_green_lower_1)
    upper_green = np.array(HSV_green_upper_1)
    mask3 = cv2.inRange(hsv_image, lower_green, upper_green)
    masked_image = cv2.bitwise_and(frame, frame, mask=mask3)
    contours, _ = cv2.findContours(mask3, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    max_area2 = 0
    max_contour2 = None
    for contour2 in contours:
        area2 = cv2.contourArea(contour2)
        if area2 > max_area2:
            max_area2 = area2
            max_contour2 = contour2
    if max_contour2 is not None:
        (x2, y2, w2, h2) = cv2.boundingRect(max_contour2)
        cv2.rectangle(frame, (x2, y2), (x2 + w2, y2 + h2), (0, 0, 255), 2)
        xG = x2+w2/2
        yG = y2+h2/2
        print("Центр зеленого: ", xG, yG)
    cv2.imshow('Video', frame)
    cv2.imshow('Masked Image G', masked_image)

    #________________Начало_кода_отправки_данных_на_плату_Arduino__________________________________
    if arduino_port is not None and max_contour is not None and  max_contour2 is not None:
        if xR - xG > 10 and xR - xG < 50:           # Если разница между роботом и шариком по х мала, то скорость 1 (влево)
            arduino.write(b'1')
        elif xR - xG < -10:                         # Если разница между роботом и шариком по х мала, то скорость 1 (вправо)
            arduino.write(b'2')
        elif xR - xG > 10 and xR - xG < 50:         # Если разница между роботом и шариком по х велика, то скорость 2 (влево)
            arduino.write(b'3')
        elif xR - xG < -10:                         # Если разница между роботом и шариком по х велика, то скорость 2 (вправо)
            arduino.write(b'4')
        else:
            arduino.write(b'0')                     # Остановка робота

        if yR < height*(100-y_boom)/100:
            arduino.write(b'9')                     # Активация ударного механизма после того, как шар по y пересечет черту

        time.sleep(period)
    #________________Конец_кода_отправки_данных_на_плату_Arduino_____________________________________


    # Проверка нажатия клавиши 'q' для выхода из программы
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Освобождение ресурсов
video_capture.release()
cv2.destroyAllWindows()