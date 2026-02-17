# UE Controller - Face Detection Program

A Python program that monitors a camera and switches between two Unreal Engine executables based on face detection.

## Project Structure

```
.
├── src/
│   ├── ue_controller.py      # Main controller (orchestrator)
│   ├── config.py             # Configuration management
│   ├── face_detector.py      # Face detection using OpenCV Haar Cascade
│   ├── mode_decider.py       # Mode decision logic (time-based)
│   ├── program_runner.py     # External program execution
│   └── camera_handler.py     # Camera access management
├── projects/
│   ├── idle/                 # Idle mode UE program
│   │   └── can.exe
│   └── tracking/             # Tracking mode UE program
│       └── mediapipe.exe
├── tests/
│   ├── conftest.py           # Shared test fixtures
│   ├── test_config.py        # Config tests
│   ├── test_face_detector.py # Face detection tests
│   ├── test_mode_decider.py  # Mode decision tests
│   └── test_program_runner.py
├── config.json               # Configuration file
├── requirements.txt          # Python dependencies
└── README.md
```

## Architecture

The codebase follows **SOLID principles**:

- **Single Responsibility**: Each module has one job
  - `config.py` - Configuration loading
  - `face_detector.py` - Face detection using Haar Cascade
  - `mode_decider.py` - Time-based decision logic
  - `program_runner.py` - Program execution
  - `camera_handler.py` - Camera resource management
  - `ue_controller.py` - Orchestration only

- **Dependency Inversion**: High-level modules depend on abstractions, not concrete implementations

## How It Works

This program uses **TIME-BASED HANDOFF** to solve the single camera problem:

```
[Controller] → Launches tracking program → Runs for 30 seconds → Exits
[Controller] → Opens camera, checks for faces → No face detected
[Controller] → Launches idle program → Runs for 60 seconds → Exits  
[Controller] → Opens camera, checks for faces → Face detected!
[Controller] → Launches tracking program → Runs for 30 seconds → Exits
...continues loop
```

**Key point:** Your UE programs must be designed to run briefly and exit automatically. The controller waits for the program to finish before checking the camera.

### Face Detection Logic

The controller uses **time-based thresholds** (not frame counts):

- **Switch to tracking**: Face must be present for `detection_threshold_seconds` continuously
- **Switch to idle**: Face must be absent for `detection_threshold_seconds` continuously

This prevents flickering between modes when faces appear/disappear briefly.

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Edit config.json
Update the paths to your Unreal Engine executables:

```json
{
    "tracking_exe": "projects/tracking/mediapipe.exe",
    "idle_exe": "projects/idle/can.exe",
    "camera_index": 0,
    "face_detection_confidence": 0.5,
    "detection_threshold_seconds": 3.0,
    "tracking_run_seconds": 30,
    "idle_run_seconds": 60
}
```

### Configuration Options

| Setting | Description | Default |
|---------|-------------|---------|
| `tracking_exe` | Path to UE program when face detected | (required) |
| `idle_exe` | Path to UE program when no face | (required) |
| `camera_index` | Which camera to use (0 = default) | 0 |
| `face_detection_confidence` | Face detection sensitivity (0.0-1.0) | 0.5 |
| `detection_threshold_seconds` | Seconds of continuous face presence/absence before switching | 3.0 |
| `tracking_run_seconds` | How long to run tracking program | 30 |
| `idle_run_seconds` | How long to run idle program | 60 |

## Run the Program

```bash
python src/ue_controller.py
```

Or with a custom config path:
```bash
python src/ue_controller.py path/to/config.json
```

## Running Tests

The project includes unit tests for all modules:

```bash
pytest tests/ -v
```

Or run specific test files:
```bash
pytest tests/test_face_detector.py -v
pytest tests/test_mode_decider.py -v
pytest tests/test_config.py -v
pytest tests/test_program_runner.py -v
```

## Important - UE Program Requirements

Your Unreal Engine programs MUST be designed to:
- **Run briefly** (e.g., 10-60 seconds)
- **Exit automatically** when done
- NOT run indefinitely

The controller waits for your program to exit before it can check the camera again.

### Example UE Logic:
```
On BeginPlay:
    Do your metahuman tracking for X seconds
    Save results if needed
    ExecuteConsoleCommand("quit")  // Exit the program
```

## Troubleshooting

### "Camera already in use" error
- Your UE program is not exiting properly
- Make sure your UE programs call "quit" or exit after their runtime

### Programs never switch
- Increase `tracking_run_seconds` to give more time
- Lower `face_detection_confidence` to make detection more sensitive
- Lower `detection_threshold_seconds` to switch faster

### Too much switching
- Increase `detection_threshold_seconds` for more stability
- Increase `idle_run_seconds` to run idle longer between checks

## Dependencies

- Python 3.7+
- OpenCV (opencv-python>=4.8.0) - includes Haar Cascade classifiers
- NumPy (numpy>=1.24.0)
- pytest (for testing)
