"""Process lifecycle management - Idle program handling."""
import os
import subprocess
import shlex
from typing import Optional, Tuple


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


class ProcessManager:
    """Manages background process lifecycle (Idle program)."""
    
    def __init__(self, exe_path: str):
        self.exe_path = exe_path
        self._process: Optional[subprocess.Popen] = None
    
    def start(self) -> bool:
        """Start the idle program in background (hidden)."""
        # Parse the executable path from the command string
        actual_exe, full_cmd = parse_command_string(self.exe_path)
        
        # Check if user accidentally provided a direct media file
        if os.path.exists(actual_exe) and actual_exe.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.wmv')):
            print(f"[ERROR] Cannot execute a video file directly: {actual_exe}")
            print(f"[HINT] Use a player executable with the video as argument")
            return False
        
        if not os.path.exists(actual_exe):
            print(f"[ERROR] Idle EXE not found: {actual_exe}")
            return False
        
        try:
            print(f"[INFO] Starting idle program...")
            
            # Check if this is a video player (VLC, MPV, etc.) - don't hide these
            is_player = any(player in actual_exe.lower() for player in ['vlc', 'mpv', 'mplayer', 'wmplayer'])
            
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            # Hide non-player processes, show players normally (they'll go fullscreen)
            startupinfo.wShowWindow = 1 if is_player else 0  # SW_SHOWNORMAL=1, SW_HIDE=0
            
            # Pass the full command string to support arguments
            self._process = subprocess.Popen(
                full_cmd,
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