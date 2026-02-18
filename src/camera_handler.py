"""Camera handling and face detection."""
import time
import cv2
from face_detector import FaceDetector


class CameraHandler:
    """Manages camera access and face detection."""
    
    def __init__(self, camera_index: int, face_detector: FaceDetector):
        self.camera_index = camera_index
        self.face_detector = face_detector
        self._cap = None
    
    def open(self) -> bool:
        """Open the camera for continuous use."""
        try:
            print("[INFO] Opening camera...")
            self._cap = cv2.VideoCapture(self.camera_index)
            
            if not self._cap.isOpened():
                print("[ERROR] Cannot open camera")
                return False
            
            time.sleep(0.5)  # Camera initialization
            print("[INFO] Camera opened successfully")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to open camera: {e}")
            return False
    
    def release(self):
        """Release the camera."""
        if self._cap:
            self._cap.release()
            self._cap = None
            print("[INFO] Camera released")
    
    def is_opened(self) -> bool:
        """Check if camera is currently open."""
        return self._cap is not None and self._cap.isOpened()
    
    def check_face(self, check_duration: float = 1.0) -> bool:
        """Check for faces using already opened camera."""
        if not self.is_opened():
            print("[ERROR] Camera not open")
            return False
        
        try:
            print("[INFO] Checking for faces...")
            face_found = self.face_detector.detect_continuous(self._cap, check_duration)
            print(f"[RESULT] Face detected: {face_found}")
            return face_found
            
        except Exception as e:
            print(f"[ERROR] Face detection failed: {e}")
            return False
