"""Camera handling and face detection."""
import time
import cv2
from face_detector import FaceDetector


class CameraHandler:
    """Manages camera access and face detection."""
    
    def __init__(self, camera_index: int, face_detector: FaceDetector):
        self.camera_index = camera_index
        self.face_detector = face_detector
    
    def check_face(self, check_duration: float = 1.0) -> bool:
        """Open camera and check for faces."""
        cap = None
        try:
            print("[INFO] Opening camera to check for faces...")
            cap = cv2.VideoCapture(self.camera_index)
            
            if not cap.isOpened():
                print("[ERROR] Cannot open camera")
                return False
            
            time.sleep(0.5)  # Camera initialization
            face_found = self.face_detector.detect_continuous(cap, check_duration)
            print(f"[RESULT] Face detected: {face_found}")
            return face_found
            
        except Exception as e:
            print(f"[ERROR] Camera check failed: {e}")
            return False
        finally:
            if cap:
                cap.release()
                print("[INFO] Camera released")
