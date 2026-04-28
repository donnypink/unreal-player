"""
UE Controller - Face Detection Program
Screen-saver style switching:
- Idle program (VLC) runs continuously in background
- Detection camera shows UI with boundary zone
- Face detected -> Tracking launches, window switches to tracking (idle hidden)
- Face lost for grace period -> Tracking closes, window switches back to idle
- Press 'q' in detection UI to quit
"""
import time
import sys
import os
import subprocess
import signal
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
    """Controls launching tracking program based on face detection with UI.

    Screen-saver mode: Idle runs continuously. Tracking is launched/closed
    dynamically based on face presence. Window switching brings tracking/idle
    to foreground. Detection UI stays visible throughout.
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
        self._tracking_process: Optional[subprocess.Popen] = None
        self._tracking_running = False
        self._tracking_minimized = False  # Track if tracking window is minimized
        self._idle_pid: Optional[int] = None
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
        print("\nFlow: IDLE runs continuously (fullscreen)")
        print("      UI shows camera feed with detection zone")
        print("      ↓ face detected IN zone")
        print("      TRACKING fullscreen (foreground)")
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

    def _switch_to_tracking(self) -> bool:
        """Launch tracking and bring its window to foreground, hide idle.
        
        If tracking is already running (but minimized), just restore its window.
        """
        # If tracking is already running (but possibly minimized), just restore window
        if self._tracking_running and self._is_tracking_still_running():
            tracking_hwnd = self.window_manager.find_window(self._tracking_process.pid)
            if tracking_hwnd:
                self.window_manager.maximize(tracking_hwnd)
                self.window_manager.bring_to_foreground(tracking_hwnd)
                print("[INFO] Tracking window restored to foreground")
                return True
            else:
                print("[WARN] Could not find tracking window, will relaunch")
                # Fall through to launch new instance

        tracking_path = self.config.tracking_exe

        # Check if user accidentally provided a direct media file
        from process_manager import parse_command_string
        actual_exe, _ = parse_command_string(tracking_path)
        
        if os.path.exists(actual_exe) and actual_exe.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.wmv')):
            print(f"[ERROR] Cannot execute a video file directly: {actual_exe}")
            print(f"[HINT] Update config.json to use an executable player (e.g., 'vlc.exe {tracking_path}')")
            return False

        if not os.path.exists(actual_exe):
            print(f"[ERROR] Tracking EXE not found: {actual_exe}")
            return False

        try:
            print(f"[INFO] Launching tracking program...")
            
            # Launch as non-blocking process
            self._tracking_process = self.window_manager.launch_nonblocking(tracking_path)
            if self._tracking_process is None:
                return False
            
            self._tracking_running = True
            print(f"[INFO] Tracking launched (PID: {self._tracking_process.pid})")
            
            # Wait for window to appear and bring to foreground
            time.sleep(1.5)
            
            # Minimize idle to put it in background
            if self._idle_pid:
                idle_hwnd = self.window_manager.find_window(self._idle_pid)
                if idle_hwnd:
                    self.window_manager.minimize(idle_hwnd)
                    print("[INFO] Idle window minimized")
                else:
                    print("[WARN] Could not find idle window to minimize")
            
            # Bring tracking to foreground
            tracking_hwnd = self.window_manager.find_window(self._tracking_process.pid)
            if tracking_hwnd:
                self.window_manager.maximize(tracking_hwnd)
                self.window_manager.bring_to_foreground(tracking_hwnd)
                print("[INFO] Tracking window brought to foreground")
            else:
                print("[WARN] Could not find tracking window, ensuring idle is visible")
                # Ensure idle is back in foreground if tracking fails to create window
                self._restore_idle()
            
            return True
        except Exception as e:
            print(f"[ERROR] Failed to launch tracking: {e}")
            # Ensure idle is visible on failure
            self._restore_idle()
            return False
    
    def _restore_idle(self):
        """Restore idle window to foreground (VLC protection)."""
        if self._idle_pid:
            idle_hwnd = self.window_manager.find_window(self._idle_pid)
            if idle_hwnd:
                self.window_manager.maximize(idle_hwnd)
                self.window_manager.bring_to_foreground(idle_hwnd)
                print("[INFO] Idle window restored (fallback)")

    def _switch_to_idle(self) -> bool:
        """Minimize tracking and bring idle window back to foreground.
        
        Tracking process is kept running (just minimized) so it can be
        restored quickly when face is detected again.
        """
        if not self._tracking_running or self._tracking_process is None:
            return True  # Not running
        
        # Check if tracking is still running - if not, clean up
        if not self._is_tracking_still_running():
            print("[INFO] Tracking process died, cleaning up")
            self._tracking_process = None
            self._tracking_running = False
            self.mode_decider.reset_tracking()
            # Still restore idle
            if self._idle_pid:
                idle_hwnd = self.window_manager.find_window(self._idle_pid)
                if idle_hwnd:
                    self.window_manager.maximize(idle_hwnd)
                    self.window_manager.bring_to_foreground(idle_hwnd)
            return True
        
        # Minimize tracking window (keep process running)
        tracking_hwnd = self.window_manager.find_window(self._tracking_process.pid)
        if tracking_hwnd:
            self.window_manager.minimize(tracking_hwnd)
            print("[INFO] Tracking window minimized (process kept running)")
        
        # Bring idle to foreground
        if self._idle_pid:
            idle_hwnd = self.window_manager.find_window(self._idle_pid)
            if idle_hwnd:
                self.window_manager.maximize(idle_hwnd)
                self.window_manager.bring_to_foreground(idle_hwnd)
                print("[INFO] Idle window brought to foreground")
        
        # Keep _tracking_running = True and process running - just minimize window
        # Mode decider will handle the state
        self.mode_decider.reset_tracking()
        return True

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
        
        # Store idle PID for window management
        self._idle_pid = self.idle_manager.get_pid()

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
                    # Bring idle back
                    self._switch_to_idle()

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
                # - Face detected + threshold met -> Launch tracking, switch window
                # - Face lost + grace period exceeded -> Close tracking, switch back to idle

                if result == "tracking" and (not self._tracking_running or self._tracking_minimized):
                    # Face detected, launch tracking or restore minimized window
                    self.audio.play_tracking_launch()
                    self._switch_to_tracking()
                    self._tracking_minimized = False

                if result == "idle" and self._tracking_running and not self._tracking_minimized:
                    # Face lost for grace period, minimize tracking and switch back to idle
                    self._switch_to_idle()
                    self._tracking_minimized = True

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
        # Terminate tracking if running
        if self._tracking_running and self._tracking_process:
            try:
                print("[INFO] Terminating tracking program...")
                self._tracking_process.terminate()
                try:
                    self._tracking_process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self._tracking_process.kill()
                    self._tracking_process.wait(timeout=2)
            except Exception as e:
                print(f"[WARN] Error terminating tracking: {e}")
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
