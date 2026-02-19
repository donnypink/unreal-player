"""
UE Controller - Face Detection Program
Idle runs continuously in background.
Detection UI shows camera feed with adjustable boundary box.
Tracking launches when face detected within boundary.
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
from detection_ui import DetectionUI
from window_manager import WindowManager


class UEController:
    """Controls launching tracking program based on face detection with UI."""
    
    def __init__(self, config_path: str = "config.json"):
        self.config = Config(config_path)
        self.face_detector = FaceDetector(self.config.face_detection_confidence)
        self.mode_decider = ModeDecider(
            threshold_seconds=self.config.detection_threshold_seconds,
            grace_period=0.5  # 500ms grace period for brief detection failures
        )
        self.program_runner = ProgramRunner()
        self.detection_ui = DetectionUI("Face Detection")
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
        print("\nFlow: IDLE runs continuously (background)")
        print("      UI shows camera feed with detection zone")
        print("      ↓ face detected IN zone")
        print("      UI closed → TRACKING fullscreen → UI reopened")
        print("      Press 'q' in UI to quit\n")
    
    def _start_idle(self) -> bool:
        """Start the idle program (runs continuously in background)."""
        idle_path = self.config.idle_exe
        
        if not os.path.exists(idle_path):
            print(f"[ERROR] Idle EXE not found: {idle_path}")
            return False
        
        try:
            print(f"[INFO] Starting idle program (background)...")
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0  # SW_HIDE - hidden
            
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
    
    def _get_detection_status(self) -> str:
        """Get current detection status text."""
        mode = self.mode_decider.update(False)  # Check mode without updating
        if self._tracking_running:
            return "TRACKING RUNNING"
        elif self.mode_decider.is_face_present:
            return f"FACE DETECTED ({self.mode_decider.face_duration:.1f}s)"
        else:
            return "MONITORING"
    
    def _run_tracking(self):
        """Run tracking program in fullscreen foreground."""
        tracking_path = self.config.tracking_exe
        
        if not os.path.exists(tracking_path):
            print(f"[ERROR] Tracking EXE not found: {tracking_path}")
            return
        
        self._tracking_running = True
        print(f"[INFO] Launching tracking in fullscreen...")
        
        # Launch tracking in fullscreen (foreground)
        self.window_manager.launch_fullscreen(tracking_path, "tracking")
        
        print("[INFO] Tracking closed")
        self._tracking_running = False
        self.mode_decider.reset()
    
    def run(self):
        """Main loop with detection UI."""
        self._print_banner()
        
        # Start idle first
        if not self._start_idle():
            print("[ERROR] Failed to start idle program. Exiting.")
            return
        
        # Open detection UI (also opens camera)
        if not self.detection_ui.open(self.config.camera_index):
            print("[ERROR] Failed to open camera/UI. Exiting.")
            self._cleanup()
            return
        
        # Set up boundary check callback
        self.face_detector.set_boundary_check(
            lambda rect: self.detection_ui.is_face_in_boundary(rect)
        )
        
        try:
            while True:
                # Ensure idle is running
                self._restart_idle_if_needed()
                
                # Read frame from camera
                frame = self.detection_ui.read_frame()
                if frame is None:
                    continue
                
                # Detect faces
                face_found, face_rects = self.face_detector.detect(frame)
                print(f"[DEBUG] face_found={face_found}, face_rects={len(face_rects)}")
                
                # Update mode decider
                result = self.mode_decider.update(face_found)
                print(f"[DEBUG] mode_decider result={result}, is_face_present={self.mode_decider.is_face_present}, face_duration={self.mode_decider.face_duration:.2f}s")
                
                # Prepare config info for UI
                config_info = {
                    'threshold': self.config.detection_threshold_seconds,
                    'confidence': self.config.face_detection_confidence
                }
                
                # Update UI
                status = self._get_detection_status()
                ui_running = self.detection_ui.update(
                    config_info, status, face_rects
                )
                
                if not ui_running:
                    print("[INFO] UI closed by user")
                    break
                
                # Check if we should launch tracking
                if result == "tracking" and not self._tracking_running:
                    print("[INFO] Face detected! Preparing to launch tracking...")
                    
                    # Close UI to release camera
                    print("[INFO] Closing UI to release camera...")
                    self.detection_ui.release()
                    
                    # Launch tracking
                    self._run_tracking()
                    
                    # Reopen UI for continued monitoring
                    print("[INFO] Reopening UI...")
                    if not self.detection_ui.open(self.config.camera_index):
                        print("[ERROR] Failed to reopen UI. Exiting.")
                        break
                    
                    # Re-setup boundary check
                    self.face_detector.set_boundary_check(
                        lambda rect: self.detection_ui.is_face_in_boundary(rect)
                    )
                    
                    print("[INFO] Back to monitoring...")
                
                time.sleep(0.05)  # ~20 FPS
                
        except KeyboardInterrupt:
            print("\n[INFO] Shutting down...")
            self._cleanup()
        except Exception as e:
            print(f"[ERROR] {e}")
            self._cleanup()
    
    def _cleanup(self):
        """Clean up processes on shutdown."""
        print("[INFO] Cleaning up...")
        
        # Close UI
        self.detection_ui.release()
        
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
