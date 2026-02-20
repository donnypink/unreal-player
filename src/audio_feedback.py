"""Audio feedback for detection events."""
import threading
from typing import Optional
from pathlib import Path


class AudioFeedback:
    """Handles audio feedback for face detection events."""
    
    def __init__(self, enabled: bool = True, sound_dir: str = "sounds"):
        self.enabled = enabled
        self.sound_dir = Path(sound_dir)
        self._audio_available = False
        self._audio_thread: Optional[threading.Thread] = None
        
        # Try to import pygame
        try:
            import pygame
            self._pygame = pygame
            self._audio_available = True
            pygame.mixer.init()
            print("[INFO] Audio feedback initialized")
        except ImportError:
            print("[WARN] pygame not available, audio feedback disabled")
        except Exception as e:
            print(f"[WARN] Audio init failed: {e}")
    
    def _play_sound(self, sound_file: str):
        """Play sound in a separate thread."""
        if not self.enabled or not self._audio_available:
            return
        
        sound_path = self.sound_dir / sound_file
        if not sound_path.exists():
            # Try to generate beep as fallback
            self._beep_fallback()
            return
        
        try:
            self._pygame.mixer.music.load(str(sound_path))
            self._pygame.mixer.music.play()
        except Exception as e:
            print(f"[WARN] Failed to play sound: {e}")
    
    def _beep_fallback(self):
        """Fallback to system beep if pygame fails."""
        try:
            import winsound
            winsound.MessageBeep()
        except:
            print("\a")  # Terminal bell
    
    def play_detection_start(self):
        """Play sound when face detection starts (face first seen)."""
        if not self.enabled:
            return
        self._audio_thread = threading.Thread(
            target=self._play_sound,
            args=("detection_start.wav",),
            daemon=True
        )
        self._audio_thread.start()
    
    def play_tracking_launch(self):
        """Play sound when tracking program is about to launch."""
        if not self.enabled:
            return
        self._audio_thread = threading.Thread(
            target=self._play_sound,
            args=("tracking_launch.wav",),
            daemon=True
        )
        self._audio_thread.start()
    
    def play_tracking_close(self):
        """Play sound when tracking program closes."""
        if not self.enabled:
            return
        self._audio_thread = threading.Thread(
            target=self._play_sound,
            args=("tracking_close.wav",),
            daemon=True
        )
        self._audio_thread.start()
    
    def play_error(self):
        """Play sound on error."""
        if not self.enabled:
            return
        self._audio_thread = threading.Thread(
            target=self._play_sound,
            args=("error.wav",),
            daemon=True
        )
        self._audio_thread.start()
    
    def enable(self):
        """Enable audio feedback."""
        self.enabled = True
        print("[INFO] Audio feedback enabled")
    
    def disable(self):
        """Disable audio feedback."""
        self.enabled = False
        print("[INFO] Audio feedback disabled")
    
    def toggle(self) -> bool:
        """Toggle audio feedback on/off. Returns new state."""
        self.enabled = not self.enabled
        print(f"[INFO] Audio feedback {'enabled' if self.enabled else 'disabled'}")
        return self.enabled
