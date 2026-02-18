# Goal is to count people and return both image and count

from ultralytics import YOLO

# Load a pretrained YOLO26n model
model = YOLO("yolo26n.pt")

# Perform object detection on an image
results = model("../data/ex-still.jpg")  # Predict on an image
# results[0].show()  # Display results
print(results[0].boxes)