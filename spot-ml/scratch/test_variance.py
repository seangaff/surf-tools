import cv2
import numpy as np
import matplotlib.pyplot as plt
import os

def detect_lines(img_path):
    img = cv2.imread(img_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Calculate row-wise variance
    variances = np.var(gray, axis=1)
    
    # Calculate row-wise edges (Sobel Y to detect horizontal lines)
    sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=5)
    abs_sobel_y = np.absolute(sobel_y)
    row_edges = np.sum(abs_sobel_y, axis=1)
    
    plt.figure(figsize=(12, 6))
    
    plt.subplot(1, 3, 1)
    plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    plt.title("Original")
    
    plt.subplot(1, 3, 2)
    plt.plot(variances, range(len(variances)))
    plt.gca().invert_yaxis()
    plt.title("Row Variance")
    
    plt.subplot(1, 3, 3)
    plt.plot(row_edges, range(len(row_edges)))
    plt.gca().invert_yaxis()
    plt.title("Row Edge Sum")
    
    plt.savefig('scratch/variance_plot.png')

detect_lines('../data/ex-still.jpg')
