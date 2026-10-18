import cv2
import numpy as np

image = cv2.imread('../data/ex-still-boatdocks.jpg')
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=5)
sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=5)

abs_sobel_x = np.absolute(sobel_x)
abs_sobel_y = np.absolute(sobel_y)

# Sum edges row-wise
row_edges_x = np.sum(abs_sobel_x, axis=1)
row_edges_y = np.sum(abs_sobel_y, axis=1)

# To avoid division by zero
row_edges_x[row_edges_x == 0] = 1

# Ratio of horizontal to vertical edges
ratio_y_x = row_edges_y / row_edges_x

# Smooth the ratio
window_size = max(1, int(image.shape[0] * 0.02))
window = np.ones(window_size) / float(window_size)
smoothed_ratio = np.convolve(ratio_y_x, window, mode='same')

print("Row 50 (Land/Sky):", smoothed_ratio[50])
print("Row 350 (Ocean):", smoothed_ratio[350])
print("Row 650 (Ocean/Beach):", smoothed_ratio[650])

max_ratio = np.max(smoothed_ratio)
mean_ratio = np.mean(smoothed_ratio)
print(f"Max ratio: {max_ratio}, Mean ratio: {mean_ratio}")

# Let's find bounds based on ratio
threshold = mean_ratio * 1.5 # Arbitrary
h = image.shape[0]

top = 0
for y in range(h):
    if smoothed_ratio[y] > threshold:
        top = y
        break
        
bottom = h
for y in range(h-1, -1, -1):
    if smoothed_ratio[y] > threshold:
        bottom = y
        break

print(f"Detected bounds with ratio threshold {threshold}: Top={top}, Bottom={bottom}")
