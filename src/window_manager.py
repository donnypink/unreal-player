"""Window management for launching programs in fullscreen."""
import subprocess
import time
import os
import ctypes
from ctypes import windll


class WindowManager:
    """Manages window operations for program launching."""
    
    def __init__(self):
        self.user32 = windll.user32
    
    def launch_fullscreen(self, exe_path: str, mode: str) -> bool:
        """Launch a program and make it fullscreen in foreground."""
        if os.path.exists(exe_path) and exe_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.wmv')):
            print(f"[ERROR] Cannot execute a video file directly: {exe_path}")
            return False

        if not os.path.exists(exe_path):
            print(f"[ERROR] EXE not found: {exe_path}")
            return False
        
        try:
            print(f"[INFO] Launching {mode} in fullscreen...")
            
            # Pass string to support command arguments
            process = subprocess.Popen(
                exe_path,
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
