'''
Preprocess steps to try:
1. Remove top and bottom of image (sky and beach)
2. Reduce glare and increase contrast
3. Split into smaller sub images, adjust for distance from cam

'''

import cv2
import numpy as np
import matplotlib.pyplot as plt
import os

def find_water_boundaries(image, k_clusters=4):
    """
    Dynamically finds the horizon (top) and shoreline (bottom) using Color Segmentation.
    1. Uses K-Means to cluster the row-wise median colors into bands (Sky, Water, Land, Beach).
    2. Uses horizontal edge density to find the wave peak (guaranteed to be in the water).
    3. Anchors the 'Water' cluster at the wave peak and expands outwards until the color changes.
    """
    h, w = image.shape[:2]
    
    # --- 1. Find the Wave Peak (Texture) ---
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=5)
    row_edges = np.sum(np.absolute(sobel_y), axis=1)
    
    window_size = max(1, int(h * 0.02))
    window = np.ones(window_size) / float(window_size)
    smoothed_edges = np.convolve(row_edges, window, mode='same')
    max_row = np.argmax(smoothed_edges)
    
    # --- 2. Color Clustering ---
    # Calculate median color of each row to ignore local noise (like a single surfer/boat)
    row_colors = np.median(image, axis=1).astype(np.uint8) # Shape: (h, 3)
    
    # Convert to LAB space for perceptual color clustering
    row_colors_lab = cv2.cvtColor(row_colors.reshape(-1, 1, 3), cv2.COLOR_BGR2LAB).reshape(-1, 3)
    
    Z = np.float32(row_colors_lab)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, _ = cv2.kmeans(Z, k_clusters, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    labels = labels.flatten()
    
    # Smooth the labels to prevent 1-pixel anomalies from stopping the expansion
    # We use a moving mode (majority vote) filter. 
    # Since numpy doesn't have a built-in mode filter, we use a simple sliding window heuristic.
    smooth_window = max(3, int(h * 0.01))
    smoothed_labels = np.copy(labels)
    for i in range(h):
        start = max(0, i - smooth_window//2)
        end = min(h, i + smooth_window//2 + 1)
        vals, counts = np.unique(labels[start:end], return_counts=True)
        smoothed_labels[i] = vals[np.argmax(counts)]
        
    # --- 3. Expand from the Anchor ---
    # The water cluster is the dominant cluster around the wave peak
    water_cluster = smoothed_labels[max_row]
    
    top_bound = max_row
    for y in range(max_row, -1, -1):
        if smoothed_labels[y] != water_cluster:
            top_bound = y
            break
            
    bottom_bound = max_row
    for y in range(max_row, h):
        if smoothed_labels[y] != water_cluster:
            bottom_bound = y
            break
            
    # Add a tiny safety margin to ensure we don't crop the surfers at the very edge
    margin = int(h * 0.02)
    top_bound = max(0, top_bound - margin)
    bottom_bound = min(h, bottom_bound + margin)
    
    return top_bound, bottom_bound

def dynamic_crop(image, top_bound, bottom_bound):
    """
    1. Remove top and bottom of image (sky and beach) using dynamically found bounds.
    """
    return image[top_bound:bottom_bound, :]

def enhance_contrast_glare(image):
    """
    2. Reduce glare and increase contrast
    Uses CLAHE (Contrast Limited Adaptive Histogram Equalization) on the L channel of the LAB color space.
    """
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    # Apply CLAHE to L channel
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    
    # Merge channels and convert back to BGR
    limg = cv2.merge((cl, a, b))
    final = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
    return final

def split_image(image, num_horizontal_splits=2, num_vertical_splits=3):
    """
    3. Split into smaller sub images, adjust for distance from cam
    For adjusting for distance from cam, one could use different sized horizontal bands.
    Here we implement a standard grid split, but it can be adapted to scale sub-images
    based on their vertical position.
    """
    h, w = image.shape[:2]
    # Simple grid split
    sub_h = h // num_horizontal_splits
    sub_w = w // num_vertical_splits
    
    sub_images = []
    for r in range(num_horizontal_splits):
        for c in range(num_vertical_splits):
            sub_img = image[r*sub_h:(r+1)*sub_h, c*sub_w:(c+1)*sub_w]
            sub_images.append(sub_img)
            
    return sub_images

def main():
    # Construct path to data/ex-still.jpg
    base_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(base_dir, '../data/ex-still-boatdocks.jpg')
    
    if not os.path.exists(image_path):
        # Fallback to current dir's data/
        image_path = 'data/ex-still-boatdocks.jpg'
        
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Could not load image from {image_path}")
        return
        
    print(f"Original image shape: {img.shape}")
    
    # Step 1: Detect water boundaries dynamically
    top_bound, bottom_bound = find_water_boundaries(img)
    print(f"Detected top bound: {top_bound}, bottom bound: {bottom_bound}")
    
    # Crop image
    cropped = dynamic_crop(img, top_bound, bottom_bound)
    print(f"Cropped image shape: {cropped.shape}")
    
    # Step 2: Enhance contrast and reduce glare
    enhanced = enhance_contrast_glare(cropped)
    
    # Step 3: Split into sub-images
    sub_images = split_image(enhanced, num_horizontal_splits=2, num_vertical_splits=3)
    print(f"Generated {len(sub_images)} sub-images")
    print(f"Sub-image shape: {sub_images[0].shape}")
    
    # Prepare visualization
    # Draw the detected crop lines on the original image for visual verification
    img_with_lines = img.copy()
    cv2.line(img_with_lines, (0, top_bound), (img_with_lines.shape[1], top_bound), (0, 0, 255), 3)
    cv2.line(img_with_lines, (0, bottom_bound), (img_with_lines.shape[1], bottom_bound), (0, 255, 0), 3)
    
    display_img = sub_images[0]
    
    # Convert from BGR to RGB for Matplotlib
    img_with_lines_rgb = cv2.cvtColor(img_with_lines, cv2.COLOR_BGR2RGB)
    display_img_rgb = cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB)
    
    plt.figure(figsize=(15, 6))
    
    plt.subplot(1, 2, 1)
    plt.imshow(img_with_lines_rgb)
    plt.title("Original with Dynamic Crop Lines")
    plt.axis('off')
    
    plt.subplot(1, 2, 2)
    plt.imshow(display_img_rgb)
    plt.title("Preprocessed Sub-image (Top-Left)")
    plt.axis('off')
    
    plt.show()

if __name__ == "__main__":
    main()
