import cv2
import numpy as np

image = cv2.imread('../data/ex-still-boatdocks.jpg')
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=5)
abs_sobel_y = np.absolute(sobel_y)
row_edges = np.sum(abs_sobel_y, axis=1)

window_size = max(1, int(image.shape[0] * 0.02))
window = np.ones(window_size) / float(window_size)
smoothed_edges = np.convolve(row_edges, window, mode='same')

max_edge = np.max(smoothed_edges)
max_row = np.argmax(smoothed_edges)

top_threshold = max_edge * 0.1
bottom_threshold = max_edge * 0.3

# Expand upwards from max_row
top_bound = max_row
for y in range(max_row, -1, -1):
    # Stop if we drop below threshold
    if smoothed_edges[y] < top_threshold:
        top_bound = y
        break
    # Optional: Stop if we start increasing significantly (hit a peninsula after a smooth ocean valley)
    # Actually, let's just see where the threshold triggers first.

# Expand downwards from max_row
bottom_bound = max_row
for y in range(max_row, image.shape[0]):
    if smoothed_edges[y] < bottom_threshold:
        bottom_bound = y
        break

print(f"Max Row (Waves): {max_row}")
print(f"Detected bounds: Top={top_bound}, Bottom={bottom_bound}")
