# UE Controller - Motion Detection Program

A simple Python program that monitors a camera and switches between two Unreal Engine executables based on motion detection.

## How It Works

This program uses **TIME-BASED HANDOFF** to solve the single camera problem:

```
[Controller] → Launches UE_Tracking.exe → Runs for 30 seconds → Exits
[Controller] → Opens camera, checks for motion → No motion detected
[Controller] → Launches UE_Idle.exe → Runs for 60 seconds → Exits  
[Controller] → Opens camera, checks for motion → Motion detected!
[Controller] → Launches UE_Tracking.exe → Runs for 30 seconds → Exits
...continues loop
```

**Key point:** Your UE programs must be designed to run briefly and exit automatically. The controller waits for the program to finish before checking the camera.

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Edit config.json
Update the paths to your Unreal Engine executables:

```json
{
    "tracking_exe": "C:\\Path\\To\\Your\\Tracking.exe",
    "idle_exe": "C:\\Path\\To\\Your\\Idle.exe",
    "camera_index": 0,
    "motion_threshold": 30,
    "detection_delay_frames": 5,
    "tracking_run_seconds": 30,
    "idle_run_seconds": 60
}
```

### Configuration Options

| Setting | Description | Default |
|---------|-------------|---------|
| `tracking_exe` | Path to UE program when someone is detected | (required) |
| `idle_exe` | Path to UE program when empty | (required) |
| `camera_index` | Which camera to use (0 = default) | 0 |
| `motion_threshold` | Motion sensitivity (lower = more) | 30 |
| `detection_delay_frames` | Frames to check before switching | 5 |
| `tracking_run_seconds` | How long to run tracking program | 30 |
| `idle_run_seconds` | How long to run idle program | 60 |

## Run the Program

```bash
python ue_controller.py
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
- Lower `motion_threshold` to make detection more sensitive

### Too much switching
- Increase `detection_delay_frames` for more stability
- Increase `idle_run_seconds` to run idle longer between checks
