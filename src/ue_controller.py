"""
UE Controller - Face Detection Program
Screen-saver style switching:
- Idle program (VLC) runs continuously in background
- Detection camera shows UI with boundary zone
- Face detected -> Tracking launches fullscreen foreground
- Face lost for grace period -> Tracking closes, Idle returns to foreground
- Press 'q' in detection UI to quit
"""
import time
import sys
import os
import subprocess
import signal

from config import Config
from face_detector import FaceDetector
from mode_decider import ModeDecider
from program_runner import ProgramRunner
from detection_ui import DetectionUI
from window_manager import WindowManager, parse_command_string
from process_manager import ProcessManager
from audio_feedback import AudioFeedback


class UEController:
    """Controls launching tracking program based on face detection with UI.

    Screen-saver mode: Idle runs continuously. Tracking is launched/closed
    dynamically based on face presence. Detection UI stays visible.
    """

    def __init__(self, config_path: str = "config.json"):
        self.config = Config(config_path)
        self.face_detector = FaceDetector(self.config.face_detection_confidence)
        self.mode_decider = ModeDecider(
            threshold_seconds=self.config.detection_threshold_seconds,
            grace_period=0.5,
            face_loss_grace_period=self.config.face_loss_grace_period
        )
        self.program_runner = ProgramRunner()
        self.detection_ui = DetectionUI(
            window_name="Face Detection",
            camera_index=self.config.detection_camera_index
        )
        self.window_manager = WindowManager()
        self.idle_manager = ProcessManager(self.config.idle_exe)
        self.audio = AudioFeedback(
            enabled=self.config.audio_enabled,
            sound_dir=self.config.sound_dir
        )
        self._tracking_process = None  # Track the tracking program process
        self._tracking_running = False
        self._last_face_state = False  # Track state change for audio

    def _print_banner(self):
        """Print startup banner."""
        print("=" * 50)
        print("UE Controller - Face Detection Program")
        print("=" * 50)
        print(f"Detection Camera: {self.config.detection_camera_index}")
        print(f"Tracking EXE: {self.config.tracking_exe}")
        print(f"Idle EXE: {self.config.idle_exe}")
        print(f"Face detection threshold: {self.config.detection_threshold_seconds}s")
        print(f"Face loss grace period: {self.config.face_loss_grace_period}s")
        print("=" * 50)
        print("\nFlow: IDLE runs continuously (background)")
        print("      UI shows camera feed with detection zone")
        print("      ↓ face detected IN zone")
        print("      TRACKING fullscreen → IDLE stays hidden")
        print("      ↓ face lost for grace period")
        print("      TRACKING closes → IDLE returns fullscreen")
        print("      Press 'q' in UI to quit\n")

    def _get_detection_status(self) -> str:
        """Get current detection status text."""
        if self._tracking_running:
            if self.mode_decider.time_since_face_lost > 0:
                remaining = self.config.face_loss_grace_period - self.mode_decider.time_since_face_lost
                if remaining > 0:
                    return f"TRACKING (face lost: {remaining:.1f}s to close)"
            return "TRACKING RUNNING"
        elif self.mode_decider.is_face_present:
            return f"FACE DETECTED ({self.mode_decider.face_duration:.1f}s)"
        else:
            return "MONITORING"

    def _launch_tracking(self) -> bool:
        """Launch tracking program as a background process (non-blocking)."""
        if self._tracking_running:
            return True  # Already running

        tracking_path = self.config.tracking_exe

        # Parse the executable path from the command string
        actual_exe, full_cmd = parse_command_string(tracking_path)

        # Check if user accidentally provided a direct media file
        if os.path.exists(actual_exe) and actual_exe.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.wmv')):
            print(f"[ERROR] Cannot execute a video file directly: {actual_exe}")
            print(f"[HINT] Update config.json to use an executable player (e.g., 'vlc.exe {tracking_path}')")
            return False

        if not os.path.exists(actual_exe):
            print(f"[ERROR] Tracking EXE not found: {actual_exe}")
            return False

        try:
            print(f"[INFO] Launching tracking program...")

            # Launch as background process
            self._tracking_process = subprocess.Popen(
                full_cmd,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            self._tracking_running = True
            print(f"[INFO] Tracking launched (PID: {self._tracking_process.pid})")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to launch tracking: {e}")
            return False

    def _close_tracking(self) -> bool:
        """Close the tracking program if running."""
        if not self._tracking_running or self._tracking_process is None:
            return True  # Not running

        try:
            print("[INFO] Closing tracking program (face lost)...")

            # Try graceful termination first
            self._tracking_process.terminate()

            try:
                self._tracking_process.wait(timeout=3)
                print("[INFO] Tracking closed gracefully")
            except subprocess.TimeoutExpired:
                # Force kill if needed
                self._tracking_process.kill()
                self._tracking_process.wait(timeout=2)
                print("[INFO] Tracking killed (force)")

            self._tracking_process = None
            self._tracking_running = False
            self.mode_decider.reset_tracking()
            self.audio.play_tracking_close()
            return True
        except Exception as e:
            print(f"[WARN] Error closing tracking: {e}")
            self._tracking_process = None
            self._tracking_running = False
            return False

    def _is_tracking_still_running(self) -> bool:
        """Check if tracking process is still alive."""
        if self._tracking_process is None:
            return False
        return self._tracking_process.poll() is None

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

        # Open detection UI (also opens detection camera)
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

                # Check if tracking process died unexpectedly
                if self._tracking_running and not self._is_tracking_still_running():
                    print("[INFO] Tracking process ended unexpectedly")
                    self._tracking_process = None
                    self._tracking_running = False
                    self.mode_decider.reset_tracking()

                # Read frame and detect faces
                frame = self.detection_ui.read_frame()
                if frame is None:
                    continue

                face_found, face_rects = self.face_detector.detect(frame)

                # Audio feedback: face detected for first time
                if face_found and not self._last_face_state:
                    self.audio.play_detection_start()

                result = self.mode_decider.update(face_found)
                self._last_face_state = face_found

                # Update UI (with extended info for tracking state)
                config_info = {
                    'threshold': self.config.detection_threshold_seconds,
                    'confidence': self.config.face_detection_confidence,
                    'face_loss_grace_period': self.config.face_loss_grace_period
                }
                status = self._get_detection_status()

                if not self.detection_ui.update(config_info, status, face_rects):
                    print("[INFO] UI closed by user")
                    break

                # Screen-saver logic:
                # - Face detected + threshold met -> Launch tracking (idle stays running)
                # - Face lost + grace period exceeded -> Close tracking (idle visible again)

                if result == "tracking" and not self._tracking_running:
                    # Face detected, launch tracking
                    self.audio.play_tracking_launch()
                    self._launch_tracking()

                if result == "idle" and self._tracking_running:
                    # Face lost for grace period, close tracking
                    self._close_tracking()

                time.sleep(0.05)  # ~20 FPS

        except KeyboardInterrupt:
            print("\n[INFO] Shutting down...")
        except Exception as e:
            print(f"[ERROR] {e}")
        finally:
            self._cleanup()

    def _cleanup(self):
        """Clean up processes on shutdown."""
        print("[INFO] Cleaning up...")
        # Close tracking if running
        if self._tracking_running:
            self._close_tracking()
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
