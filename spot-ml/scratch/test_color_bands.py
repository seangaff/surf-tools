import cv2
import numpy as np

def test_color_bands(image_path):
    img = cv2.imread(image_path)
    # Calculate row-wise median colors
    row_colors = np.median(img, axis=1) # shape: (h, 3)
    
    # Convert row colors to LAB for better perceptual clustering
    row_colors_lab = cv2.cvtColor(row_colors.reshape(-1, 1, 3).astype(np.uint8), cv2.COLOR_BGR2LAB).reshape(-1, 3)
    
    # We want to cluster the rows into 3 or 4 bands
    Z = np.float32(row_colors_lab)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    K = 3
    ret, label, center = cv2.kmeans(Z, K, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    
    label = label.flatten()
    
    # Let's see the contiguous blocks of labels
    blocks = []
    current_label = label[0]
    start_y = 0
    for y in range(1, len(label)):
        if label[y] != current_label:
            blocks.append((current_label, start_y, y))
            current_label = label[y]
            start_y = y
    blocks.append((current_label, start_y, len(label)))
    
    print(f"\nImage: {image_path}")
    for b in blocks:
        print(f"Cluster {b[0]}: Rows {b[1]} to {b[2]} (Height: {b[2]-b[1]})")

test_color_bands('../data/ex-still.jpg')
test_color_bands('../data/ex-still-boatdocks.jpg')
