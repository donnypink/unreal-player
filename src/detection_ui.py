"""Simplified Detection UI - delegates to specialized classes."""
import cv2
import numpy as np
from typing import Callable, List

from camera_manager import CameraManager
from boundary_renderer import BoundaryRenderer


class DetectionUI:
    """UI window showing camera feed with detection boundary and config overlay.
    
    Delegates camera handling to CameraManager and rendering to BoundaryRenderer.
    """
    
    def __init__(self, window_name: str = "Face Detection", camera_index: int = 0):
        self.window_name = window_name
        self.camera = CameraManager(camera_index)
        self.renderer: BoundaryRenderer = None
        self._drag_start = None
        self._drag_callback: Callable = None
        
        # Create window
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(self.window_name, self._mouse_callback)
    
    def _mouse_callback(self, event, x, y, flags, param):
        """Handle mouse events for boundary adjustment."""
        if not self.renderer:
            return
        
        if event == cv2.EVENT_LBUTTONDOWN:
            self._drag_start = (x, y)
            self.renderer.set_dragging(True)
        elif event == cv2.EVENT_MOUSEMOVE and self._drag_start:
            x1, y1 = self._drag_start
            # Update boundary while dragging
            new_x = min(x1, x)
            new_y = min(y1, y)
            new_w = abs(x - x1)
            new_h = abs(y - y1)
            if new_w > 50 and new_h > 50:
                self.renderer.set_boundary(new_x, new_y, new_w, new_h)
                if self._drag_callback:
                    self._drag_callback()
        elif event == cv2.EVENT_LBUTTONUP:
            self._drag_start = None
            self.renderer.set_dragging(False)
        elif event == cv2.EVENT_RBUTTONDOWN:
            self.renderer.reset_boundary()
        elif event == cv2.EVENT_MBUTTONDOWN:
            self.renderer.toggle_visibility()
    
    def open(self) -> bool:
        """Open camera and initialize UI."""
        if not self.camera.open():
            return False
        
        # Initialize renderer with frame dimensions
        width, height = self.camera.get_frame_size()
        self.renderer = BoundaryRenderer(width, height)
        return True
    
    def release(self):
        """Release camera and close UI."""
        self.camera.release()
        cv2.destroyWindow(self.window_name)
    
    def is_opened(self) -> bool:
        """Check if camera and UI are active."""
        return self.camera.is_opened() and self.renderer is not None
    
    def get_boundary(self):
        """Get current detection boundary."""
        return self.renderer.get_boundary() if self.renderer else None
    
    def is_face_in_boundary(self, face_rect) -> bool:
        """Check if face is within detection boundary."""
        if not self.renderer:
            return True
        result = self.renderer.is_face_in_boundary(face_rect)
        # Debug output
        fx, fy, fw, fh = face_rect
        bx, by, bw, bh = self.renderer.get_boundary() or (0, 0, 0, 0)
        face_cx, face_cy = fx + fw // 2, fy + fh // 2
        # print(f"[DEBUG] Face at ({fx},{fy},{fw},{fh}), center=({face_cx},{face_cy}), "
            #   f"boundary=({bx},{by},{bw},{bh}), in_boundary={result}")
        return result
    
    def set_drag_callback(self, callback: Callable):
        """Set callback for boundary drag updates."""
        self._drag_callback = callback
    
    def read_frame(self):
        """Read a frame from camera."""
        return self.camera.read_frame()
    
    def update(self, config_info: dict, detection_status: str,
               face_rects: List = None) -> bool:
        """Update UI with new frame and info. Returns False if window closed."""
        if not self.is_opened():
            return False
        
        frame = self.camera.read_frame()
        if frame is None:
            return False
        
        # Render UI elements
        frame = self.renderer.render(frame, face_rects or [], config_info, detection_status)
        
        # Show frame
        cv2.imshow(self.window_name, frame)
        
        # Check for key press
        key = cv2.waitKey(1) & 0xFF
        return key != ord('q')
