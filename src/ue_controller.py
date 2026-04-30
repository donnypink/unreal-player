"""
UE Controller - Face Detection Program
Screen-saver style switching:
- Both Tracking and Idle apps are launched at startup and run continuously.
- Detection camera shows UI with boundary zone.
- Face detected -> Tracking window focused, Idle minimized.
- Face lost for grace period -> Idle window focused, Tracking minimized.
"""
import time
import sys
import os
import subprocess
from typing import Optional

from config import Config
from face_detector import FaceDetector
from mode_decider import ModeDecider
from program_runner import ProgramRunner
from detection_ui import DetectionUI
from window_manager import WindowManager
from process_manager import ProcessManager
from audio_feedback import AudioFeedback


class UEController:
    """Controls window switching between Tracking and Idle based on face detection."""

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
        
        self._tracking_process: Optional[subprocess.Popen] = None
        self._tracking_running = False
        self._idle_pid: Optional[int] = None
        self._last_face_state = False
        self._current_mode = "unknown"

    def _print_banner(self):
        """Print startup banner."""
        print("=" * 50)
        print("UE Controller - Face Detection Program")
        print("=" * 50)
        print(f"Tracking EXE: {self.config.tracking_exe}")
        print(f"Idle EXE: {self.config.idle_exe}")
        print(f"Face detection threshold: {self.config.detection_threshold_seconds}s")
        print("=" * 50)
        print("\nFlow: BOTH programs run continuously")
        print("      ↓ face detected IN zone")
        print("      TRACKING focused (foreground) / IDLE minimized")
        print("      ↓ face lost for grace period")
        print("      IDLE focused (foreground) / TRACKING minimized\n")

    def _get_detection_status(self) -> str:
        if self._current_mode == "tracking":
            if self.mode_decider.time_since_face_lost > 0:
                remaining = self.config.face_loss_grace_period - self.mode_decider.time_since_face_lost
                if remaining > 0:
                    return f"TRACKING (face lost: {remaining:.1f}s to swap)"
            return "TRACKING IN FOREGROUND"
        elif self.mode_decider.is_face_present:
            return f"FACE DETECTED ({self.mode_decider.face_duration:.1f}s)"
        else:
            return "IDLE IN FOREGROUND"

    def _switch_to_tracking(self):
        """Bring tracking window to foreground, hide idle."""
        print("[INFO] Switching focus to TRACKING...")
        self.window_manager.minimize_by_title(self.config.idle_title)
        
        focused = False
        delay = self.config.switch_delay_seconds
        for _ in range(3):
            if self.window_manager.focus_by_title(self.config.tracking_title, exclude_substring=self.config.idle_title, delay=delay):
                focused = True
                print("[INFO] Tracking window successfully focused.")
                break
            time.sleep(0.1)
            
        if not focused:
            print("[WARN] Tracking window failed to focus.")

    def _switch_to_idle(self):
        """Bring idle window to foreground, hide tracking."""
        print("[INFO] Switching focus to IDLE...")
        self.window_manager.minimize_by_title(self.config.tracking_title, exclude_substring=self.config.idle_title)
        
        focused = False
        delay = self.config.switch_delay_seconds
        for _ in range(3):
            if self.window_manager.focus_by_title(self.config.idle_title, delay=delay):
                focused = True
                print("[INFO] Idle window successfully focused.")
                break
            time.sleep(0.1)
            
        if not focused:
            print("[WARN] Idle window failed to focus.")

    def _is_tracking_still_running(self) -> bool:
        """Check if tracking process is still alive."""
        if self._tracking_process is None:
            return False
        return self._tracking_process.poll() is None

    def _setup_face_detection(self):
        self.face_detector.set_boundary_check(
            lambda rect: self.detection_ui.is_face_in_boundary(rect)
        )

    def run(self):
        """Main loop with detection UI."""
        self._print_banner()

        # 1. Start Idle Program
        if not self.idle_manager.start():
            print("[ERROR] Failed to start idle program. Exiting.")
            return
        self._idle_pid = self.idle_manager.get_pid()

        # 2. Start Tracking Program
        print("[INFO] Launching tracking program initially...")
        self._tracking_process = self.window_manager.launch_nonblocking(self.config.tracking_exe)
        if self._tracking_process:
            self._tracking_running = True
        else:
            print("[ERROR] Tracking process failed to start.")

        # 3. Wait for applications to render windows
        wait_time = self.config.initial_wait_seconds
        print(f"[INFO] Waiting {wait_time} seconds for application windows to render fully...")
        time.sleep(wait_time)

        # 4. Open detection UI
        if not self.detection_ui.open():
            print("[ERROR] Failed to open camera/UI. Exiting.")
            self._cleanup()
            return
        self._setup_face_detection()
        self.detection_ui.set_drag_callback(self._setup_face_detection)

        # 5. Set Initial State -> Idle Foreground
        self._switch_to_idle()
        self._current_mode = "idle"

        try:
            while True:
                # Process health checks
                self.idle_manager.ensure_running()

                if self._tracking_running and not self._is_tracking_still_running():
                    print("[WARN] Tracking process ended unexpectedly. Restarting...")
                    self._tracking_process = self.window_manager.launch_nonblocking(self.config.tracking_exe)
                    
                    # Wait for it to restart, reusing our configured wait time
                    time.sleep(self.config.initial_wait_seconds) 
                    
                    # Re-apply window state based on current mode
                    if self._current_mode == "tracking":
                        self._switch_to_tracking()
                    else:
                        self.window_manager.minimize_by_title(self.config.tracking_title)

                frame = self.detection_ui.read_frame()
                if frame is None:
                    continue

                face_found, face_rects = self.face_detector.detect(frame)

                if face_found and not self._last_face_state:
                    self.audio.play_detection_start()

                result = self.mode_decider.update(face_found)
                self._last_face_state = face_found

                # UI Updates
                config_info = {
                    'threshold': self.config.detection_threshold_seconds,
                    'confidence': self.config.face_detection_confidence,
                    'face_loss_grace_period': self.config.face_loss_grace_period
                }
                status = self._get_detection_status()
                if not self.detection_ui.update(config_info, status, face_rects):
                    print("[INFO] UI closed by user")
                    break

                # State Switching Logic
                if result == "tracking" and self._current_mode != "tracking":
                    self.audio.play_tracking_launch()
                    self._switch_to_tracking()
                    self._current_mode = "tracking"

                elif result == "idle" and self._current_mode != "idle":
                    self._switch_to_idle()
                    self._current_mode = "idle"

                time.sleep(0.05)

        except KeyboardInterrupt:
            print("\n[INFO] Shutting down...")
        except Exception as e:
            print(f"[ERROR] {e}")
        finally:
            self._cleanup()

    def _cleanup(self):
        print("[INFO] Cleaning up processes...")
        if self._tracking_running and self._tracking_process:
            try:
                self._tracking_process.terminate()
                try:
                    self._tracking_process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self._tracking_process.kill()
            except Exception as e:
                print(f"[WARN] Error terminating tracking: {e}")
        self.detection_ui.release()
        self.idle_manager.stop()


if __name__ == "__main__":
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.json"
    try:
        controller = UEController(config_path)
        controller.run()
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)