#!/usr/bin/env python3
"""
Unified Picrawler Control Hub
- Live video feed
- Manual robot control
- Radiation detection
- Autonomous exploration
- Real-time data visualization
"""

import cv2
import numpy as np
import threading
import time
import readchar
import json
from datetime import datetime
import matplotlib.pyplot as plt
from collections import deque

try:
    from picrawler import Picrawler
    from radiation_bot import RadiationBot, RadiationSensor
except ImportError:
    print("Warning: Picrawler modules not found, using mock classes")
    Picrawler = None
    RadiationBot = None

class PicrawlerControlHub:
    def __init__(self):
        self.running = False
        self.video_thread = None
        self.display_thread = None
        self.camera = None
        self.current_frame = None
        self.frame_lock = threading.Lock()
        
        # Robot setup
        if RadiationBot:
            self.robot = RadiationBot()
        else:
            self.robot = None
            print("Mock mode: No physical robot")
        
        # Status variables
        self.status = {
            'position': (0, 0, 0),
            'radiation_cpm': 0,
            'radiation_microsv': 0,
            'mode': 'Manual',
            'last_action': 'None',
            'total_samples': 0,
            'max_radiation': 0,
            'battery_level': 100  # Mock battery
        }
        
        # Video settings
        self.video_enabled = True
        self.overlay_enabled = True
        self.recording = False
        self.video_writer = None
        
        # Data logging
        self.data_log = deque(maxlen=1000)
        
    def initialize_camera(self):
        """Initialize camera for video feed"""
        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                print("Warning: Camera not found, using mock video")
                self.camera = None
                return False
            
            # Set camera properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            
            print("Camera initialized successfully")
            return True
        except Exception as e:
            print(f"Camera initialization failed: {e}")
            self.camera = None
            return False
    
    def create_mock_frame(self):
        """Create mock video frame for testing"""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Create mock environment
        cv2.rectangle(frame, (50, 50), (590, 430), (40, 40, 40), -1)
        cv2.circle(frame, (320, 240), 30, (0, 255, 0), -1)  # Robot position
        
        # Add grid
        for i in range(8):
            x = 80 + i * 70
            cv2.line(frame, (x, 80), (x, 400), (80, 80, 80), 1)
        for i in range(5):
            y = 80 + i * 80
            cv2.line(frame, (80, y), (560, y), (80, 80, 80), 1)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        cv2.putText(frame, f"MOCK FEED {timestamp}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return frame
    
    def video_capture_loop(self):
        """Main video capture loop"""
        while self.running:
            try:
                if self.camera and self.camera.isOpened():
                    ret, frame = self.camera.read()
                    if not ret:
                        frame = self.create_mock_frame()
                else:
                    frame = self.create_mock_frame()
                
                # Add overlay if enabled
                if self.overlay_enabled:
                    frame = self.add_status_overlay(frame)
                
                # Store frame
                with self.frame_lock:
                    self.current_frame = frame.copy()
                
                # Record if enabled
                if self.recording and self.video_writer:
                    self.video_writer.write(frame)
                    
            except Exception as e:
                print(f"Video capture error: {e}")
                time.sleep(0.1)
            
            time.sleep(1/30)  # 30 FPS
    
    def add_status_overlay(self, frame):
        """Add status information overlay to video frame"""
        overlay = frame.copy()
        
        # Semi-transparent background for text
        cv2.rectangle(overlay, (10, 10), (350, 200), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Status information
        y_offset = 35
        line_height = 25
        
        # Robot status
        pos = self.status['position']
        cv2.putText(frame, f"Position: ({pos[0]:.1f}, {pos[1]:.1f})", 
                   (15, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        y_offset += line_height
        
        cv2.putText(frame, f"Heading: {pos[2]:.0f}°", 
                   (15, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        y_offset += line_height
        
        # Radiation data
        rad_color = (0, 255, 255)  # Yellow
        if self.status['radiation_cpm'] > 100:
            rad_color = (0, 0, 255)  # Red for high radiation
        elif self.status['radiation_cpm'] > 50:
            rad_color = (0, 165, 255)  # Orange
        
        cv2.putText(frame, f"Radiation: {self.status['radiation_cpm']:.1f} CPM", 
                   (15, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, rad_color, 2)
        y_offset += line_height
        
        cv2.putText(frame, f"Dose: {self.status['radiation_microsv']:.2f} µSv/h", 
                   (15, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, rad_color, 2)
        y_offset += line_height
        
        # Mode and controls
        cv2.putText(frame, f"Mode: {self.status['mode']}", 
                   (15, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        y_offset += line_height
        
        cv2.putText(frame, f"Last: {self.status['last_action']}", 
                   (15, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Recording indicator
        if self.recording:
            cv2.circle(frame, (620, 30), 10, (0, 0, 255), -1)
            cv2.putText(frame, "REC", (590, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        
        # Controls help (bottom)
        help_text = "ESC:Quit | SPACE:Demo | R:Record | O:Overlay | H:Help"
        cv2.putText(frame, help_text, (10, 470), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
        
        return frame
    
    def display_loop(self):
        """Display video feed"""
        while self.running:
            with self.frame_lock:
                if self.current_frame is not None:
                    cv2.imshow('Picrawler Control Hub', self.current_frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                self.stop()
                break
            
            time.sleep(1/30)
    
    def update_status(self):
        """Update robot status"""
        if self.robot:
            self.status['position'] = self.robot.tracker.get_position()
            
            # Get radiation reading
            try:
                if hasattr(self.robot, 'sensor'):
                    cpm = self.robot.sensor.get_reading()
                    microsv = self.robot.sensor.convert_to_microsieverts(cpm)
                    self.status['radiation_cpm'] = cpm
                    self.status['radiation_microsv'] = microsv
                    
                    if cpm > self.status['max_radiation']:
                        self.status['max_radiation'] = cpm
            except:
                pass
            
            self.status['total_samples'] = len(self.robot.radiation_data) if hasattr(self.robot, 'radiation_data') else 0
    
    def start_recording(self):
        """Start video recording"""
        if not self.recording:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"picrawler_session_{timestamp}.mp4"
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.video_writer = cv2.VideoWriter(filename, fourcc, 30.0, (640, 480))
            self.recording = True
            print(f"Recording started: {filename}")
    
    def stop_recording(self):
        """Stop video recording"""
        if self.recording:
            self.recording = False
            if self.video_writer:
                self.video_writer.release()
                self.video_writer = None
            print("Recording stopped")
    
    def keyboard_control_loop(self):
        """Handle keyboard input for robot control"""
        print("\n=== PICRAWLER CONTROL HUB ===")
        print("Movement: WASD | Stand/Sit: Q/E")
        print("Radiation: R | Demo: SPACE | Record: Shift+R")
        print("Help: H | Quit: ESC")
        print("=====================================\n")
        
        while self.running:
            try:
                key = readchar.readchar()
                
                if key == '\x1b':  # ESC
                    self.stop()
                    break
                
                # Robot movement
                elif key.lower() == 'w':
                    self.move_robot('forward', 2)
                elif key.lower() == 's':
                    self.move_robot('backward', 2)
                elif key.lower() == 'a':
                    self.move_robot('turn left', 1)
                elif key.lower() == 'd':
                    self.move_robot('turn right', 1)
                elif key.lower() == 'q':
                    self.robot_action('stand')
                elif key.lower() == 'e':
                    self.robot_action('sit')
                
                # Radiation and demo functions
                elif key.lower() == 'r':
                    if key.isupper():  # Shift+R
                        if self.recording:
                            self.stop_recording()
                        else:
                            self.start_recording()
                    else:
                        self.take_radiation_reading()
                
                elif key == ' ':  # SPACE
                    self.run_demo_mode()
                
                # Utility functions
                elif key.lower() == 'o':
                    self.overlay_enabled = not self.overlay_enabled
                    print(f"Overlay {'enabled' if self.overlay_enabled else 'disabled'}")
                
                elif key.lower() == 'h':
                    self.show_help()
                
                elif key.lower() == 'v':
                    self.save_data()
                
                elif key.lower() == 'm':
                    self.generate_map()
                
            except KeyboardInterrupt:
                self.stop()
                break
    
    def move_robot(self, action, steps):
        """Execute robot movement"""
        if self.robot:
            self.robot.move_and_track(action, steps)
            self.status['last_action'] = f"{action} {steps}"
            self.update_status()
    
    def robot_action(self, action):
        """Execute robot action"""
        if self.robot:
            self.robot.do_action(action, 1, 80)
            self.status['last_action'] = action
    
    def take_radiation_reading(self):
        """Take radiation reading at current position"""
        if self.robot and hasattr(self.robot, 'collect_radiation_sample'):
            self.status['mode'] = 'Sampling'
            print("Taking radiation reading...")
            reading = self.robot.collect_radiation_sample(3)
            self.status['mode'] = 'Manual'
            self.update_status()
            print(f"Radiation: {reading:.1f} CPM")
    
    def run_demo_mode(self):
        """Run autonomous demo"""
        if self.robot and hasattr(self.robot, 'demo_mode'):
            self.status['mode'] = 'Demo'
            print("Starting demo mode...")
            
            # Run demo in separate thread to keep video going
            demo_thread = threading.Thread(target=self.robot.demo_mode)
            demo_thread.daemon = True
            demo_thread.start()
    
    def generate_map(self):
        """Generate and save radiation heatmap"""
        if self.robot and hasattr(self.robot, 'generate_heatmap'):
            self.robot.generate_heatmap()
            print("Heatmap generated!")
    
    def save_data(self):
        """Save collected data"""
        if self.robot and hasattr(self.robot, 'save_data'):
            self.robot.save_data()
            print("Data saved!")
    
    def show_help(self):
        """Display help information"""
        print("\n=== CONTROLS ===")
        print("Movement:")
        print("  W/S - Forward/Backward")
        print("  A/D - Turn Left/Right")
        print("  Q/E - Stand/Sit")
        print("\nRadiation:")
        print("  r - Take reading")
        print("  SPACE - Demo mode")
        print("  m - Generate map")
        print("  v - Save data")
        print("\nVideo:")
        print("  R - Start/stop recording")
        print("  o - Toggle overlay")
        print("\nESC - Quit")
        print("================\n")
    
    def start(self):
        """Start the control hub"""
        self.running = True
        
        # Initialize camera
        self.initialize_camera()
        
        # Start threads
        self.video_thread = threading.Thread(target=self.video_capture_loop)
        self.video_thread.daemon = True
        self.video_thread.start()
        
        if self.video_enabled:
            self.display_thread = threading.Thread(target=self.display_loop)
            self.display_thread.daemon = True
            self.display_thread.start()
        
        # Update status periodically
        status_thread = threading.Thread(target=self.status_update_loop)
        status_thread.daemon = True
        status_thread.start()
        
        # Start keyboard control (main thread)
        self.keyboard_control_loop()
    
    def status_update_loop(self):
        """Periodically update status"""
        while self.running:
            self.update_status()
            time.sleep(0.5)
    
    def stop(self):
        """Stop all operations"""
        print("\nShutting down...")
        self.running = False
        
        if self.recording:
            self.stop_recording()
        
        if self.camera:
            self.camera.release()
        
        cv2.destroyAllWindows()
        
        if self.robot:
            try:
                self.robot.do_action('sit', 1, 80)
            except:
                pass
        
        print("Control hub stopped.")

def main():
    hub = PicrawlerControlHub()
    
    try:
        hub.start()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        hub.stop()

if __name__ == "__main__":
    main()