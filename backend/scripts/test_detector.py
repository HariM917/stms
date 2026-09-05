"""
Test script for the TrafficSignDetector class
"""
import argparse
import sys
from pathlib import Path

import cv2

# Add the parent directory to sys.path to allow importing the backend modules
sys.path.append(str(Path(__file__).resolve().parent.parent))
from backend.detectors.traffic_sign_detector import TrafficSignDetector


def main():
    parser = argparse.ArgumentParser(description="Test the TrafficSignDetector on an image")
    parser.add_argument("--image", type=str, required=True, help="Path to the image to test")
    parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold")
    parser.add_argument("--output", type=str, default="detected_signs.jpg", help="Output image path")
    args = parser.parse_args()

    # Load image
    img_path = Path(args.image)
    if not img_path.exists():
        print(f"Error: Image file {img_path} does not exist.")
        return

    # Read the image
    img = cv2.imread(str(img_path))
    if img is None:
        print(f"Error: Could not read image {img_path}.")
        return

    print(f"Image loaded: {img_path}, shape: {img.shape}")

    # Initialize the detector
    detector = TrafficSignDetector(confidence_threshold=args.conf)

    # Run detection
    print("Running traffic sign detection...")
    results = detector.detect(img)

    if results is None:
        print("Error: Detection failed.")
        return

    # Process detection results
    detections = detector.postprocess(results, img)
    print(f"Found {len(detections)} traffic signs:")

    # Draw bounding boxes on the image
    for detection in detections:
        class_name = detection['class']
        confidence = detection['confidence']
        bbox = detection.get('bbox')

        print(f"  - {class_name}: {confidence:.2f}")

        if bbox:
            x1, y1, x2, y2 = bbox
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(img, f"{class_name} {confidence:.2f}",
                      (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Save the output image
    cv2.imwrite(args.output, img)
    print(f"Output image saved to {args.output}")

if __name__ == "__main__":
    main()
