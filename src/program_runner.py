"""Program execution management."""
import os
import time
import subprocess


class ProgramRunner:
    """Runs external programs with timeout handling."""
    
    def __init__(self, post_run_delay: float = 1.0):
        self.post_run_delay = post_run_delay
        self.current_process = None
    
    def run(self, exe_path: str, mode: str, duration: int) -> bool:
        """Run an executable for a specified duration."""
        if not os.path.exists(exe_path):
            print(f"[ERROR] EXE not found: {exe_path}")
            return False
        
        print(f"[INFO] Starting {mode} program (will run for {duration} seconds)...")
        
        try:
            self.current_process = subprocess.run(
                [exe_path],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                timeout=duration
            )
            print(f"[INFO] {mode} program finished")
            return True
            
        except subprocess.TimeoutExpired:
            print(f"[INFO] {mode} program timeout reached")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to run {mode}: {e}")
            return False
        finally:
            self.current_process = None
            time.sleep(self.post_run_delay)
