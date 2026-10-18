import cv2
import numpy as np

img = cv2.imread('../data/ex-still.jpg')
if img is None:
    img = cv2.imread('data/ex-still.jpg')

# Try edge detection and hough lines
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
edges = cv2.Canny(gray, 50, 150, apertureSize=3)
lines = cv2.HoughLines(edges, 1, np.pi/180, 200)

out = img.copy()
if lines is not None:
    for rho, theta in lines[0:5]:
        a = np.cos(theta)
        b = np.sin(theta)
        x0 = a*rho
        y0 = b*rho
        x1 = int(x0 + 1500*(-b))
        y1 = int(y0 + 1500*(a))
        x2 = int(x0 - 1500*(-b))
        y2 = int(y0 - 1500*(a))
        cv2.line(out, (x1, y1), (x2, y2), (0, 0, 255), 2)

cv2.imwrite('scratch/hough.jpg', out)
