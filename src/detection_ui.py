"""Detection UI with adjustable boundary box for face detection."""
import cv2
import time
from typing import Tuple, Optional, Callable


class DetectionUI:
    """UI window showing camera feed with detection boundary and config overlay."""
    
    def __init__(self, window_name: str = "Face Detection"):
        self.window_name = window_name
        self._cap = None
        self._boundary = None  # (x, y, width, height)
        self._dragging = False
        self._drag_start = None
        self._frame_width = 0
        self._frame_height = 0
        self._show_boundary = True
        self._callback = None
        
        # Create window
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(self.window_name, self._mouse_callback)
        
        # Default boundary (center 60% of frame)
        self._default_boundary_ratio = 0.6
    
    def _mouse_callback(self, event, x, y, flags, param):
        """Handle mouse events for boundary adjustment."""
        if event == cv2.EVENT_LBUTTONDOWN:
            # Start dragging
            self._dragging = True
            self._drag_start = (x, y)
        elif event == cv2.EVENT_MOUSEMOVE and self._dragging:
            # Update boundary while dragging
            if self._drag_start:
                x1, y1 = self._drag_start
                x2, y2 = x, y
                # Ensure positive dimensions
                x = min(x1, x2)
                y = min(y1, y2)
                w = abs(x2 - x1)
                h = abs(y2 - y1)
                if w > 50 and h > 50:  # Minimum size
                    self._boundary = (x, y, w, h)
        elif event == cv2.EVENT_LBUTTONUP:
            # Stop dragging
            self._dragging = False
            self._drag_start = None
        elif event == cv2.EVENT_RBUTTONDOWN:
            # Reset to default boundary on right click
            self._set_default_boundary()
        elif event == cv2.EVENT_MBUTTONDOWN:
            # Toggle boundary visibility on middle click
            self._show_boundary = not self._show_boundary
    
    def _set_default_boundary(self):
        """Set boundary to center of frame."""
        if self._frame_width > 0 and self._frame_height > 0:
            ratio = self._default_boundary_ratio
            w = int(self._frame_width * ratio)
            h = int(self._frame_height * ratio)
            x = (self._frame_width - w) // 2
            y = (self._frame_height - h) // 2
            self._boundary = (x, y, w, h)
            print(f"[INFO] Default boundary set: ({x}, {y}, {w}, {h})")
    
    def open(self, camera_index: int) -> bool:
        """Open camera and initialize UI."""
        self._cap = cv2.VideoCapture(camera_index)
        if not self._cap.isOpened():
            return False
        
        # Get frame dimensions
        ret, frame = self._cap.read()
        if ret:
            self._frame_height, self._frame_width = frame.shape[:2]
            self._set_default_boundary()
            print(f"[INFO] Camera opened: {self._frame_width}x{self._frame_height}")
        
        return True
    
    def release(self):
        """Release camera and close UI."""
        if self._cap:
            self._cap.release()
            self._cap = None
        cv2.destroyWindow(self.window_name)
    
    def is_opened(self) -> bool:
        """Check if camera and UI are active."""
        return self._cap is not None and self._cap.isOpened()
    
    def get_boundary(self) -> Optional[Tuple[int, int, int, int]]:
        """Get current detection boundary (x, y, width, height)."""
        return self._boundary
    
    def is_face_in_boundary(self, face_rect: Tuple[int, int, int, int]) -> bool:
        """Check if face rectangle is within detection boundary."""
        if self._boundary is None:
            return True  # No boundary set, accept all
        
        fx, fy, fw, fh = face_rect
        bx, by, bw, bh = self._boundary
        
        # Check if face center is within boundary
        face_cx = fx + fw // 2
        face_cy = fy + fh // 2
        
        # Check if face center is inside boundary box
        in_boundary = (bx <= face_cx <= bx + bw and 
                      by <= face_cy <= by + bh)
        
        # Debug output
        print(f"[DEBUG] Face at ({fx},{fy},{fw},{fh}), center=({face_cx},{face_cy}), "
              f"boundary=({bx},{by},{bw},{bh}), in_boundary={in_boundary}")
        
        return in_boundary
    
    def update(self, config_info: dict, detection_status: str, 
               face_rects: list = None, callback: Callable = None) -> bool:
        """Update UI with new frame and info. Returns False if window closed."""
        if not self.is_opened():
            return False
        
        ret, frame = self._cap.read()
        if not ret:
            return False
        
        # Draw boundary box
        if self._show_boundary and self._boundary:
            x, y, w, h = self._boundary
            color = (0, 255, 0) if not self._dragging else (0, 255, 255)
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(frame, "Detection Zone", (x, y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # Draw detected faces
        if face_rects:
            for rect in face_rects:
                x, y, w, h = rect
                # Green if in boundary, red if outside
                in_boundary = self.is_face_in_boundary(rect)
                color = (0, 255, 0) if in_boundary else (0, 0, 255)
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        
        # Draw config overlay
        overlay_y = 30
        cv2.putText(frame, f"Threshold: {config_info.get('threshold', 3.0)}s", 
                   (10, overlay_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        overlay_y += 25
        cv2.putText(frame, f"Confidence: {config_info.get('confidence', 0.5)}", 
                   (10, overlay_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        overlay_y += 25
        cv2.putText(frame, f"Status: {detection_status}", 
                   (10, overlay_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        # Draw instructions
        overlay_y = self._frame_height - 60
        cv2.putText(frame, "Drag: Resize zone | Right-click: Reset | Middle: Toggle", 
                   (10, overlay_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        overlay_y += 20
        cv2.putText(frame, "Press 'q' to quit", 
                   (10, overlay_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        # Show frame
        cv2.imshow(self.window_name, frame)
        
        # Check for key press
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            return False
        
        return True
    
    def read_frame(self):
        """Read a frame from camera."""
        if self.is_opened():
            ret, frame = self._cap.read()
            if ret:
                return frame
        return None
