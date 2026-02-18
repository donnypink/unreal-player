# UE Controller - Face Detection Program

A Python program that monitors a camera and launches a tracking Unreal Engine executable when a face is detected. The idle program runs continuously in the background.

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
│   ├── idle/                 # Idle mode UE program (runs continuously)
│   │   └── can.exe
│   └── tracking/             # Tracking mode UE program (launched on face detect)
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

The program follows this flow:

```
[IDLE] ────────────────────────────────────────────────
  │                                                    │
  │ runs continuously in background                  │
  │                                                    │
  ↓ face detected for threshold seconds               │
[TRACKING] launches ────────────────────────────────→ │
  │ runs until manually closed                         │
  │                                                    │
  ↓ user closes tracking                               │
  └────────────────────────────────────────────────────┘
       (IDLE was running all along, continues)
```

**Flow:**
1. **Idle** program launches and runs **continuously** in the background
2. Camera checks for faces every 0.5 seconds
3. When face detected for `detection_threshold_seconds` → **Tracking** launches
4. **Idle keeps running** (not stopped)
5. Tracking runs until **manually closed** by user
6. After Tracking closes → back to monitoring (Idle still running)
7. Loop continues

### Face Detection Logic

- **Launch tracking**: Face must be present for `detection_threshold_seconds` continuously (default: 3.0s)
- **Return to monitoring**: Tracking runs until user manually closes it
- This prevents flickering when faces appear/disappear briefly

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
    "detection_threshold_seconds": 3.0
}
```

### Configuration Options

| Setting | Description | Default |
|---------|-------------|---------|
| `tracking_exe` | Path to UE program launched when face detected | (required) |
| `idle_exe` | Path to UE program that runs continuously | (required) |
| `camera_index` | Which camera to use (0 = default) | 0 |
| `face_detection_confidence` | Face detection sensitivity (0.0-1.0) | 0.5 |
| `detection_threshold_seconds` | Seconds of continuous face presence before launching tracking | 3.0 |

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

Your Unreal Engine programs should be designed as follows:

### Idle Program
- Runs **continuously** in the background (never exits)
- Should **NOT** use the camera (controller owns camera access)
- Should be lightweight
- Will be restarted if it crashes

### Tracking Program
- Launched when a face is detected
- **Can** use the camera for metahuman tracking
- Must be **manually closed** by user when done
- When closed, controller continues monitoring (idle still running)

## Troubleshooting

### "Camera already in use" error
- Make sure idle program doesn't access the camera
- Only tracking program should use camera

### Programs never switch to tracking
- Lower `face_detection_confidence` to make detection more sensitive
- Lower `detection_threshold_seconds` to launch faster
- Ensure good lighting for face detection

### Too much switching
- Increase `detection_threshold_seconds` for more stability
- Adjust camera position for better face visibility

### Idle program crashes
- Controller will automatically restart idle if it exits
- Check idle program logs for errors

## Dependencies

- Python 3.7+
- OpenCV (opencv-python>=4.8.0) - includes Haar Cascade classifiers
- NumPy (numpy>=1.24.0)
- pytest (for testing)
