"""
Wrapper script to train and integrate the Indian Traffic Sign Detection model
"""
import argparse
import subprocess
from pathlib import Path


def run_command(command, description):
    """Run a command and print its output"""
    print(f"\n{description}...")
    print(f"Running: {command}")
    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        universal_newlines=True
    )

    # Print output in real-time
    for line in process.stdout:
        line = line.strip()
        if line:
            print(line)

    process.wait()
    return process.returncode

def main():
    parser = argparse.ArgumentParser(description="Train and integrate Indian Traffic Sign Detection model")
    parser.add_argument("--model-size", type=str, default="n", choices=["n", "s", "m", "l", "x"],
                      help="YOLOv8 model size (n=nano, s=small, m=medium, l=large, x=xlarge)")
    parser.add_argument("--epochs", type=int, default=20,
                      help="Number of training epochs (default: 20)")
    parser.add_argument("--batch-size", type=int, default=8,
                      help="Training batch size (default: 8)")
    parser.add_argument("--skip-train", action="store_true",
                      help="Skip the training phase (use if model already trained)")
    parser.add_argument("--skip-test", action="store_true",
                      help="Skip the testing phase")
    args = parser.parse_args()

    # Get the project root directory
    script_dir = Path(__file__).resolve().parent
    project_dir = script_dir.parent

    print("\n=== Indian Traffic Sign Detection Model Training and Integration ===")
    print(f"Project directory: {project_dir}")

    # 1. Install required packages if needed
    requirements = ["ultralytics"]
    for req in requirements:
        try:
            __import__(req)
            print(f"{req} is already installed.")
        except ImportError:
            print(f"{req} not found. Installing...")
            run_command(f"pip install {req}", f"Installing {req}")

    if not args.skip_train:
        # 2. Train the model
        train_cmd = (
            f"python {script_dir}/train_traffic_sign_model.py "
            f"--model-size {args.model_size} "
            f"--epochs {args.epochs} "
            f"--batch-size {args.batch_size}"
        )
        run_command(train_cmd, "Training the Indian Traffic Sign Detection model")

    if not args.skip_test:
        # 3. Test the model
        test_cmd = f"python {script_dir}/test_traffic_sign_model.py"
        run_command(test_cmd, "Testing the trained model")

    # 4. Verify the detector
    verify_cmd = (
        "python -c \"from backend.detectors.traffic_sign_detector import TrafficSignDetector; "
        "detector = TrafficSignDetector(); print('TrafficSignDetector initialized successfully');\""
    )
    run_command(verify_cmd, "Verifying the TrafficSignDetector class")

    print("\n=== Process Completed ===")
    print("You can now use the Indian Traffic Sign Detection model in your STMS backend.")

if __name__ == "__main__":
    main()
