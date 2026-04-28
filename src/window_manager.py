"""Window management for launching programs and controlling windows."""
import subprocess
import time
import os
import ctypes
from typing import Optional, Tuple
from ctypes import windll, wintypes

# Constants for window operations
SW_MINIMIZE = 6
SW_MAXIMIZE = 3
SW_RESTORE = 9
SW_SHOW = 5


class WindowManager:
    """Manages window operations for program launching and control."""
    
    def __init__(self):
        self.user32 = windll.user32
    
    def launch_nonblocking(self, cmd_string: str) -> Optional[subprocess.Popen]:
        """Launch a program as a non-blocking background process.
        
        Args:
            cmd_string: Command string with path and arguments
            
        Returns:
            subprocess.Popen object or None if failed
        """
        from process_manager import parse_command_string
        
        actual_exe, full_cmd = parse_command_string(cmd_string)
        
        # Check if user accidentally provided a direct media file
        if os.path.exists(actual_exe) and actual_exe.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.wmv')):
            print(f"[ERROR] Cannot execute a video file directly: {actual_exe}")
            return None
        
        if not os.path.exists(actual_exe):
            print(f"[ERROR] EXE not found: {actual_exe}")
            return None
        
        try:
            process = subprocess.Popen(
                full_cmd,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            print(f"[INFO] Launched non-blocking (PID: {process.pid})")
            return process
        except Exception as e:
            print(f"[ERROR] Failed to launch: {e}")
            return None
    
    def find_window(self, pid: int, max_retries: int = 3, retry_delay: float = 0.5) -> Optional[int]:
        """Find window handle by process ID with retry logic.
        
        Args:
            pid: Process ID to search for
            max_retries: Number of retry attempts
            retry_delay: Delay between retries in seconds
            
        Returns:
            Window handle (hwnd) or None if not found
        """
        for attempt in range(max_retries):
            hwnd = self._find_window_by_process(pid)
            if hwnd:
                return hwnd
            
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
        
        return None
    
    def _find_window_by_process(self, pid: int) -> Optional[int]:
        """Find window handle by process ID using EnumWindows."""
        result = []
        
        def callback(hwnd: wintypes.HWND, lParam: wintypes.LPARAM) -> wintypes.BOOL:
            """EnumWindows callback - must use proper ctypes signatures."""
            if self.user32.IsWindowVisible(hwnd):
                # Get process ID of the window
                process_id = wintypes.DWORD()
                self.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
                if process_id.value == pid:
                    result.append(hwnd)
                    return 0  # Stop enumeration (False)
            return 1  # Continue enumeration (True)
        
        try:
            EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
            cb = EnumWindowsProc(callback)
            self.user32.EnumWindows(cb, 0)
        except Exception as e:
            print(f"[WARN] EnumWindows failed: {e}")
        
        return result[0] if result else None
    
    def bring_to_foreground(self, hwnd: int) -> bool:
        """Bring a window to the foreground.
        
        Args:
            hwnd: Window handle
            
        Returns:
            True if successful
        """
        try:
            # Restore if minimized
            if self.user32.IsIconic(hwnd):
                self.user32.ShowWindow(hwnd, SW_RESTORE)
            
            self.user32.SetForegroundWindow(hwnd)
            return True
        except Exception as e:
            print(f"[WARN] Failed to bring to foreground: {e}")
            return False
    
    def maximize(self, hwnd: int) -> bool:
        """Maximize a window (fullscreen).
        
        Args:
            hwnd: Window handle
            
        Returns:
            True if successful
        """
        try:
            # Restore if minimized first
            if self.user32.IsIconic(hwnd):
                self.user32.ShowWindow(hwnd, SW_RESTORE)
            
            self.user32.ShowWindow(hwnd, SW_MAXIMIZE)
            return True
        except Exception as e:
            print(f"[WARN] Failed to maximize: {e}")
            return False
    
    def minimize(self, hwnd: int) -> bool:
        """Minimize a window.
        
        Args:
            hwnd: Window handle
            
        Returns:
            True if successful
        """
        try:
            self.user32.ShowWindow(hwnd, SW_MINIMIZE)
            return True
        except Exception as e:
            print(f"[WARN] Failed to minimize: {e}")
            return False
    
    def activate_fullscreen(self, pid: int, max_retries: int = 3) -> bool:
        """Launch program, find its window, and activate fullscreen.
        
        Args:
            pid: Process ID
            max_retries: Retry attempts for finding window
            
        Returns:
            True if successful
        """
        hwnd = self.find_window(pid, max_retries)
        if not hwnd:
            print(f"[WARN] Could not find window for PID {pid}")
            return False
        
        self.maximize(hwnd)
        self.bring_to_foreground(hwnd)
        return True
    
    def launch_fullscreen(self, exe_path: str, mode: str) -> bool:
        """Launch a program and make it fullscreen in foreground (blocking)."""
        from process_manager import parse_command_string
        
        actual_exe, full_cmd = parse_command_string(exe_path)
        
        # Check if user accidentally provided a direct media file
        if os.path.exists(actual_exe) and actual_exe.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.wmv')):
            print(f"[ERROR] Cannot execute a video file directly: {actual_exe}")
            return False
        
        if not os.path.exists(actual_exe):
            print(f"[ERROR] EXE not found: {actual_exe}")
            return False
        
        try:
            print(f"[INFO] Launching {mode} in fullscreen...")
            
            # Pass the full command string to support arguments
            process = subprocess.Popen(
                full_cmd,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            
            # Wait for window to appear
            time.sleep(2)
            
            # Find the window and make it fullscreen
            hwnd = self._find_window_by_process(process.pid)
            if hwnd:
                # Bring to front and maximize (fullscreen)
                self.user32.ShowWindow(hwnd, SW_MAXIMIZE)
                self.user32.SetForegroundWindow(hwnd)
                print(f"[INFO] {mode} window set to fullscreen foreground")
            else:
                print(f"[WARN] Could not find {mode} window, letting it run normally")
            
            # Wait for process to complete
            process.wait()
            print(f"[INFO] {mode} program closed")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to launch {mode}: {e}")
            return False
