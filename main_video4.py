# Библиотеки для установки: opencv-python, numpy, pyserial
import cv2
import numpy as np
import self as self
import serial.tools.list_ports
import time
import matplotlib.pyplot as plt


#________________________Начало_настройки_параметров_____________________________
serial_speed = 115200               # Скорость передачи данных по Serial
cam = 0                             # 0 использование встроенной камеры, 1 web камеры
HSV_red_lower_1 = [0, 50, 50]       # Нижняя граница HSV для красного цвета 1
HSV_red_upper_1 = [10, 255, 255]    # Верхняя граница HSV для красного цвета 1
HSV_red_lower_2 = [170, 80, 50]     # Нижняя граница HSV для красного цвета 2
HSV_red_upper_2 = [180, 255, 255]   # Верхняя граница HSV для красного цвета 2
HSV_green_lower_1 = [35, 50, 50]    # Нижняя граница HSV для зеленого цвета
HSV_green_upper_1 = [60, 255, 255]  # Верхняя граница HSV для зеленого цвета
y_boom = 12                         # % от экрана, где будет проходит граница срабатывания удара
period = 0.03                       # Время в секундах того, как часто будет обрабатываться и высылаться координаты
boardR = 89                         # % от экрана правый борт
boardL = 5                          # % от экрана левый борт
delta = 0                           # Коэфициент коррректировки отражения
#________________________Конец_настройки_параметров______________________________

# Автоматический поиск и подключение по Serial с Arduino
class Serial_arduino:
    ports = list(serial.tools.list_ports.comports())
    arduino_port = None
    for port in ports:
        if "Arduino" in port.description:
            arduino_port = port.device
            break
    if arduino_port is not None:
        print(f"Arduino найден на порту {arduino_port}")
        arduino = serial.Serial(arduino_port, serial_speed)
        time.sleep(2)
    else:
        print("Arduino не найден")

class Detect_color:
    def __init__(self, color, HSV_color_lower_1, HSV_color_upper_1, HSV_color_lower_2, HSV_color_upper_2):
        self.color = color
        self.HSV_color_lower_1 = HSV_color_lower_1
        self.HSV_color_upper_1 = HSV_color_upper_1
        self.HSV_color_lower_2 = HSV_color_lower_2
        self.HSV_color_upper_2 = HSV_color_upper_2
        self.asdf = color
    def detect(self, hsv_image, frame):
        self.hsv_image = hsv_image
        self.frame = frame
        lower_color = np.array(self.HSV_color_lower_1)
        upper_color = np.array(self.HSV_color_upper_1)
        mask1 = cv2.inRange(self.hsv_image, lower_color, upper_color)
        lower_color = np.array(self.HSV_color_lower_2)
        upper_color = np.array(self.HSV_color_upper_2)
        mask2 = cv2.inRange(self.hsv_image, lower_color, upper_color)
        final_mask = mask1 + mask2
        masked_image = cv2.bitwise_and(self.frame, self.frame, mask=final_mask)
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
            cv2.rectangle(self.frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            xR = x + w / 2
            yR = y + h / 2
            # print("Центр красного: ", xR, yR)
        cv2.imshow('Video', frame)
        cv2.imshow(f'Masked Image {self.color}', masked_image)


# Функция для рисования прямой на кадре
def draw_line(frame, slope, intercept, color):
    height, width, _ = frame.shape
    # Находим две точки на прямой, используя коэффициенты наклона и смещение
    x1 = width*boardL/100
    y1 = int(slope * x1 + intercept)
    x2 = width*boardR/100
    y2 = int(slope * x2 + intercept)
    # Рисуем линию на кадре
    cv2.line(frame, (int(x1), y1), (int(x2), y2), color, 2)

if __name__ == "__main__":
    Serial_arduino()

    video_capture = cv2.VideoCapture(cam)
    if not video_capture.isOpened():
        print("Не удалось открыть видеопоток")
        exit()

    x0, y0 = 1, 1
    lst = [(0, 0), (0, 0), (0, 0), (0, 0), (0, 0)]
    width = video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = video_capture.get(cv2.CAP_PROP_FPS)
    # Выводим параметры
    print(f"Ширина кадра: {width}")
    print(f"Высота кадра: {height}")
    print(f"Частота кадров: {fps}")

    Red = Detect_color("Red", HSV_red_lower_1, HSV_red_upper_1, HSV_red_lower_2, HSV_red_upper_2)

    while True:
        ret, frame = video_capture.read()
        if not ret:
            print("Не удалось захватить кадр")
            break
        hsv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # Рисуем линию сработки удара
        draw_line(frame, 0, height*((100-y_boom)/100), (40, 12, 33))
        # Рисуем линию правого борта
        cv2.line(frame, (int(width*boardR/100), 0), (int(width*boardR/100), int(height)), (40, 12, 33), 2)
        # Рисуем линию левого борта
        cv2.line(frame, (int(width*boardL/100), 0), (int(width*boardL/100), int(height)), (40, 12, 33), 2)

        # Определение красного
        Red.detect(hsv_image, frame)
        Red.detect()

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
            #print("Центр красного: ", xR, yR)


            # Запись последних 5 координат
            lst = lst[1:] + lst[:1]
            lst.pop(-1)
            lst.append((int(Red.xR), int(Red.yR)))
            print(lst)
            for i in lst:
                cv2.circle(frame, (i[0], i[1]), 5, (0, 255, 0), -1)
            # Построение прямой по 5 координатам
            x_mean = (lst[0][0] + lst[1][0] + lst[2][0] + lst[3][0] + lst[4][0]) / 5
            y_mean = (lst[0][1] + lst[1][1] + lst[2][1] + lst[3][1] + lst[4][1]) / 5
            dx1 = lst[0][0] - x_mean
            dy1 = lst[0][1] - y_mean
            dx2 = lst[1][0] - x_mean
            dy2 = lst[1][1] - y_mean
            dx3 = lst[2][0] - x_mean
            dy3 = lst[2][1] - y_mean
            dx4 = lst[3][0] - x_mean
            dy4 = lst[3][1] - y_mean
            dx5 = lst[4][0] - x_mean
            dy5 = lst[4][1] - y_mean
            sum_dx_dy = dx1 * dy1 + dx2 * dy2 + dx3 * dy3 + dx4 * dy4 + dx5 * dy5
            sum_dx_squared = dx1 * dx1 + dx2 * dx2 + dx3 * dx3 + dx4 * dx4 + dx5 * dx5
            if sum_dx_squared!=0:
                m = sum_dx_dy / sum_dx_squared
            c = y_mean - m * x_mean
            print("y=",m,"х+",c)
            # Рисуем прямую на изображении
            draw_line(frame, m, c, (0, 0, 255))

            # Рисуем линию рикошета
            draw_line(frame, -m+delta, c + 2 * (m * width * boardL / 100), (0, 0, 255))
            draw_line(frame, -m+delta, c + 2 * (m * width * boardR / 100), (0, 0, 255))

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
            #print("Центр зеленого: ", xG, yG)
        cv2.imshow('Video', frame)
        cv2.imshow('Masked Image G', masked_image)


        #________________Начало_кода_отправки_данных_на_плату_Arduino__________________________________
        if Serial_arduino.arduino_port is not None and max_contour is not None and  max_contour2 is not None:


            if yR < height*(100-y_boom)/100:
                Serial_arduino.arduino.write(b'9')                     # Активация ударного механизма после того, как шар по y пересечет черту

            time.sleep(period)
        #________________Конец_кода_отправки_данных_на_плату_Arduino_____________________________________


        # Проверка нажатия клавиши 'q' для выхода из программы
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Освобождение ресурсов
    video_capture.release()
    cv2.destroyAllWindows()