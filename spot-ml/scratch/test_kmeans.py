import cv2
import numpy as np
import os

def test_kmeans(img_path):
    img = cv2.imread(img_path)
    if img is None:
        print(f"Error loading {img_path}")
        return
        
    # Resize for faster processing
    scale = 0.5
    small_img = cv2.resize(img, (0,0), fx=scale, fy=scale)
    h, w = small_img.shape[:2]
    
    # Convert to HSV or LAB
    lab = cv2.cvtColor(small_img, cv2.COLOR_BGR2LAB)
    
    # Flatten
    Z = lab.reshape((-1,3))
    Z = np.float32(Z)
    
    # Define criteria, number of clusters(K) and apply kmeans()
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    K = 3
    ret, label, center = cv2.kmeans(Z, K, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    
    # Convert back into uint8, and make original image
    center = np.uint8(center)
    res = center[label.flatten()]
    res2 = res.reshape((small_img.shape))
    
    # Convert back to BGR for saving
    res2_bgr = cv2.cvtColor(res2, cv2.COLOR_LAB2BGR)
    cv2.imwrite('scratch/kmeans_out.jpg', res2_bgr)
    print("Kmeans saved.")

test_kmeans('../data/ex-still.jpg')
