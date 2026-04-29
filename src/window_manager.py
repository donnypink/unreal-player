"""Window management for launching programs and controlling windows using pygetwindow."""
import subprocess
import time
import os
import ctypes
from typing import Optional

try:
    import pygetwindow as gw
except ImportError:
    print("[ERROR] pygetwindow not installed. Please run: pip install pygetwindow")
    raise


class WindowManager:
    """Manages window operations for program launching and title-based switching."""
    
    def __init__(self):
        pass
    
    def launch_nonblocking(self, cmd_string: str) -> Optional[subprocess.Popen]:
        """Launch a program as a non-blocking background process with proper CWD."""
        from process_manager import parse_command_string
        
        actual_exe, full_cmd = parse_command_string(cmd_string)
        
        if os.path.exists(actual_exe) and actual_exe.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.wmv')):
            print(f"[ERROR] Cannot execute a video file directly: {actual_exe}")
            return None
        
        if not os.path.exists(actual_exe):
            print(f"[ERROR] EXE not found: {actual_exe}")
            return None
            
        # Get the directory of the executable so it can load its local assets properly
        exe_dir = os.path.dirname(os.path.abspath(actual_exe))
        
        try:
            process = subprocess.Popen(
                full_cmd,
                cwd=exe_dir if exe_dir else None,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            print(f"[INFO] Launched non-blocking (PID: {process.pid}) in {exe_dir}")
            return process
        except Exception as e:
            print(f"[ERROR] Failed to launch: {e}")
            return None

    def focus_by_title(self, title_substring: str, exclude_substring: Optional[str] = None, maximize: bool = True) -> bool:
        """Focus window matching title substring with highly reliable Alt-key bypass."""
        try:
            all_matches = gw.getWindowsWithTitle(title_substring)
            
            # Filter out excluded titles
            if exclude_substring:
                windows = [w for w in all_matches if exclude_substring.lower() not in w.title.lower()]
            else:
                windows = all_matches
            
            if not windows:
                print(f"[WARN] No window found matching '{title_substring}'.")
                titles = [w.title for w in gw.getAllWindows() if w.title.strip()]
                print(f"[HINT] Available window titles: {titles[:15]}") # Print first 15 to help debug
                return False

            win = windows[0]
            
            # Already active and formatted nicely? Early exit
            if win.isActive and not win.isMinimized:
                if maximize and not win.isMaximized:
                    try: win.maximize()
                    except: pass
                return True

            # Applying Windows ALT-key bypass...
            ctypes.windll.user32.keybd_event(0x12, 0, 0, 0)  # ALT down
            ctypes.windll.user32.keybd_event(0x12, 0, 2, 0)  # ALT up
            
            if win.isMinimized:
                win.restore()
                time.sleep(0.2)
            
            if maximize and not win.isMaximized:
                try:
                    win.maximize()
                    time.sleep(0.1)
                except: pass
            
            try:
                win.activate()
            except Exception as e:
                print(f"[WARN] Failed to send activate to '{win.title}': {e}")
            
            time.sleep(0.1) 
            if win.isActive:
                return True
            else:
                return False

        except Exception as e:
            print(f"[ERROR] Unexpected error focusing '{title_substring}': {e}")
            return False

    def minimize_by_title(self, title_substring: str, exclude_substring: Optional[str] = None) -> bool:
        """Minimize a window by its title."""
        try:
            all_matches = gw.getWindowsWithTitle(title_substring)
            if exclude_substring:
                windows = [w for w in all_matches if exclude_substring.lower() not in w.title.lower()]
            else:
                windows = all_matches
            
            if not windows:
                return False
            
            win = windows[0]
            if not win.isMinimized:
                win.minimize()
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to minimize '{title_substring}': {e}")
            return False