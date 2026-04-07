"""Window management for launching programs in fullscreen."""
import subprocess
import time
import os
import ctypes
from typing import Tuple
from ctypes import windll


def parse_command_string(cmd_string: str) -> Tuple[str, str]:
    """Parse a command string into executable path and arguments.
    
    Returns:
        Tuple of (executable_path, full_command_string)
    """
    # Handle quoted paths with spaces
    cmd_string = cmd_string.strip()
    if cmd_string.startswith('"'):
        # Find the closing quote
        end_quote = cmd_string.find('"', 1)
        if end_quote > 0:
            exe_path = cmd_string[1:end_quote]
            return exe_path, cmd_string
    # No quotes, split on first space
    parts = cmd_string.split(None, 1)
    exe_path = parts[0] if parts else cmd_string
    return exe_path, cmd_string


class WindowManager:
    """Manages window operations for program launching."""
    
    def __init__(self):
        self.user32 = windll.user32
    
    def launch_fullscreen(self, exe_path: str, mode: str) -> bool:
        """Launch a program and make it fullscreen in foreground."""
        # Parse the executable path from the command string
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
                self.user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE = 3
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
    
    def _find_window_by_process(self, pid: int):
        """Find window handle by process ID."""
        result = None
        
        def callback(hwnd, extra):
            nonlocal result
            if self.user32.IsWindowVisible(hwnd):
                # Get process ID of the window
                lpdw_process_id = ctypes.c_ulong()
                self.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(lpdw_process_id))
                if lpdw_process_id.value == pid:
                    result = hwnd
                    return False  # Stop enumeration
            return True
        
        try:
            EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
            cb = EnumWindowsProc(callback)
            self.user32.EnumWindows(cb, 0)
        except Exception:
            pass
        
        return result