"""Face detection using OpenCV."""
import time
import cv2


class FaceDetector:
    """Detects faces from camera frames using Haar Cascade."""
    
    def __init__(self, min_confidence: float = 0.5):
        self.min_confidence = min_confidence
        self._face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
    
    def detect(self, frame) -> bool:
        """Detect faces in a single frame. Returns True if face found."""
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self._face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        return len(faces) > 0
    
    def detect_continuous(self, cap, duration_seconds: float, check_interval: float = 0.1) -> bool:
        """Detect faces continuously for a duration. Returns True if any face detected."""
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.05)
                continue
                
            if self.detect(frame):
                return True
                
            time.sleep(check_interval)
        
        return False
