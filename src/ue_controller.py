"""
UE Controller - Face Detection Program
Switches between two Unreal Engine executables based on face detection
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
        print(f"Tracking run time: {self.config.tracking_run_seconds} seconds")
        print(f"Idle run time: {self.config.idle_run_seconds} seconds")
        print("=" * 50)
        print("\nIMPORTANT: Your UE programs must be designed to run briefly")
        print("and exit automatically. The controller waits for the program")
        print("to finish before checking the camera.\n")
    
    def _get_exe_and_duration(self, mode: str) -> tuple:
        """Get executable path and duration for a mode."""
        if mode == "tracking":
            return self.config.tracking_exe, self.config.tracking_run_seconds
        return self.config.idle_exe, self.config.idle_run_seconds
    
    def _decide_next_mode(self) -> str:
        """Check camera and decide next mode."""
        print("[INFO] Checking camera for faces...")
        face_found = self.camera_handler.check_face()
        return self.mode_decider.update(face_found)
    
    def run(self):
        """Main loop: run programs briefly, then check camera."""
        self._print_banner()
        
        recommended_mode = "idle"
        
        try:
            while True:
                exe_path, duration = self._get_exe_and_duration(recommended_mode)
                
                # Run the UE program (blocks until it exits)
                self.program_runner.run(exe_path, recommended_mode, duration)
                self.current_mode = recommended_mode
                
                # Decide next mode
                recommended_mode = self._decide_next_mode()
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n[INFO] Shutting down...")
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
