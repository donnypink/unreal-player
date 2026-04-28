# UE Controller - Face Detection Screen-Saver

A Python program that monitors a camera and switches between idle and tracking programs based on face detection. When a face is detected in the configured zone for a threshold duration, the tracking program launches fullscreen. When the face is lost for a grace period, tracking closes and idle returns to foreground.

## Project Structure

```
.
├── src/
│   ├── ue_controller.py      # Main controller (orchestrator)
│   ├── config.py             # Configuration management
│   ├── face_detector.py      # Face detection using OpenCV Haar Cascade
│   ├── mode_decider.py       # Mode decision logic (time-based)
│   ├── program_runner.py     # External program execution
│   ├── detection_ui.py       # Detection UI with boundary box
│   ├── camera_manager.py     # Camera access management
│   ├── boundary_renderer.py  # UI rendering for detection boundary
│   ├── window_manager.py     # Window switching (foreground/background)
│   ├── process_manager.py    # Idle process lifecycle
│   └── audio_feedback.py     # Audio feedback for detection events
├── projects/
│   ├── idle/                 # Idle mode UE program (runs continuously)
│   └── tracking/             # Tracking mode UE program (launched on face detect)
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
  - `detection_ui.py` - UI with draggable detection boundary
  - `camera_manager.py` - Camera resource management
  - `boundary_renderer.py` - Renders detection boundary and overlays
  - `window_manager.py` - Window switching (foreground/background/maximize/minimize)
  - `process_manager.py` - Manages idle program lifecycle
  - `audio_feedback.py` - Audio feedback for detection events
  - `ue_controller.py` - Orchestration only

## Screen-Saver Behavior

```
[IDLE] fullscreen ─────────────────────────────────────
   │                                                    │
   │ runs continuously (VLC video loop)                │
   │                                                    │
   ↓ face detected in zone for threshold seconds        │
[TRACKING] fullscreen ────────────────────────────────→
   │ launched, idle minimized                          │
   │                                                    │
   ↓ face lost for grace period                         │
[IDLE] returns to foreground ──────────────────────────┘
   tracking closes, idle maximized
```

**Flow:**
1. **Idle** program (VLC) launches and runs **continuously** in fullscreen
2. Detection camera monitors for faces within the boundary zone
3. When face detected for `detection_threshold_seconds` → **Tracking** launches fullscreen
4. Idle is minimized (stays running in background)
5. When face lost for `face_loss_grace_period` → **Tracking** closes
6. Idle returns to foreground fullscreen
7. Detection UI stays visible throughout

### Face Detection Logic

- **Launch tracking**: Face must be present in zone for `detection_threshold_seconds` continuously (default: 3.0s)
- **Close tracking**: Face must be lost for `face_loss_grace_period` (default: 2.0s)
- Uses separate detection camera (`detection_camera_index`) from tracking program

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Edit config.json
```json
{
    "tracking_exe": "projects/tracking/mediapipe.exe",
    "idle_exe": "\"C:\\Program Files\\VideoLAN\\VLC\\vlc.exe\" --fullscreen --loop \"video.mp4\"",
    "detection_camera_index": 0,
    "face_detection_confidence": 0.5,
    "detection_threshold_seconds": 3.0,
    "face_loss_grace_period": 2.0,
    "audio_enabled": false,
    "sound_dir": "sounds"
}
```

### Configuration Options

| Setting | Description | Default |
|---------|-------------|---------|
| `tracking_exe` | Path to UE program launched when face detected | (required) |
| `idle_exe` | Path to video player with idle video (e.g., VLC) | (required) |
| `detection_camera_index` | Which camera to use for face detection | 0 |
| `face_detection_confidence` | Face detection sensitivity (0.0-1.0) | 0.5 |
| `detection_threshold_seconds` | Seconds of continuous face presence before launching tracking | 3.0 |
| `face_loss_grace_period` | Seconds of face absence before closing tracking | 2.0 |
| `audio_enabled` | Enable audio feedback for detection events | `false` |
| `sound_dir` | Directory for custom sound files | `sounds` |

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

## Important - Program Requirements

### Idle Program
- Runs **continuously** in fullscreen (e.g., VLC with looping video)
- Should **NOT** use the detection camera
- Will be restarted if it crashes

### Tracking Program
- Launched when a face is detected and stays running while face is present
- Can use its own camera for metahuman tracking
- Closes automatically after face loss grace period
- When closed, idle returns to foreground

## Window Management

The `window_manager.py` module handles window switching:

- `launch_nonblocking(cmd)` - Launch process without blocking
- `find_window(pid)` - Find window handle by process ID (with retry)
- `bring_to_foreground(hwnd)` - Bring window to front
- `maximize(hwnd)` / `minimize(hwnd)` - Window state controls

This ensures smooth transitions between idle and tracking programs.

## Troubleshooting

### "Camera already in use" error
- Make sure idle program doesn't access the camera
- Check `detection_camera_index` in config.json

### Programs never switch to tracking
- Lower `face_detection_confidence` to make detection more sensitive
- Lower `detection_threshold_seconds` to launch faster
- Ensure good lighting for face detection
- Ensure face is within the boundary zone

### Too much switching
- Increase `detection_threshold_seconds` for more stable launch
- Increase `face_loss_grace_period` to reduce rapid switching
- Adjust camera position for better face visibility

### Idle program crashes
- Controller will automatically restart idle if it exits
- Check idle program logs for errors

## Dependencies

- Python 3.7+
- OpenCV (opencv-python>=4.8.0) - includes Haar Cascade classifiers
- NumPy (numpy>=1.24.0)
- pygame (pygame>=2.5.0) - audio feedback
- pytest (for testing)

## Audio Feedback

The program provides optional audio feedback for detection events:

- **Detection Start**: Plays when a face is first detected in the boundary zone
- **Tracking Launch**: Plays when tracking program is about to launch
- **Tracking Close**: Plays when tracking program closes

### Audio Configuration

```json
{
    "audio_enabled": true,
    "sound_dir": "sounds"
}
```

### Custom Sounds

Place custom WAV files in the `sounds/` directory:
- `start_beep.wav` - Face detection start sound
- `tracking_close.wav` - Tracking close sound

If custom sounds are not found, the program falls back to silent mode.