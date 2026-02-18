"""Configuration management for UE Controller."""
import json
from pathlib import Path


class Config:
    """Handles loading and accessing configuration."""
    
    DEFAULTS = {
        "camera_index": 0,
        "face_detection_confidence": 0.5,
        "detection_threshold_seconds": 3.0
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
