"""
UE Controller - Face Detection Program
Idle runs continuously in background.
Detection UI shows camera feed with adjustable boundary box.
Tracking launches when face detected within boundary.
"""
import time
import sys
import os

from config import Config
from face_detector import FaceDetector
from mode_decider import ModeDecider
from program_runner import ProgramRunner
from detection_ui import DetectionUI
from window_manager import WindowManager
from process_manager import ProcessManager


class UEController:
    """Controls launching tracking program based on face detection with UI."""
    
    def __init__(self, config_path: str = "config.json"):
        self.config = Config(config_path)
        self.face_detector = FaceDetector(self.config.face_detection_confidence)
        self.mode_decider = ModeDecider(
            threshold_seconds=self.config.detection_threshold_seconds,
            grace_period=0.5
        )
        self.program_runner = ProgramRunner()
        self.detection_ui = DetectionUI(
            window_name="Face Detection",
            camera_index=self.config.camera_index
        )
        self.window_manager = WindowManager()
        self.idle_manager = ProcessManager(self.config.idle_exe)
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
    
    def _get_detection_status(self) -> str:
        """Get current detection status text."""
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
        
        self.window_manager.launch_fullscreen(tracking_path, "tracking")
        
        print("[INFO] Tracking closed")
        self._tracking_running = False
        self.mode_decider.reset()
    
    def _setup_face_detection(self):
        """Setup boundary check callback for face detector."""
        self.face_detector.set_boundary_check(
            lambda rect: self.detection_ui.is_face_in_boundary(rect)
        )
    
    def run(self):
        """Main loop with detection UI."""
        self._print_banner()
        
        # Start idle first
        if not self.idle_manager.start():
            print("[ERROR] Failed to start idle program. Exiting.")
            return
        
        # Open detection UI (also opens camera)
        if not self.detection_ui.open():
            print("[ERROR] Failed to open camera/UI. Exiting.")
            self._cleanup()
            return
        
        # Setup face detection with boundary check
        self._setup_face_detection()
        # Re-setup when boundary is dragged
        self.detection_ui.set_drag_callback(self._setup_face_detection)
        
        try:
            while True:
                # Ensure idle is running
                self.idle_manager.ensure_running()
                
                # Read frame and detect faces
                frame = self.detection_ui.read_frame()
                if frame is None:
                    continue
                
                face_found, face_rects = self.face_detector.detect(frame)
                result = self.mode_decider.update(face_found)
                
                # Update UI
                config_info = {
                    'threshold': self.config.detection_threshold_seconds,
                    'confidence': self.config.face_detection_confidence
                }
                status = self._get_detection_status()
                
                if not self.detection_ui.update(config_info, status, face_rects):
                    print("[INFO] UI closed by user")
                    break
                
                # Check if we should launch tracking
                if result == "tracking" and not self._tracking_running:
                    self._launch_tracking_sequence()
                
                time.sleep(0.05)  # ~20 FPS
                
        except KeyboardInterrupt:
            print("\n[INFO] Shutting down...")
        except Exception as e:
            print(f"[ERROR] {e}")
        finally:
            self._cleanup()
    
    def _launch_tracking_sequence(self):
        """Close UI, launch tracking, reopen UI."""
        print("[INFO] Face detected! Preparing to launch tracking...")
        
        # Close UI to release camera
        print("[INFO] Closing UI to release camera...")
        self.detection_ui.release()
        
        # Launch tracking
        self._run_tracking()
        
        # Reopen UI for continued monitoring
        print("[INFO] Reopening UI...")
        if not self.detection_ui.open():
            print("[ERROR] Failed to reopen UI. Exiting.")
            return
        
        # Re-setup face detection
        self._setup_face_detection()
        self.detection_ui.set_drag_callback(self._setup_face_detection)
        
        print("[INFO] Back to monitoring...")
    
    def _cleanup(self):
        """Clean up processes on shutdown."""
        print("[INFO] Cleaning up...")
        self.detection_ui.release()
        self.idle_manager.stop()


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
