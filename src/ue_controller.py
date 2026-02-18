"""
UE Controller - Face Detection Program
Switches between two Unreal Engine executables based on face detection.
Idle runs continuously until face detected, then tracking launches.
Tracking runs until manually closed, then returns to idle.
"""
import time
import sys
from pathlib import Path

from config import Config
from face_detector import FaceDetector
from mode_decider import ModeDecider
from program_runner import ProgramRunner
from camera_handler import CameraHandler


class UEController:
    """Controls switching between UE programs based on face detection."""
    
    def __init__(self, config_path: str = "config.json"):
        self.config = Config(config_path)
        self.face_detector = FaceDetector(self.config.face_detection_confidence)
        self.mode_decider = ModeDecider(self.config.detection_threshold_seconds)
        self.program_runner = ProgramRunner()
        self.camera_handler = CameraHandler(
            self.config.camera_index, 
            self.face_detector
        )
        self.current_mode = None
    
    def _print_banner(self):
        """Print startup banner."""
        print("=" * 50)
        print("UE Controller - Face Detection Program")
        print("=" * 50)
        print(f"Tracking EXE: {self.config.tracking_exe}")
        print(f"Idle EXE: {self.config.idle_exe}")
        print(f"Face detection threshold: {self.config.detection_threshold_seconds}s")
        print("=" * 50)
        print("\nFlow: IDLE → [face detected] → TRACKING → [manual close] → IDLE")
        print("Idle runs until face detected. Tracking runs until manually closed.\n")
    
    def _get_exe_path(self, mode: str) -> str:
        """Get executable path for a mode."""
        if mode == "tracking":
            return self.config.tracking_exe
        return self.config.idle_exe
    
    def _check_face_detected(self) -> bool:
        """Check camera for face detection."""
        print("[INFO] Checking camera for faces...")
        face_found = self.camera_handler.check_face()
        result = self.mode_decider.update(face_found)
        print(f"[RESULT] Mode decision: {result}")
        return result == "tracking"
    
    def run(self):
        """Main loop: idle runs, face detected → tracking, tracking closed → idle."""
        self._print_banner()
        
        try:
            while True:
                # Always start with idle
                idle_path = self._get_exe_path("idle")
                self.current_mode = "idle"
                
                # Run idle in background and continuously check for faces
                print("[INFO] Starting idle mode (checking for faces)...")
                
                # Launch idle program (non-blocking check loop)
                import subprocess
                import os
                
                if not os.path.exists(idle_path):
                    print(f"[ERROR] Idle EXE not found: {idle_path}")
                    time.sleep(5)
                    continue
                
                # Start idle program
                idle_process = subprocess.Popen(
                    [idle_path],
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
                print(f"[INFO] Idle program started (PID: {idle_process.pid})")
                
                # While idle is running, check for faces
                face_detected = False
                while idle_process.poll() is None:  # While idle is still running
                    face_detected = self._check_face_detected()
                    if face_detected:
                        print("[INFO] Face detected! Switching to tracking...")
                        break
                    time.sleep(0.5)  # Check every 0.5 seconds
                
                # If idle exited on its own, restart it
                if idle_process.poll() is not None and not face_detected:
                    print("[INFO] Idle program exited, restarting...")
                    time.sleep(1)
                    continue
                
                # Face detected - terminate idle and launch tracking
                if face_detected:
                    print("[INFO] Stopping idle program...")
                    idle_process.terminate()
                    try:
                        idle_process.wait(timeout=5)
                    except:
                        idle_process.kill()
                    
                    # Launch tracking
                    tracking_path = self._get_exe_path("tracking")
                    self.current_mode = "tracking"
                    self.program_runner.run(tracking_path, "tracking")
                    
                    # Tracking closed - reset decider and continue to idle
                    print("[INFO] Tracking closed, returning to idle...")
                    self.mode_decider.reset()
                    time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n[INFO] Shutting down...")
            if hasattr(self, 'idle_process') and self.idle_process:
                self.idle_process.terminate()
        except Exception as e:
            print(f"[ERROR] {e}")


if __name__ == "__main__":
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.json"
    
    try:
        controller = UEController(config_path)
        controller.run()
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        print("Please create config.json with your EXE paths")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
