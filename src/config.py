"""Configuration management for UE Controller."""
import json
from pathlib import Path


class Config:
    """Handles loading and accessing configuration."""
    
    DEFAULTS = {
        "camera_index": 0,
        "detection_camera_index": 0,
        "tracking_camera_index": 1,
        "face_detection_confidence": 0.5,
        "detection_threshold_seconds": 3.0,
        "face_loss_grace_period": 2.0,
        "audio_enabled": True,
        "sound_dir": "sounds"
    }
    
    def __init__(self, config_path: str = "config.json"):
        self._data = self._load(config_path)
    
    def _load(self, path: str) -> dict:
        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def get(self, key: str, default=None):
        return self._data.get(key, self.DEFAULTS.get(key, default))
    
    @property
    def tracking_exe(self) -> str:
        return self._data["tracking_exe"]
    
    @property
    def idle_exe(self) -> str:
        return self._data["idle_exe"]
    
    @property
    def camera_index(self) -> int:
        return self.get("camera_index")
    
    @property
    def face_detection_confidence(self) -> float:
        return self.get("face_detection_confidence")
    
    @property
    def detection_threshold_seconds(self) -> float:
        return self.get("detection_threshold_seconds")
    
    @property
    def audio_enabled(self) -> bool:
        return self.get("audio_enabled")
    
    @property
    def sound_dir(self) -> str:
        return self.get("sound_dir")

    @property
    def detection_camera_index(self) -> int:
        return self.get("detection_camera_index")

    @property
    def tracking_camera_index(self) -> int:
        return self.get("tracking_camera_index")

    @property
    def face_loss_grace_period(self) -> float:
        return self.get("face_loss_grace_period")
