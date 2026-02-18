"""Window management for launching programs in fullscreen."""
import subprocess
import time
import os
from ctypes import windll, Structure, c_long, byref


class WindowManager:
    """Manages window operations for program launching."""
    
    def __init__(self):
        self.user32 = windll.user32
        self.kernel32 = windll.kernel32
    
    def minimize_all_windows(self):
        """Minimize all visible windows."""
        try:
            print("[INFO] Minimizing all windows...")
            
            # EnumWindows callback
            def enum_windows_callback(hwnd, extra):
                if self.user32.IsWindowVisible(hwnd):
                    # Minimize the window
                    self.user32.ShowWindow(hwnd, 6)  # SW_MINIMIZE = 6
                return True
            
            # Enumerate all windows and minimize visible ones
            EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
            callback = EnumWindowsProc(enum_windows_callback)
            self.user32.EnumWindows(callback, 0)
            
            time.sleep(0.5)  # Give windows time to minimize
            print("[INFO] All windows minimized")
            
        except Exception as e:
            print(f"[WARN] Could not minimize windows: {e}")
    
    def launch_fullscreen(self, exe_path: str, mode: str) -> bool:
        """Launch a program and make it fullscreen."""
        if not os.path.exists(exe_path):
            print(f"[ERROR] EXE not found: {exe_path}")
            return False
        
        try:
            print(f"[INFO] Launching {mode} in fullscreen...")
            
            # Launch the program
            process = subprocess.Popen(
                [exe_path],
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
                print(f"[INFO] {mode} window set to fullscreen")
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
            import ctypes
            EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
            cb = EnumWindowsProc(callback)
            self.user32.EnumWindows(cb, 0)
        except Exception:
            pass
        
        return result


import ctypes
