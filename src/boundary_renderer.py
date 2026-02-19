"""UI rendering for detection boundary and overlays."""
import cv2
import numpy as np
from typing import Tuple, Optional, List


class BoundaryRenderer:
    """Renders detection boundary, faces, and config overlays on frames."""
    
    def __init__(self, frame_width: int, frame_height: int):
        self.frame_width = frame_width
        self.frame_height = frame_height
        self._default_ratio = 0.6
        self._boundary: Optional[Tuple[int, int, int, int]] = None
        self._show_boundary = True
        self._dragging = False
        self._set_default_boundary()
    
    def _set_default_boundary(self):
        """Set boundary to center of frame."""
        w = int(self.frame_width * self._default_ratio)
        h = int(self.frame_height * self._default_ratio)
        x = (self.frame_width - w) // 2
        y = (self.frame_height - h) // 2
        self._boundary = (x, y, w, h)
        print(f"[INFO] Default boundary set: ({x}, {y}, {w}, {h})")
    
    def set_boundary(self, x: int, y: int, w: int, h: int):
        """Set custom boundary."""
        self._boundary = (x, y, w, h)
    
    def reset_boundary(self):
        """Reset to default boundary."""
        self._set_default_boundary()
    
    def toggle_visibility(self):
        """Toggle boundary visibility."""
        self._show_boundary = not self._show_boundary
    
    def set_dragging(self, dragging: bool):
        """Set dragging state for visual feedback."""
        self._dragging = dragging
    
    def get_boundary(self) -> Optional[Tuple[int, int, int, int]]:
        """Get current boundary (x, y, width, height)."""
        return self._boundary
    
    def is_face_in_boundary(self, face_rect: Tuple[int, int, int, int]) -> bool:
        """Check if face center is within boundary."""
        if self._boundary is None:
            return True
        
        fx, fy, fw, fh = face_rect
        bx, by, bw, bh = self._boundary
        
        face_cx = fx + fw // 2
        face_cy = fy + fh // 2
        
        return (bx <= face_cx <= bx + bw and by <= face_cy <= by + bh)
    
    def render(self, frame: np.ndarray, face_rects: List[Tuple[int, int, int, int]],
               config_info: dict, status: str) -> np.ndarray:
        """Render all UI elements on frame."""
        # Draw boundary box
        if self._show_boundary and self._boundary:
            x, y, w, h = self._boundary
            color = (0, 255, 0) if not self._dragging else (0, 255, 255)
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(frame, "Detection Zone", (x, y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # Draw detected faces
        for rect in face_rects:
            x, y, w, h = rect
            in_boundary = self.is_face_in_boundary(rect)
            color = (0, 255, 0) if in_boundary else (0, 0, 255)
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        
        # Draw config overlay
        self._draw_overlay(frame, config_info, status)
        
        return frame
    
    def _draw_overlay(self, frame: np.ndarray, config_info: dict, status: str):
        """Draw config info and status overlay."""
        overlay_y = 30
        cv2.putText(frame, f"Threshold: {config_info.get('threshold', 3.0)}s",
                   (10, overlay_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        overlay_y += 25
        cv2.putText(frame, f"Confidence: {config_info.get('confidence', 0.5)}",
                   (10, overlay_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        overlay_y += 25
        cv2.putText(frame, f"Status: {status}",
                   (10, overlay_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        # Draw instructions
        overlay_y = self.frame_height - 60
        cv2.putText(frame, "Drag: Resize zone | Right-click: Reset | Middle: Toggle",
                   (10, overlay_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        overlay_y += 20
        cv2.putText(frame, "Press 'q' to quit",
                   (10, overlay_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
