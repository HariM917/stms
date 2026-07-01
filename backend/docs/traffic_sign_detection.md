# Traffic Sign Detection for Smart Traffic Management System

This guide walks through the process of training, testing, and integrating a YOLOv8-based traffic sign detection model for the Smart Traffic Management System (STMS).

## Setup and Requirements

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/stms-backend.git
   cd stms-backend
   ```

2. Install required packages:
   ```
   pip install ultralytics opencv-python numpy
   ```

## Dataset Structure

The Indian traffic signs dataset is organized as follows:
- `traffic_sign_frames/`: Root directory
  - `hump/`: Traffic sign type
    - `hump_20kmph/`: Speed variation
      - `frame_0001.jpg`: Image frames
      - `frame_0002.jpg`: ...
    - `hump_30kmph/`: ...
  - `pedestrian_crossing/`: Traffic sign type
    - `pedestrian_crossing_20kmph/`: Speed variation
    - ...

## Quick Start

The easiest way to train and integrate the traffic sign detection model is to use the wrapper script:

```
python scripts/setup_traffic_sign_detection.py
```

This script will:
1. Install required packages
2. Train a YOLOv8 model on the traffic sign dataset
3. Test the model performance
4. Verify the detector integration

### Advanced Options:

```
python scripts/setup_traffic_sign_detection.py --model-size m --epochs 50 --batch-size 16
```

Available options:
- `--model-size`: YOLOv8 model size (n=nano, s=small, m=medium, l=large, x=xlarge)
- `--epochs`: Number of training epochs
- `--batch-size`: Training batch size
- `--skip-train`: Skip the training phase (use if model already trained)
- `--skip-test`: Skip the testing phase

## Manual Process

If you prefer to run each step manually:

### 1. Train the Model

```
python scripts/train_traffic_sign_model.py --model-size n --epochs 100
```

This will:
- Prepare the dataset (create train/valid/test splits if needed)
- Train a YOLOv8 model on the dataset
- Save the best model to `runs/train/indian_traffic_signs_yolov8n/weights/best.pt`
- Copy the best model to `backend/models/indian_traffic_sign_model.pt`

### 2. Test the Model

```
python scripts/test_traffic_sign_model.py
```

This evaluates the model on the test set and provides performance metrics.

### 3. Test on a Single Image

```
python scripts/test_detector.py --image path/to/your/image.jpg
```

## Integration with STMS

The traffic sign detector is integrated into the STMS backend through the `TrafficSignDetector` class in `backend/detectors/traffic_sign_detector.py`.

Example usage in your code:

```python
from backend.detectors.traffic_sign_detector import TrafficSignDetector

# Initialize the detector
detector = TrafficSignDetector()

# Process a frame
frame = cv2.imread('test_image.jpg')
results = detector.detect(frame)
detections = detector.postprocess(results, frame)

# Print results
for detection in detections:
    print(f"Traffic sign: {detection['class']}, confidence: {detection['confidence']}")
```

## Performance Optimization

For better performance:
- Use a larger model (--model-size m or --model-size l)
- Increase the number of training epochs
- Use data augmentation
- Fine-tune hyperparameters

## Troubleshooting

Common issues:

1. **Model not found error**:
   - Check if the model file exists in one of the expected paths
   - Run training to generate the model file

2. **CUDA out of memory**:
   - Reduce batch size
   - Use a smaller model size

3. **Poor detection accuracy**:
   - Improve dataset quality
   - Increase training epochs
   - Use a larger model size
   - Adjust confidence threshold

For more help, check the [documentation](https://docs.ultralytics.com/) or open an issue on GitHub.