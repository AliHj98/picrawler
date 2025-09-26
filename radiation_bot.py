#!/usr/bin/env python3
"""
Radiation Detection Spider Bot
Hackathon project for autonomous radiation mapping and source detection
"""

from picrawler import Picrawler
import time
import math
import json
import threading
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

try:
    import RPi.GPIO as GPIO
except ImportError:
    print("Warning: RPi.GPIO not available, using mock sensor")
    GPIO = None

class RadiationSensor:
    def __init__(self, pin=18, sensor_type="cajoe_d_v1_1"):
        self.pin = pin
        self.sensor_type = sensor_type
        self.pulse_count = 0
        self.start_time = time.time()
        self.reading_interval = 5.0  # seconds for stable CPM reading
        self.last_reading = 0
        self.pulse_buffer = []
        
        # Cajoe D-v1.1 specific settings
        # VIN pin is pulse output, direct connection to GPIO
        # Tube: J305ß, Sensitivity: 65cps/(μR/s) for gamma
        
        if GPIO:
            GPIO.setmode(GPIO.BCM)
            # Use pull-down for Cajoe D-v1.1 (active high pulses)
            # If using voltage divider, may need pull-up instead
            GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            # Detect rising edge for Cajoe pulse detection
            # Increase bouncetime if getting false triggers
            GPIO.add_event_detect(self.pin, GPIO.RISING, callback=self._pulse_callback, bouncetime=10)
        
    def _pulse_callback(self, channel):
        """Callback for radiation pulse detection from Cajoe D-v1.1"""
        current_time = time.time()
        self.pulse_count += 1
        self.pulse_buffer.append(current_time)
        
        # Keep only last 60 seconds of pulses for rolling CPM
        cutoff_time = current_time - 60
        self.pulse_buffer = [t for t in self.pulse_buffer if t > cutoff_time]
    
    def get_reading(self):
        """Get current radiation reading in CPM (counts per minute)"""
        current_time = time.time()
        elapsed = current_time - self.start_time
        
        if elapsed >= self.reading_interval:
            # Calculate CPM using pulse buffer for more accurate reading
            recent_pulses = len(self.pulse_buffer)
            cpm = recent_pulses  # Already filtered to last 60 seconds
            
            # Also calculate short-term average
            if elapsed > 0:
                short_term_cpm = (self.pulse_count / elapsed) * 60
                # Use average of both methods for stability
                self.last_reading = (cpm + short_term_cpm) / 2
            else:
                self.last_reading = cpm
                
            self.pulse_count = 0
            self.start_time = current_time
            return self.last_reading
        return self.last_reading
    
    def get_instant_cpm(self):
        """Get instant CPM based on pulse buffer"""
        return len(self.pulse_buffer)
    
    def convert_to_microsieverts(self, cpm):
        """Convert CPM to µSv/h using Cajoe D-v1.1 sensitivity"""
        # J305ß tube sensitivity: 65 cps/(μR/s) for gamma
        # 1 μR/s ≈ 0.036 µSv/h (rough conversion)
        if cpm <= 0:
            return 0
        cps = cpm / 60
        micro_r_per_sec = cps / 65
        micro_sv_per_hour = micro_r_per_sec * 0.036 * 3600
        return micro_sv_per_hour
    
    def get_mock_reading(self, x, y, source_x=50, source_y=50):
        """Mock sensor for testing - simulates radiation field"""
        distance = math.sqrt((x - source_x)**2 + (y - source_y)**2)
        base_radiation = 20  # background
        source_strength = 1000
        radiation = base_radiation + source_strength / (1 + distance/10)
        return radiation + np.random.normal(0, radiation * 0.1)

class PositionTracker:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.heading = 0  # degrees
        self.step_size = 10  # cm per step
        
    def update_position(self, action, steps):
        """Update position based on robot movement"""
        distance = steps * self.step_size
        
        if 'forward' in action:
            self.x += distance * math.cos(math.radians(self.heading))
            self.y += distance * math.sin(math.radians(self.heading))
        elif 'backward' in action:
            self.x -= distance * math.cos(math.radians(self.heading))
            self.y -= distance * math.sin(math.radians(self.heading))
        elif 'turn left' in action:
            self.heading += 45 * steps
        elif 'turn right' in action:
            self.heading -= 45 * steps
            
        self.heading = self.heading % 360
    
    def get_position(self):
        return (self.x, self.y, self.heading)

class RadiationBot(Picrawler):
    def __init__(self, sensor_pin=18):
        super().__init__()
        self.sensor = RadiationSensor(sensor_pin)
        self.tracker = PositionTracker()
        self.radiation_data = []
        self.heatmap_data = defaultdict(list)
        self.exploration_grid = []
        self.is_exploring = False
        self.max_radiation = 0
        self.max_radiation_pos = (0, 0)
        
        print("RadiationBot initialized!")
        print("Starting calibration...")
        self.do_action('stand', 1, 80)
        time.sleep(1)
    
    def collect_radiation_sample(self, duration=5):
        """Collect radiation reading at current position"""
        print(f"Collecting radiation sample for {duration} seconds...")
        
        readings = []
        microsievert_readings = []
        start_time = time.time()
        
        # Clear pulse buffer for fresh reading
        if hasattr(self.sensor, 'pulse_buffer'):
            self.sensor.pulse_buffer = []
        
        while time.time() - start_time < duration:
            if GPIO:
                reading = self.sensor.get_reading()
                instant_cpm = self.sensor.get_instant_cpm()
                microsieverts = self.sensor.convert_to_microsieverts(reading)
            else:
                # Mock reading for testing
                x, y, _ = self.tracker.get_position()
                reading = self.sensor.get_mock_reading(x, y)
                instant_cpm = reading
                microsieverts = reading * 0.01  # Mock conversion
            
            readings.append(reading)
            microsievert_readings.append(microsieverts)
            print(f"  {time.time() - start_time:.1f}s: {reading:.1f} CPM ({microsieverts:.2f} µSv/h)")
            time.sleep(1.0)
        
        avg_reading = sum(readings) / len(readings) if readings else 0
        avg_microsieverts = sum(microsievert_readings) / len(microsievert_readings) if microsievert_readings else 0
        x, y, heading = self.tracker.get_position()
        
        data_point = {
            'timestamp': datetime.now().isoformat(),
            'position': (x, y),
            'heading': heading,
            'radiation_cpm': avg_reading,
            'radiation_microsieverts': avg_microsieverts,
            'readings': readings,
            'microsievert_readings': microsievert_readings
        }
        
        self.radiation_data.append(data_point)
        self.heatmap_data[(round(x/10)*10, round(y/10)*10)].append(avg_reading)
        
        if avg_reading > self.max_radiation:
            self.max_radiation = avg_reading
            self.max_radiation_pos = (x, y)
        
        print(f"Position: ({x:.1f}, {y:.1f}), Radiation: {avg_reading:.1f} CPM ({avg_microsieverts:.2f} µSv/h)")
        return avg_reading
    
    def move_and_track(self, action, steps, speed=60):
        """Execute movement and update position tracking"""
        print(f"Moving: {action}, {steps} steps")
        self.do_action(action, steps, speed)
        self.tracker.update_position(action, steps)
        time.sleep(0.5)  # Allow movement to complete
    
    def explore_grid(self, grid_size=5, step_distance=2):
        """Systematic grid exploration"""
        print(f"Starting grid exploration: {grid_size}x{grid_size}")
        self.is_exploring = True
        
        for row in range(grid_size):
            for col in range(grid_size):
                if not self.is_exploring:
                    break
                    
                print(f"Exploring grid point ({row}, {col})")
                
                # Collect radiation sample
                radiation = self.collect_radiation_sample(2)
                
                # Move to next grid point
                if col < grid_size - 1:  # Not last column
                    self.move_and_track('forward', step_distance)
                elif row < grid_size - 1:  # End of row, not last row
                    if row % 2 == 0:  # Even row - turn right
                        self.move_and_track('turn right', 1)
                        self.move_and_track('forward', step_distance)
                        self.move_and_track('turn right', 1)
                    else:  # Odd row - turn left
                        self.move_and_track('turn left', 1)
                        self.move_and_track('forward', step_distance)
                        self.move_and_track('turn left', 1)
        
        print("Grid exploration complete!")
        self.is_exploring = False
        return self.radiation_data
    
    def find_radiation_source(self, max_steps=20):
        """Navigate toward highest radiation source using gradient ascent"""
        print("Starting radiation source detection...")
        
        current_radiation = self.collect_radiation_sample(2)
        steps_taken = 0
        
        while steps_taken < max_steps:
            # Test all four directions
            directions = ['forward', 'turn right', 'turn right', 'turn right']
            best_direction = None
            best_radiation = current_radiation
            
            for direction in directions:
                # Turn to test direction
                if 'turn' in direction:
                    self.move_and_track(direction, 1)
                    continue
                
                # Move forward and test
                self.move_and_track('forward', 1)
                test_radiation = self.collect_radiation_sample(1)
                
                if test_radiation > best_radiation:
                    best_radiation = test_radiation
                    best_direction = 'forward'
                
                # Move back
                self.move_and_track('backward', 1)
                self.move_and_track('turn right', 1)  # Continue rotation
            
            if best_direction:
                # Move in best direction
                self.move_and_track('forward', 2)
                current_radiation = best_radiation
                print(f"Moving toward source, radiation: {current_radiation:.1f} CPM")
            else:
                print("No improvement found, source likely found!")
                break
                
            steps_taken += 1
        
        final_pos = self.tracker.get_position()
        print(f"Source search complete! Final position: ({final_pos[0]:.1f}, {final_pos[1]:.1f})")
        print(f"Final radiation level: {current_radiation:.1f} CPM")
        
    def generate_heatmap(self, save_file="radiation_heatmap.png"):
        """Generate and save radiation heatmap"""
        if not self.radiation_data:
            print("No radiation data collected yet!")
            return
        
        print("Generating radiation heatmap...")
        
        # Extract positions and radiation levels
        positions = [data['position'] for data in self.radiation_data]
        radiations = [data['radiation_cpm'] for data in self.radiation_data]
        
        x_coords = [pos[0] for pos in positions]
        y_coords = [pos[1] for pos in positions]
        
        # Create heatmap
        plt.figure(figsize=(10, 8))
        scatter = plt.scatter(x_coords, y_coords, c=radiations, cmap='hot', s=100)
        plt.colorbar(scatter, label='Radiation (CPM)')
        plt.xlabel('X Position (cm)')
        plt.ylabel('Y Position (cm)')
        plt.title('Radiation Heatmap')
        plt.grid(True, alpha=0.3)
        
        # Mark highest radiation point
        if self.max_radiation_pos:
            plt.scatter(self.max_radiation_pos[0], self.max_radiation_pos[1], 
                       c='blue', s=200, marker='x', label=f'Max: {self.max_radiation:.1f} CPM')
            plt.legend()
        
        plt.tight_layout()
        plt.savefig(save_file, dpi=300, bbox_inches='tight')
        print(f"Heatmap saved as {save_file}")
        
        return save_file
    
    def save_data(self, filename="radiation_data.json"):
        """Save all collected radiation data"""
        with open(filename, 'w') as f:
            json.dump(self.radiation_data, f, indent=2)
        print(f"Data saved to {filename}")
    
    def demo_mode(self):
        """Run complete demonstration"""
        print("=== RADIATION DETECTION SPIDER BOT DEMO ===")
        print("1. Grid exploration")
        print("2. Source detection")
        print("3. Heatmap generation")
        
        try:
            # Grid exploration
            self.explore_grid(grid_size=4, step_distance=2)
            
            # Source detection
            self.find_radiation_source(max_steps=15)
            
            # Generate results
            self.generate_heatmap()
            self.save_data()
            
            print("=== DEMO COMPLETE ===")
            print(f"Total samples collected: {len(self.radiation_data)}")
            print(f"Highest radiation: {self.max_radiation:.1f} CPM at {self.max_radiation_pos}")
            
        except KeyboardInterrupt:
            print("\nDemo interrupted by user")
            self.is_exploring = False
        finally:
            self.do_action('sit', 1, 80)
            if GPIO:
                GPIO.cleanup()

if __name__ == "__main__":
    # Create radiation bot
    bot = RadiationBot()
    
    try:
        # Run demo
        bot.demo_mode()
        
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        if GPIO:
            GPIO.cleanup()