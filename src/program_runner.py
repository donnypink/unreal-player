"""Program execution management."""
import os
import time
import subprocess


class ProgramRunner:
    """Runs external programs until manually closed."""
    
    def __init__(self, post_run_delay: float = 1.0):
        self.post_run_delay = post_run_delay
        self.current_process = None
    
    def run(self, exe_path: str, mode: str) -> bool:
        """Run an executable until it exits (manually closed by user)."""
        if not os.path.exists(exe_path):
            print(f"[ERROR] EXE not found: {exe_path}")
            return False
        
        print(f"[INFO] Starting {mode} program (run until manually closed)...")
        
        try:
            # Run without timeout - waits for manual close
            self.current_process = subprocess.run(
                [exe_path],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            print(f"[INFO] {mode} program closed")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to run {mode}: {e}")
            return False
        finally:
            self.current_process = None
            time.sleep(self.post_run_delay)
