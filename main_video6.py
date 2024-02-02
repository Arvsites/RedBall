# Библиотеки для установки: opencv-python, numpy, pyserial
import cv2
import numpy as np
import time
import socket
from threading import Thread


#________________________Начало_настройки_параметров_____________________________
UDP_IP = "192.168.4.1"  # IP-адрес NodeMCU
UDP_PORT = 1234  # Порт, на котором NodeMCU будет слушать
serial_speed = 9600               # Скорость передачи данных по Serial
cam = 0                             # 0 использование встроенной камеры, 1 web камеры
HSV_red_lower_1 = [0, 50, 50]       # Нижняя граница HSV для красного цвета 1
HSV_red_upper_1 = [10, 255, 255]    # Верхняя граница HSV для красного цвета 1
HSV_red_lower_2 = [170, 80, 50]     # Нижняя граница HSV для красного цвета 2
HSV_red_upper_2 = [180, 255, 255]   # Верхняя граница HSV для красного цвета 2
HSV_green_lower_1 = [35, 50, 50]    # Нижняя граница HSV для зеленого цвета
HSV_green_upper_1 = [60, 255, 255]  # Верхняя граница HSV для зеленого цвета
y_boom = 35                         # % от экрана, где будет проходит граница срабатывания удара
boardR = 89                         # % от экрана правый борт
boardL = 5                          # % от экрана левый борт
delta = 0                           # Коэфициент коррректировки траектории отражения
n = 4                              # Количество отрезков зоны робота, выход за которые дает команду по Serial порту
#________________________Конец_настройки_параметров______________________________


# Класс для определения цвета и вывода маски на экран
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
        self.max_contour = None
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > max_area:
                max_area = area
                self.max_contour = contour
        if self.max_contour is not None:
            (x, y, w, h) = cv2.boundingRect(self.max_contour)
            cv2.rectangle(self.frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            self.x_color = x + w / 2
            self.y_color = y + h / 2
            # print("Центр красного: ", self.xR, self.yR)
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
    if y1 > height*(100 - y_boom)/100 and slope != 0:
        y1 = int(height*(100 - y_boom)/100)
        x1 = int((height*(100 - y_boom)/100 - intercept)/slope)
    if y2 > height*(100 - y_boom)/100 and slope != 0:
        y2 = int(height*(100 - y_boom)/100)
        x2 = int((height*(100 - y_boom)/100 - intercept)/slope)
    # Рисуем линию на кадре
    cv2.line(frame, (int(x1), y1), (int(x2), y2), color, 2)

# Код передачи инфомации по UDP протоколу. Тут вся логика передачи информации на Arduino.
def robot(x_boom, x_color, array_zone):
    global flag
    n_boom = 0
    n_color = 0
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
    if n_color-n_boom >= 1:
        data = "1"
        sock.sendto(data.encode(), (UDP_IP, UDP_PORT))
    elif n_color-n_boom <= -1:
        data = "2"
        sock.sendto(data.encode(), (UDP_IP, UDP_PORT))
    else:
        data = "0"
        sock.sendto(data.encode(), (UDP_IP, UDP_PORT))

    if height*(100-y_boom)/100 <= Red.y_color:
        if flag == 1:
            flag = 0
            data = "3"
            sock.sendto(data.encode(), (UDP_IP, UDP_PORT))
            # Создаём новый поток
            th = Thread(target=remind, args=())
            # И запускаем его
            th.start()


# функция для удара робота, чтоб не ударял много раз подряд
def remind():
    time.sleep(1)
    global flag
    flag = 1

# Точка входа кода
if __name__ == "__main__":
    flag = 1 #флаг для отчета удара времени робота
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #запуск UDP протокола

    video_capture = cv2.VideoCapture(cam)
    if not video_capture.isOpened():
        print("Не удалось открыть видеопоток")
        exit()

    x0, y0 = 1, 1
    x_boom = boardL
    lst = [(0, 0), (0, 0), (0, 0), (0, 0), (0, 0)]
    width = video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = video_capture.get(cv2.CAP_PROP_FPS)
    # Выводим параметры
    print(f"Ширина кадра: {width}")
    print(f"Высота кадра: {height}")
    print(f"Частота кадров: {fps}")

    # Создание объектов для определения цветов
    Red = Detect_color("Red", HSV_red_lower_1, HSV_red_upper_1, HSV_red_lower_2, HSV_red_upper_2)
    Green = Detect_color("Green", HSV_green_lower_1, HSV_green_upper_1, (0,0,0), (0,0,0))

    # Разбитие на отрезки поля, выход за которые дает команду по Serial порту
    delta_zone = (width * boardR / 100 - width * boardL / 100) /n
    array_zone = [width * boardL / 100]
    mas_delta_zone = width * boardL / 100
    for i in range(n):
        mas_delta_zone += delta_zone
        array_zone.append(mas_delta_zone)

    while True:
        ret, frame = video_capture.read()
        if not ret:
            print("Не удалось захватить кадр")
            break
        hsv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Определение красного и зеленого
        Red.detect(hsv_image, frame)
        Green.detect(hsv_image, frame)

        # Запись последних 5 координат красного цвета
        if Red.max_contour is not None:
            lst = lst[1:] + lst[:1]
            lst.pop(-1)
            lst.append((int(Red.x_color), int(Red.y_color)))
            print(lst)
            for i in lst:
                cv2.circle(frame, (i[0], i[1]), 5, (0, 255, 0), -1)
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
            if sum_dx_squared != 0:
                m = sum_dx_dy / sum_dx_squared
            c = y_mean - m * x_mean
            print("Формула прямой траектории y=",m,"х+",c)
            print("Формула прямой рекошета y=", -m+delta, "х+", c + 2 * (m * width * boardL / 100))
            draw_line(frame, m, c, (0, 0, 255))

            # Расчет точки попадания
            if -m +delta != 0:
                if width * boardR / 100 > (height * (100 - y_boom) / 100 - (c + 2 * (m * width * boardL / 100))) / (-m + delta) > width * boardL / 100:
                    x_boom = (height * (100 - y_boom) / 100 - (c + 2 * (m * width * boardL / 100))) / (-m + delta)
                elif width * boardR / 100 > (height * (100 - y_boom) / 100 - (c + 2 * (m * width * boardR / 100))) / (-m + delta) > width * boardL / 100:
                    x_boom = (height * (100 - y_boom) / 100 - (c + 2 * (m * width * boardR / 100))) / (-m + delta)
                elif width * boardR / 100 > (height * (100 - y_boom) / 100 - c) / m > width * boardL / 100:
                    x_boom = (height * (100 - y_boom) / 100 - c) / m
                else:
                    x_boom = width*boardL/100 + (width*boardR/100 - width*boardL/100) / 2
            cv2.circle(frame, (int(x_boom), int(height*(100-y_boom)/100)), 5, (200, 255, 0), 9)

            # Рисуем линию рикошета
            draw_line(frame, -m+delta, c + 2 * (m * width * boardL / 100), (0, 0, 255))
            draw_line(frame, -m+delta, c + 2 * (m * width * boardR / 100), (0, 0, 255))
            # Рисуем линию сработки удара
            draw_line(frame, 0, height * ((100 - y_boom) / 100), (40, 12, 33))
            # Рисуем линию правого борта
            cv2.line(frame, (int(width * boardR / 100), 0), (int(width * boardR / 100), int(height)), (40, 12, 33), 2)
            # Рисуем линию левого борта
            cv2.line(frame, (int(width * boardL / 100), 0), (int(width * boardL / 100), int(height)), (40, 12, 33), 2)
            # Рисуем зоны реагирования
            for i in array_zone:
                cv2.circle(frame, (int(i), int(height * (100 - y_boom) / 100)), 1, (200, 100, 100), 5)
            cv2.imshow('Video', frame)

        # Передача информации на робота
        if Red.max_contour is not None and  Green.max_contour is not None:
            robot(x_boom, Green.x_color, array_zone)

        # Проверка нажатия клавиши 'q' для выхода из программы
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Освобождение ресурсов
    video_capture.release()
    cv2.destroyAllWindows()