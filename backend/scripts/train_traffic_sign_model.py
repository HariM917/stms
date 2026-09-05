"""
Train YOLOv8 model on Indian Traffic Signs Dataset
"""

import argparse
import os
import random
import shutil
from pathlib import Path

from ultralytics import YOLO


def prepare_dataset(dataset_path, split_ratio=None):
    """
    Prepare the dataset by:
    1. Creating train/valid/test splits if they don't exist
    2. Generating YOLO format labels if needed

    Args:
        dataset_path: Path to the dataset root
        split_ratio: Train/Valid/Test split ratios

    Returns:
        dict with paths to train, valid, test directories
    """
    if split_ratio is None:
        split_ratio = [0.7, 0.2, 0.1]
    dataset_path = Path(dataset_path)

    # Check if dataset already has train/valid/test splits
    train_dir = dataset_path / 'train'
    valid_dir = dataset_path / 'valid'
    test_dir = dataset_path / 'test'

    if train_dir.exists() and valid_dir.exists() and test_dir.exists():
        print("Found existing dataset splits.")
        return {
            'train': train_dir,
            'valid': valid_dir,
            'test': test_dir
        }

    # If we don't have proper splits, we'll create them
    print("Dataset splits not found. Creating train/valid/test splits...")

    # Create directories
    for dir_name in ['train/images', 'train/labels', 'valid/images', 'valid/labels', 'test/images', 'test/labels']:
        os.makedirs(dataset_path / dir_name, exist_ok=True)

    # Get all subdirectories containing images
    traffic_sign_dirs = []

    # First level: sign type (hump, pedestrian_crossing, etc.)
    for sign_type in dataset_path.iterdir():
        if sign_type.is_dir():
            # Second level: speed variations (20kmph, 30kmph, etc.)
            for speed_dir in sign_type.iterdir():
                if speed_dir.is_dir():
                    traffic_sign_dirs.append(speed_dir)

    # Assign images to train/valid/test splits
    for sign_dir in traffic_sign_dirs:
        sign_type = sign_dir.parent.name
        speed = sign_dir.name
        class_id = None

        # Determine class ID based on sign type
        if 'hump' in sign_type:
            class_id = 0
        elif 'pedestrian_crossing' in sign_type:
            class_id = 1
        elif 'stop' in sign_type:
            class_id = 2
        elif '20kmph' in speed:
            class_id = 3
        elif '30kmph' in speed:
            class_id = 4
        elif '40kmph' in speed:
            class_id = 5
        elif '50kmph' in speed:
            class_id = 6
        elif 'no_entry' in sign_type:
            class_id = 7
        elif 'no_parking' in sign_type:
            class_id = 8
        else:
            # Default to hump if unknown
            class_id = 0

        # Get all images in this directory
        images = [f for f in sign_dir.iterdir() if f.suffix.lower() in ['.jpg', '.jpeg', '.png']]

        # Shuffle to ensure random distribution
        random.shuffle(images)

        # Calculate split sizes
        train_size = int(len(images) * split_ratio[0])
        valid_size = int(len(images) * split_ratio[1])

        # Split images
        train_images = images[:train_size]
        valid_images = images[train_size:train_size+valid_size]
        test_images = images[train_size+valid_size:]

        # Process each split
        for img_list, target_dir in [(train_images, 'train'), (valid_images, 'valid'), (test_images, 'test')]:
            for img_path in img_list:
                try:
                    # Copy image to target directory
                    dest_img_path = dataset_path / target_dir / 'images' / img_path.name
                    # Only copy if source and destination are not the same
                    if str(img_path) != str(dest_img_path):
                        shutil.copy(img_path, dest_img_path)

                    # Create a simple label in YOLO format
                    # Format: class_id center_x center_y width height (normalized 0-1)
                    label_content = f"{class_id} 0.5 0.5 0.8 0.8"

                    # Save label file with same name but .txt extension
                    label_path = dataset_path / target_dir / 'labels' / (img_path.stem + '.txt')
                    with open(label_path, 'w') as f:
                        f.write(label_content)
                except Exception as e:
                    print(f"Error processing {img_path}: {e}")

    print(f"Dataset prepared with {len(train_images)} training, {len(valid_images)} validation, and {len(test_images)} test images")

    return {
        'train': train_dir,
        'valid': valid_dir,
        'test': test_dir
    }

def parse_args():
    parser = argparse.ArgumentParser(description='Train YOLOv8 on Indian Traffic Signs Dataset')
    parser.add_argument('--model-size', type=str, default='n', choices=['n', 's', 'm', 'l', 'x'],
                        help='YOLOv8 model size (n=nano, s=small, m=medium, l=large, x=xlarge)')
    parser.add_argument('--epochs', type=int, default=100, help='Number of training epochs')
    parser.add_argument('--batch-size', type=int, default=16, help='Batch size')
    parser.add_argument('--img-size', type=int, default=640, help='Image size')
    parser.add_argument('--workers', type=int, default=4, help='Number of worker threads')
    parser.add_argument('--device', type=str, default='', help='Training device (empty for auto)')
    parser.add_argument('--resume', action='store_true', help='Resume training from last checkpoint')
    parser.add_argument('--output-dir', type=str, default='runs/train',
                        help='Directory to save training results')
    parser.add_argument('--dataset', type=str, default=None,
                        help='Dataset path (default: project_dir/traffic_sign_frames)')
    return parser.parse_args()

def main():
    args = parse_args()

    # Set paths
    script_dir = Path(__file__).resolve().parent
    project_dir = script_dir.parent  # Main project directory

    # Set dataset path
    dataset_path = Path(args.dataset) if args.dataset else project_dir / 'traffic_sign_frames'

    yaml_path = project_dir / 'backend' / 'models' / 'indian_traffic_signs.yaml'

    print(f"Training YOLOv8{args.model_size} on Indian Traffic Signs Dataset")
    print(f"Dataset path: {dataset_path}")
    print(f"Using configuration file: {yaml_path}")

    # Prepare dataset (create splits if needed)
    prepare_dataset(dataset_path)

    # Create model
    model_name = f"yolov8{args.model_size}.pt"
    model = YOLO(model_name)

    # Train the model
    results = model.train(
        data=str(yaml_path),
        epochs=args.epochs,
        batch=args.batch_size,
        imgsz=args.img_size,
        workers=args.workers,
        device=args.device,
        resume=args.resume,
        project=args.output_dir,
        name=f'indian_traffic_signs_yolov8{args.model_size}'
    )

    print("Training completed.")
    print(f"Results saved to: {results.save_dir}")

    # Evaluate the model on validation set
    print("\nEvaluating on validation set:")
    model.val()

    # Export the model to different formats
    print("\nExporting models:")
    model.export(format='onnx')  # Export to ONNX format

    # Save the best model to the models directory
    best_model_path = Path(results.best)
    if best_model_path.exists():
        output_model_path = project_dir / 'backend' / 'models' / 'indian_traffic_sign_model.pt'
        import shutil
        shutil.copy(best_model_path, output_model_path)
        print(f"Best model saved to: {output_model_path}")

if __name__ == "__main__":
    main()
