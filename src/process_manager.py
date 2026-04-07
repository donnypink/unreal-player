"""Process lifecycle management - Idle program handling."""
import os
import subprocess
from typing import Optional


class ProcessManager:
    """Manages background process lifecycle (Idle program)."""
    
    def __init__(self, exe_path: str):
        self.exe_path = exe_path
        self._process: Optional[subprocess.Popen] = None
    
    def start(self) -> bool:
        """Start the idle program in background (hidden)."""
        if os.path.exists(self.exe_path) and self.exe_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.wmv')):
            print(f"[ERROR] Cannot execute a video file directly: {self.exe_path}")
            print(f"[HINT] Update config.json to use an executable player (e.g., 'vlc.exe {self.exe_path}')")
            return False

        if not os.path.exists(self.exe_path):
            print(f"[ERROR] Idle EXE not found: {self.exe_path}")
            return False
        
        try:
            print(f"[INFO] Starting idle program (background)...")
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0  # SW_HIDE
            
            self._process = subprocess.Popen(
                [self.exe_path],
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                startupinfo=startupinfo
            )
            print(f"[INFO] Idle program started (PID: {self._process.pid})")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to start idle: {e}")
            return False
    
    def is_running(self) -> bool:
        """Check if process is still running."""
        if self._process is None:
            return False
        return self._process.poll() is None
    
    def ensure_running(self) -> bool:
        """Restart if not running."""
        if not self.is_running():
            print("[INFO] Idle program not running, restarting...")
            return self.start()
        return True
    
    def stop(self) -> bool:
        """Stop the idle process gracefully."""
        if not self.is_running():
            return True
        
        try:
            print("[INFO] Stopping idle program...")
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait(timeout=2)
            return True
        except Exception as e:
            print(f"[WARN] Error stopping idle: {e}")
            return False
