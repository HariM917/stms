"""
Test and evaluate a trained YOLOv8 model on Indian Traffic Signs Dataset
"""

import argparse
import os
from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
from ultralytics import YOLO


def parse_args():
    parser = argparse.ArgumentParser(description='Test YOLOv8 on Indian Traffic Signs Dataset')
    parser.add_argument('--model', type=str, default='backend/models/indian_traffic_sign_model.pt',
                        help='Path to trained model')
    parser.add_argument('--data', type=str,
                        default='backend/models/indian_traffic_signs.yaml',
                        help='Path to dataset yaml')
    parser.add_argument('--img-size', type=int, default=640, help='Image size')
    parser.add_argument('--conf-thres', type=float, default=0.25, help='Confidence threshold')
    parser.add_argument('--iou-thres', type=float, default=0.45, help='NMS IoU threshold')
    parser.add_argument('--max-det', type=int, default=300, help='Maximum detections per image')
    parser.add_argument('--device', type=str, default='', help='Device to run on (empty for auto)')
    parser.add_argument('--output-dir', type=str, default='runs/test',
                        help='Directory to save test results')
    parser.add_argument('--test-images', type=str, default=None,
                        help='Path to directory containing test images (optional)')
    parser.add_argument('--save-images', action='store_true', help='Save annotated images')
    return parser.parse_args()

def plot_confusion_matrix(cm, class_names, output_path):
    """Plot confusion matrix as a heatmap."""
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=class_names, yticklabels=class_names)
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.title('Confusion Matrix')
    plt.savefig(output_path)
    plt.close()

def main():
    args = parse_args()

    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)

    print(f"Testing model: {args.model}")

    # Load model
    model = YOLO(args.model)

    # Run validation on test set
    results = model.val(
        data=args.data,
        imgsz=args.img_size,
        conf=args.conf_thres,
        iou=args.iou_thres,
        max_det=args.max_det,
        device=args.device,
        project=args.output_dir,
        name='val_results',
        plots=True
    )

    print("\nValidation Results:")
    print(f"mAP50: {results.box.map50:.4f}")
    print(f"mAP50-95: {results.box.map:.4f}")

    # Test on custom images if provided
    if args.test_images:
        test_dir = Path(args.test_images)
        if test_dir.exists() and test_dir.is_dir():
            output_images_dir = Path(args.output_dir) / 'test_images'
            os.makedirs(output_images_dir, exist_ok=True)

            print(f"\nRunning inference on images in {test_dir}")
            image_exts = ['.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff']

            image_paths = [p for p in test_dir.glob('*') if p.suffix.lower() in image_exts]

            for img_path in tqdm(image_paths, desc="Processing images"):
                # Perform inference
                pred = model.predict(
                    source=str(img_path),
                    conf=args.conf_thres,
                    iou=args.iou_thres,
                    max_det=args.max_det,
                    save=args.save_images,
                    save_dir=output_images_dir
                )

                if not args.save_images:
                    # Load and process the image manually if not saving
                    img = cv2.imread(str(img_path))

                    # Process detections
                    for det in pred[0].boxes.data:
                        x1, y1, x2, y2, conf, cls = det
                        cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                        cv2.putText(img, f"{model.names[int(cls)]} {conf:.2f}",
                                    (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX,
                                    0.5, (0, 255, 0), 2)

                    # Save the image
                    output_path = output_images_dir / f"{img_path.stem}_pred{img_path.suffix}"
                    cv2.imwrite(str(output_path), img)

            print(f"Processed {len(image_paths)} images. Results saved to {output_images_dir}")

    print("\nTesting completed.")

if __name__ == "__main__":
    main()
