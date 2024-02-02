import cv2
import numpy as np

# Загрузка изображения
image = cv2.imread('images.jpg')

# Преобразование изображения из BGR в HSV цветовое пространство
hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

# Определение диапазона красного цвета в HSV
lower_red = np.array([0, 50, 50])
upper_red = np.array([10, 255, 255])
mask1 = cv2.inRange(hsv_image, lower_red, upper_red)

lower_red = np.array([170, 50, 50])
upper_red = np.array([180, 255, 255])
mask2 = cv2.inRange(hsv_image, lower_red, upper_red)

# Объединение двух масок для получения окончательной маски
final_mask = mask1 + mask2

# Применение маски к изображению
masked_image = cv2.bitwise_and(image, image, mask=final_mask)

# Поиск контуров на маске
contours, _ = cv2.findContours(final_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Отрисовка прямоугольных контуров вокруг найденных объектов
for contour in contours:
    x, y, w, h = cv2.boundingRect(contour)
    cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

# Отображение исходного изображения и результата
cv2.imshow('Original Image', image)
# cv2.imshow('Masked Image', masked_image)
cv2.waitKey(0)
cv2.destroyAllWindows()


