"""
UE Controller - Face Detection Program
Idle runs continuously in background.
Camera stays open for continuous face detection.
Tracking launches when face detected (camera released, windows minimized, tracking fullscreen).
Camera reopened after tracking closes.
"""
import time
import sys
import os
import subprocess
from pathlib import Path

from config import Config
from face_detector import FaceDetector
from mode_decider import ModeDecider
from program_runner import ProgramRunner
from camera_handler import CameraHandler
from window_manager import WindowManager


class UEController:
    """Controls launching tracking program based on face detection."""
    
    def __init__(self, config_path: str = "config.json"):
        self.config = Config(config_path)
        self.face_detector = FaceDetector(self.config.face_detection_confidence)
        self.mode_decider = ModeDecider(self.config.detection_threshold_seconds)
        self.program_runner = ProgramRunner()
        self.camera_handler = CameraHandler(
            self.config.camera_index, 
            self.face_detector
        )
        self.window_manager = WindowManager()
        self._idle_process = None
        self._tracking_running = False
    
    def _print_banner(self):
        """Print startup banner."""
        print("=" * 50)
        print("UE Controller - Face Detection Program")
        print("=" * 50)
        print(f"Tracking EXE: {self.config.tracking_exe}")
        print(f"Idle EXE: {self.config.idle_exe}")
        print(f"Face detection threshold: {self.config.detection_threshold_seconds}s")
        print("=" * 50)
        print("\nFlow: IDLE runs continuously")
        print("      CAMERA stays open for face detection")
        print("      ↓ face detected")
        print("      WINDOWS minimized → CAMERA released → TRACKING fullscreen")
        print("      ↓ tracking closed")
        print("      CAMERA reopened → back to monitoring\n")
    
    def _start_idle(self) -> bool:
        """Start the idle program (runs continuously in background)."""
        idle_path = self.config.idle_exe
        
        if not os.path.exists(idle_path):
            print(f"[ERROR] Idle EXE not found: {idle_path}")
            return False
        
        try:
            print(f"[INFO] Starting idle program (background)...")
            # Start minimized/in background
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 7  # SW_SHOWMINNOACTIVE - minimized, not active
            
            self._idle_process = subprocess.Popen(
                [idle_path],
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                startupinfo=startupinfo
            )
            print(f"[INFO] Idle program started (PID: {self._idle_process.pid})")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to start idle: {e}")
            return False
    
    def _check_idle_running(self) -> bool:
        """Check if idle is still running."""
        if self._idle_process is None:
            return False
        return self._idle_process.poll() is None
    
    def _restart_idle_if_needed(self):
        """Restart idle if it crashed or exited."""
        if not self._check_idle_running():
            print("[INFO] Idle program not running, restarting...")
            self._start_idle()
    
    def _check_face_detected(self) -> bool:
        """Check camera for face detection."""
        face_found = self.camera_handler.check_face()
        result = self.mode_decider.update(face_found)
        return result == "tracking"
    
    def _run_tracking(self):
        """Run tracking program in fullscreen after minimizing windows."""
        tracking_path = self.config.tracking_exe
        
        if not os.path.exists(tracking_path):
            print(f"[ERROR] Tracking EXE not found: {tracking_path}")
            return
        
        self._tracking_running = True
        print(f"[INFO] Preparing to launch tracking...")
        
        # Minimize all windows
        self.window_manager.minimize_all_windows()
        
        # Launch tracking in fullscreen
        self.window_manager.launch_fullscreen(tracking_path, "tracking")
        
        print("[INFO] Tracking closed")
        self._tracking_running = False
        self.mode_decider.reset()
    
    def run(self):
        """Main loop: idle runs, camera open, tracking launches on face detect."""
        self._print_banner()
        
        # Start idle first
        if not self._start_idle():
            print("[ERROR] Failed to start idle program. Exiting.")
            return
        
        # Open camera for continuous face detection
        if not self.camera_handler.open():
            print("[ERROR] Failed to open camera. Exiting.")
            self._cleanup()
            return
        
        try:
            while True:
                # Ensure idle is running
                self._restart_idle_if_needed()
                
                # Check for faces while idle runs
                if self._check_face_detected():
                    print("[INFO] Face detected! Preparing to launch tracking...")
                    
                    # Release camera so tracking can use it
                    print("[INFO] Releasing camera for tracking...")
                    self.camera_handler.release()
                    
                    # Launch tracking (minimizes windows, launches fullscreen)
                    self._run_tracking()
                    
                    # Reopen camera for continued monitoring
                    print("[INFO] Reopening camera...")
                    if not self.camera_handler.open():
                        print("[ERROR] Failed to reopen camera. Exiting.")
                        break
                    
                    print("[INFO] Back to monitoring...")
                
                # Small delay between checks
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\n[INFO] Shutting down...")
            self._cleanup()
        except Exception as e:
            print(f"[ERROR] {e}")
            self._cleanup()
    
    def _cleanup(self):
        """Clean up processes on shutdown."""
        print("[INFO] Cleaning up...")
        
        # Release camera
        self.camera_handler.release()
        
        # Stop idle
        if self._idle_process and self._check_idle_running():
            try:
                print("[INFO] Stopping idle program...")
                self._idle_process.terminate()
                try:
                    self._idle_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self._idle_process.kill()
                    self._idle_process.wait(timeout=2)
            except Exception as e:
                print(f"[WARN] Error stopping idle: {e}")


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
