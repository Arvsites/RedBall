import cv2
import numpy as np
import serial.tools.list_ports
import time


# Ищем доступные COM-порты
ports = list(serial.tools.list_ports.comports())

arduino_port = None

# # Перебираем найденные порты
# for port in ports:
#     if "Arduino" in port.description:
#         arduino_port = port.device
#         break
#
# if arduino_port is not None:
#     print(f"Arduino найден на порту {arduino_port}")
#     arduino = serial.Serial(arduino_port, 115200)
#     time.sleep(2)
# else:
#     print("Arduino не найден")

# Создание объекта VideoCapture для захвата видео
video_capture = cv2.VideoCapture(0)  # 0 означает использование встроенной камеры

# Проверка, удалось ли открыть видеопоток
if not video_capture.isOpened():
    print("Не удалось открыть видеопоток")
    exit()

while True:
    # Захват кадра из видеопотока
    ret, frame = video_capture.read()

    # Проверка, удалось ли захватить кадр
    if not ret:
        print("Не удалось захватить кадр")
        break
    # Преобразование изображения из BGR в HSV цветовое пространство
    hsv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Определение диапазона красного цвета в HSV
    lower_red = np.array([35, 50, 50])
    upper_red = np.array([60, 255, 255])
    mask1 = cv2.inRange(hsv_image, lower_red, upper_red)

    lower_red = np.array([170, 80, 50])
    upper_red = np.array([180, 255, 255])
    mask2 = cv2.inRange(hsv_image, lower_red, upper_red)


    # Объединение двух масок для получения окончательной маски
    final_mask = mask1 + mask2

    # Применение маски к изображению
    masked_image = cv2.bitwise_and(frame, frame, mask=final_mask)

    # Поиск контуров на маске
    contours, _ = cv2.findContours(final_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Инициализация переменных для поиска самого большого контура
    max_area = 0
    max_contour = None
    for contour in contours:
        area = cv2.contourArea(contour)
        # Если площадь текущего контура больше, чем предыдущий максимум, обновляем значения
        if area > max_area:
            max_area = area
            max_contour = contour

    # Отображение только самого большого контура
    if max_contour is not None:
        (x, y, w, h) = cv2.boundingRect(max_contour)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # Отображение исходного изображения и результата
    cv2.imshow('Video', frame)
    # print("центр мяча: ", x+w/2, y+h/2)
    cv2.imshow('Masked Image', masked_image)

    # #пример кода для отправки координат на arduino
    # if x+w/2 > 160:
    #     arduino.write(b'1')
    # elif x+w/2 <140:
    #     arduino.write(b'2')
    # Определение диапазона красного цвета в HSV


    # Проверка нажатия клавиши 'q' для выхода из программы
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Освобождение ресурсов
video_capture.release()
cv2.destroyAllWindows()