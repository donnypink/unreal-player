"""Face detection using OpenCV Haar Cascade."""
import cv2
import time
import numpy as np
from typing import List, Tuple, Optional, Callable


class FaceDetector:
    """Detects faces in video frames using Haar Cascade classifier."""
    
    def __init__(self, min_confidence: float = 0.5):
        self.min_confidence = min_confidence
        # Load Haar Cascade for face detection
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self._face_cascade = cv2.CascadeClassifier(cascade_path)
        self._boundary_check = None  # Callback to check if face is in boundary
    
    def set_boundary_check(self, check_callback: Callable):
        """Set callback function to check if face is within detection boundary."""
        self._boundary_check = check_callback
    
    def detect(self, frame: np.ndarray) -> Tuple[bool, List[Tuple[int, int, int, int]]]:
        """
        Detect faces in a frame.
        Returns: (face_found, list_of_face_rectangles)
        """
        if frame is None:
            return False, []
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self._face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        face_rects = []
        valid_face_found = False
        
        for (x, y, w, h) in faces:
            face_rects.append((x, y, w, h))
            
            # Check if face is within detection boundary
            if self._boundary_check:
                if self._boundary_check((x, y, w, h)):
                    valid_face_found = True
            else:
                # No boundary check, accept all faces
                valid_face_found = True
        
        return valid_face_found, face_rects
    
    def detect_continuous(self, cap, duration_seconds: float = 1.0, 
                         check_interval: float = 0.1) -> Tuple[bool, List[Tuple[int, int, int, int]]]:
        """
        Continuously check for faces over a duration.
        Returns True only if a valid face is detected within boundary.
        """
        end_time = time.time() + duration_seconds
        all_face_rects = []
        
        while time.time() < end_time:
            ret, frame = cap.read()
            if not ret:
                break
            
            face_found, face_rects = self.detect(frame)
            all_face_rects = face_rects  # Keep latest
            
            if face_found:
                return True, all_face_rects
            
            time.sleep(check_interval)
        
        return False, all_face_rects
