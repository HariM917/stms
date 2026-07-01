#!/usr/bin/env python3
'''
AI Prediction Web Application for Smart Traffic Management System
'''

import os
import sys
import time
import uuid
import base64
from io import BytesIO

# Add parent directory to path so we can import from the backend modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import required packages, install if missing
def ensure_package(package_name):
    try:
        package_import = package_name.replace('-', '_').split('[')[0]
        __import__(package_import)
    except ImportError:
        print(f"Installing {package_name}...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])

# Ensure all required packages are installed
for package in ['numpy', 'opencv-python', 'pillow', 'flask']:
    ensure_package(package)

# Now import the packages
try:
    import numpy as np
    import cv2
    from PIL import Image
    from flask import Flask, request, render_template, redirect, url_for, flash, jsonify, send_from_directory
except ImportError as e:
    print(f"Error importing required packages even after installation: {e}")
    print("Please run 'python setup_vscode.py' to configure your environment.")
    raise

# Try importing YOLO model
try:
    from ultralytics import YOLO
    YOLO_IMPORTED = True
except ImportError:
    print("Warning: Could not import YOLO. Installing ultralytics...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "ultralytics"])
    try:
        from ultralytics import YOLO
        YOLO_IMPORTED = True
    except ImportError:
        print("Failed to import YOLO even after installation.")
        YOLO_IMPORTED = False

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'ai_traffic_management_secret_key'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize the YOLO model
model = None
if YOLO_IMPORTED:
    try:
        # Check both potential locations for YOLO weights
        yolo_paths = [
            os.path.join(parent_dir, 'yolov8n.pt'),
            os.path.join(parent_dir, 'models', 'yolov8n.pt')
        ]
        
        for path in yolo_paths:
            if os.path.exists(path):
                model = YOLO(path)
                print(f"YOLO model loaded from {path}")
                break
        
        if model is None:
            print("Warning: YOLO model weights not found in expected locations.")
    except Exception as e:
        print(f"Error initializing YOLO model: {e}")

@app.route('/')
def index():
    # Render the main page
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    # Handle file upload for prediction
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file:
        # Save the uploaded file
        filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process the image if model is available
        if model:
            try:
                results = model(filepath)
                
                # Convert result to Base64 for display
                img = cv2.imread(filepath)
                for r in results:
                    img = r.plot()
                
                # Convert to PIL Image and then to base64
                img_pil = Image.fromarray(img)
                buffered = BytesIO()
                img_pil.save(buffered, format="JPEG")
                img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
                
                # Extract detection results
                detections = []
                for r in results:
                    for i, (box, conf, cls) in enumerate(zip(r.boxes.xyxy, r.boxes.conf, r.boxes.cls)):
                        if r.names:
                            label = r.names[int(cls)]
                        else:
                            label = f"Class {int(cls)}"
                        
                        detections.append({
                            'label': label,
                            'confidence': float(conf),
                            'box': {
                                'x1': float(box[0]),
                                'y1': float(box[1]),
                                'x2': float(box[2]),
                                'y2': float(box[3])
                            }
                        })
                
                return render_template('result.html', 
                                     image_b64=img_str, 
                                     detections=detections,
                                     filename=filename)
            except Exception as e:
                flash(f'Error processing image: {str(e)}')
                return redirect(url_for('index'))
        else:
            flash('Model not available. Please check server logs.')
            return redirect(url_for('index'))

@app.route('/users')
def users():
    # Show users page
    return render_template('users.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    # Serve uploaded files
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    print("=== STMS Web Application ===")
    print("Starting server at http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
