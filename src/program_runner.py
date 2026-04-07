"""Program execution management."""
import os
import time
import subprocess
import signal
from typing import Tuple


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


class ProgramRunner:
    """Runs external programs until manually closed."""
    
    def __init__(self, post_run_delay: float = 1.0):
        self.post_run_delay = post_run_delay
        self.current_process = None
    
    def run(self, exe_path: str, mode: str) -> bool:
        """Run an executable until it exits (manually closed by user)."""
        # Parse the executable path from the command string
        actual_exe, full_cmd = parse_command_string(exe_path)
        
        # Check if user accidentally provided a direct media file
        if os.path.exists(actual_exe) and actual_exe.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.wmv')):
            print(f"[ERROR] Cannot execute a video file directly: {actual_exe}")
            return False
        
        if not os.path.exists(actual_exe):
            print(f"[ERROR] EXE not found: {actual_exe}")
            return False
        
        print(f"[INFO] Starting {mode} program (run until manually closed)...")
        
        try:
            # Use Popen for better control, CREATE_NEW_PROCESS_GROUP for clean termination
            # Pass the full command string to support arguments
            self.current_process = subprocess.Popen(
                full_cmd,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            
            # Wait for process to complete (manual close)
            return_code = self.current_process.wait()
            print(f"[INFO] {mode} program closed (return code: {return_code})")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to run {mode}: {e}")
            return False
        finally:
            self.current_process = None
            time.sleep(self.post_run_delay)
    
    def terminate(self) -> bool:
        """Terminate the current running process gracefully."""
        if self.current_process is None:
            return True
        
        process = self.current_process
        terminated = False
        
        try:
            # Try graceful termination first
            print(f"[INFO] Terminating process (PID: {process.pid})...")
            
            # On Windows, send CTRL_BREAK_EVENT to the process group
            if hasattr(signal, 'CTRL_BREAK_EVENT'):
                try:
                    os.kill(process.pid, signal.CTRL_BREAK_EVENT)
                except (ProcessLookupError, OSError):
                    pass
            
            # Wait for graceful shutdown (up to 5 seconds)
            try:
                process.wait(timeout=5)
                print("[INFO] Process terminated gracefully")
                terminated = True
            except subprocess.TimeoutExpired:
                print("[WARN] Graceful termination timed out, forcing kill...")
                
        except Exception as e:
            print(f"[WARN] Error during graceful termination: {e}")
        
        # Force kill if graceful termination failed
        if not terminated:
            try:
                process.kill()
                process.wait(timeout=2)
                print("[INFO] Process killed")
                terminated = True
            except Exception as e:
                print(f"[ERROR] Failed to kill process: {e}")
        
        # Always clear current_process
        self.current_process = None
        return terminated