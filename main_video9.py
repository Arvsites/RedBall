# Библиотеки для установки: pip install opencv-python
import cv2
import numpy as np
import time
import socket
from threading import Thread


#________________________Начало_настройки_параметров_____________________________
UDP_IP = "192.168.4.1"  # IP-адрес NodeMCU
UDP_PORT = 1234  # Порт, на котором NodeMCU будет слушать
cam = 0                             # 1 использование встроенной камеры, 0 web камеры
#это менять определение цвета
HSV_red_lower_1 = [0, 50, 50]       # Нижняя граница HSV для красного цвета 1
HSV_red_upper_1 = [10, 255, 255]    # Верхняя граница HSV для красного цвета 1
HSV_red_lower_2 = [170, 80, 50]     # Нижняя граница HSV для красного цвета 2
HSV_red_upper_2 = [180, 255, 255]   # Верхняя граница HSV для красного цвета 2
HSV_green_lower_1 = [35, 50, 50]    # Нижняя граница HSV для зеленого цвета
HSV_green_upper_1 = [60, 255, 255]  # Верхняя граница HSV для зеленого цвета
#это для определения границ удара и границ левой и правой грани
y_boom = 35                         # % от экрана, где будет проходит граница срабатывания удара
boardR = 89                         # % от экрана правый борт
boardL = 5                          # % от экрана левый борт
delta = 0                           # Коэфициент коррректировки траектории отражения
#это точность (количество отрезкор реагирования)
n = 4                              # Количество отрезков зоны робота, выход за которые дает команду роботу
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




# Код передачи инфомации по UDP протоколу. Тут вся логика передачи информации на Arduino.
def robot(x_boom, x_color, array_zone):
    global flag
    global n
    n_boom = 0
    n_color = 0
    print(n_color, n_boom)
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
    #если не работает, то выкинуть из условия " and n_color < n"
    if n_color-n_boom >= 1 and n_color < n:
        data = "2"
        sock.sendto(data.encode(), (UDP_IP, UDP_PORT))
        print('вправо')
    #если не работает, то выкинуть из условия " and n_color > 0"
    elif n_color-n_boom <= -1 and n_color > 0:
        data = "1"
        sock.sendto(data.encode(), (UDP_IP, UDP_PORT))
        print('влево')
    else:
        data = "0"
        print('стоп')
        sock.sendto(data.encode(), (UDP_IP, UDP_PORT))

    if height*(100-y_boom)/100 <= Red.y_color:
        if flag == 1:
            print("стрелять")
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


        if Red.max_contour is not None:

            #робот будет двигаться без учета траектории мяча, просто там, где мяч по Х, туда и будет стремиться по Х робот
            x_boom = Red.x_color

            cv2.circle(frame, (int(x_boom), int(height*(100-y_boom)/100)), 5, (200, 255, 0), 9)

            # Рисуем зоны реагирования удара
            for i in array_zone:
                cv2.circle(frame, (int(i), int(height * (100 - y_boom) / 100)), 1, (200, 100, 100), 5)
            cv2.imshow('Video', frame)

            # Передача информации на робота
            if Green.max_contour is not None:
                robot(x_boom, Green.x_color, array_zone)
            else:
                robot(x_boom, x_boom, array_zone)



        # Проверка нажатия клавиши 'q' для выхода из программы
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Освобождение ресурсов
    video_capture.release()
    cv2.destroyAllWindows()