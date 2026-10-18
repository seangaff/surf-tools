import cv2
import numpy as np
import sys

def test_valley(image_path):
    image = cv2.imread(image_path)
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

    # Find Top Bound (expand upwards)
    top_bound = max_row
    current_min = smoothed_edges[max_row]
    
    for y in range(max_row, -1, -1):
        val = smoothed_edges[y]
        if val < top_threshold:
            top_bound = y
            break
        
        if val < current_min:
            current_min = val
            top_bound = y  # Keep updating the best valley so far
        elif val > current_min * 1.5:
            # Rebounded by 50% from the valley minimum -> Hit a new textured object (e.g., peninsula)
            break

    # Find Bottom Bound (expand downwards)
    bottom_bound = max_row
    current_min = smoothed_edges[max_row]
    
    for y in range(max_row, image.shape[0]):
        val = smoothed_edges[y]
        if val < bottom_threshold:
            bottom_bound = y
            break
            
        if val < current_min:
            current_min = val
            bottom_bound = y
        elif val > current_min * 1.5:
            # Rebounded (hit beach rocks/texture)
            break

    print(f"{image_path} -> Max Row: {max_row}, Top Bound: {top_bound}, Bottom Bound: {bottom_bound}")

test_valley('../data/ex-still.jpg')
test_valley('../data/ex-still-boatdocks.jpg')
