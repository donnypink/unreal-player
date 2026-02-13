"""
UE Controller - Motion Detection Program
Switches between two Unreal Engine executables based on motion detection

IMPORTANT - Camera Sharing Solution:
This program uses TIME-BASED HANDOFF to handle single camera sharing:
1. Launch UE program
2. Wait for it to finish (runs briefly)
3. Re-acquire camera
4. Check for motion
5. Launch next program

Your UE programs should be designed to run briefly and exit automatically.

Usage:
    python ue_controller.py

Edit config.json to set your EXE paths and camera settings.
"""

import subprocess
import time
import json
import os
import sys
import cv2
import numpy as np
from pathlib import Path


class UEController:
    """Controls switching between UE programs based on motion detection."""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize controller with configuration."""
        self.config = self._load_config(config_path)
        self.current_process = None
        self.current_mode = None  # "tracking" or "idle"
        self.motion_history = []
        self.previous_frame = None
        
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from JSON file."""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(path, 'r') as f:
            return json.load(f)
    
    def run_program(self, exe_path: str, mode: str, run_duration: int):
        """
        Run an executable for a specified duration.
        
        CAMERA SHARING SOLUTION:
        - Launch the UE program
        - WAIT until it finishes (user's UE program runs briefly then exits)
        - After UE exits, we can re-acquire the camera for detection
        """
        if not os.path.exists(exe_path):
            print(f"[ERROR] EXE not found: {exe_path}")
            return False
            
        print(f"[INFO] Starting {mode} program (will run for {run_duration} seconds)...")
        
        try:
            # Launch the program and WAIT for it to finish
            # This is the key: UE program must exit for camera to be available again
            self.current_process = subprocess.run(
                [exe_path],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                timeout=run_duration  # Wait for program to finish or timeout
            )
            self.current_mode = mode
            print(f"[INFO] {mode} program finished")
            return True
            
        except subprocess.TimeoutExpired:
            # Program ran for max duration - treat as "finished"
            print(f"[INFO] {mode} program timeout reached")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to run {mode}: {e}")
            return False
        finally:
            self.current_process = None
            # Give OS time to release camera resources
            time.sleep(1)
    
    def detect_motion(self, cap) -> bool:
        """
        Detect motion using the camera.
        Returns True if motion detected, False otherwise.
        """
        # Read multiple frames to get stable reading
        frames_to_check = 5
        motion_detected = False
        
        for _ in range(frames_to_check):
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue
                
            # Resize for faster processing
            frame = cv2.resize(frame, (320, 240))
            
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Apply Gaussian blur to reduce noise
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            
            # Initialize previous frame on first run
            if self.previous_frame is None:
                self.previous_frame = gray
                continue
            
            # Calculate difference between frames
            frame_delta = cv2.absdiff(self.previous_frame, gray)
            
            # Apply threshold to get motion regions
            thresh = cv2.threshold(frame_delta, self.config.get("motion_threshold", 30), 255, cv2.THRESH_BINARY)[1]
            
            # Dilate to fill holes
            thresh = cv2.dilate(thresh, None, iterations=2)
            
            # Find contours of motion areas
            contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Check if any significant motion detected
            if any(cv2.contourArea(c) > 500 for c in contours):
                motion_detected = True
            
            # Update previous frame
            self.previous_frame = gray
            
            time.sleep(0.05)  # Small delay between frames
        
        return motion_detected
    
    def should_switch(self, motion_detected: bool) -> str:
        """
        Determine if we should switch programs based on motion detection.
        Uses a simple counter to avoid flickering.
        """
        self.motion_history.append(motion_detected)
        
        # Keep only recent history
        delay_frames = self.config.get("detection_delay_frames", 5)
        if len(self.motion_history) > delay_frames:
            self.motion_history.pop(0)
        
        # Decision: if majority of recent frames show motion, switch to tracking
        # otherwise switch to idle
        motion_count = sum(self.motion_history)
        
        if motion_count >= len(self.motion_history) / 2:
            return "tracking"
        else:
            return "idle"
    
    def check_camera_and_decide(self) -> str:
        """
        Check camera for motion and decide which program to run next.
        Returns "tracking" or "idle".
        """
        camera_index = self.config.get("camera_index", 0)
        cap = None
        
        try:
            # Open camera - THIS WORKS because previous UE program has exited
            print("[INFO] Opening camera to check for motion...")
            cap = cv2.VideoCapture(camera_index)
            
            if not cap.isOpened():
                print("[ERROR] Cannot open camera")
                return self.current_mode or "idle"
            
            # Give camera time to initialize
            time.sleep(0.5)
            
            # Detect motion
            motion_detected = self.detect_motion(cap)
            
            # Determine mode based on motion
            recommended_mode = self.should_switch(motion_detected)
            
            print(f"[RESULT] Motion detected: {motion_detected} → Mode: {recommended_mode}")
            return recommended_mode
            
        except Exception as e:
            print(f"[ERROR] Camera check failed: {e}")
            return self.current_mode or "idle"
        finally:
            if cap:
                cap.release()
                print("[INFO] Camera released")
    
    def run(self):
        """Main loop: run programs briefly, then check camera to decide next program."""
        print("=" * 50)
        print("UE Controller - Motion Detection Program")
        print("=" * 50)
        print(f"Tracking EXE: {self.config.get('tracking_exe')}")
        print(f"Idle EXE: {self.config.get('idle_exe')}")
        print(f"Tracking run time: {self.config.get('tracking_run_seconds', 30)} seconds")
        print(f"Idle run time: {self.config.get('idle_run_seconds', 60)} seconds")
        print("=" * 50)
        print("\nIMPORTANT: Your UE programs must be designed to run briefly")
        print("and exit automatically. The controller waits for the program")
        print("to finish before checking the camera.\n")
        
        # Settings for how long each program runs
        tracking_duration = self.config.get("tracking_run_seconds", 30)
        idle_duration = self.config.get("idle_run_seconds", 60)
        
        # Start with idle program (or detect first)
        recommended_mode = "idle"
        
        try:
            while True:
                # Decide which program to run
                if recommended_mode == "tracking":
                    exe_path = self.config.get("tracking_exe")
                    run_duration = tracking_duration
                else:
                    exe_path = self.config.get("idle_exe")
                    run_duration = idle_duration
                
                # Run the UE program (blocks until it exits)
                self.run_program(exe_path, recommended_mode, run_duration)
                
                # After UE program exits, check camera to decide next action
                print("[INFO] Checking camera for motion...")
                recommended_mode = self.check_camera_and_decide()
                
                # Brief pause before next cycle
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n[INFO] Shutting down...")
        except Exception as e:
            print(f"[ERROR] {e}")


if __name__ == "__main__":
    # Get config path from command line or use default
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.json"
    
    try:
        controller = UEController(config_path)
        controller.run()
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        print("Please create config.json with your EXE paths")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
