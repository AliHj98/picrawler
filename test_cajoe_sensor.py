#!/usr/bin/env python3
"""
Cajoe D-v1.1 Radiation Detector Test Script
Quick test to verify sensor connection and calibration
"""

from radiation_bot import RadiationSensor
import time
import signal
import sys

def signal_handler(sig, frame):
    print("\nTest interrupted by user")
    if 'sensor' in globals():
        try:
            import RPi.GPIO as GPIO
            GPIO.cleanup()
        except:
            pass
    sys.exit(0)

def main():
    print("=== Cajoe D-v1.1 Radiation Detector Test ===")
    print("Press Ctrl+C to stop\n")
    
    # Setup signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Initialize sensor
        print("Initializing Cajoe D-v1.1 on GPIO18...")
        sensor = RadiationSensor(pin=18, sensor_type="cajoe_d_v1_1")
        
        print("Sensor initialized successfully!")
        print("Waiting for radiation pulses...\n")
        
        # Test loop
        start_time = time.time()
        last_pulse_count = 0
        
        while True:
            current_time = time.time()
            elapsed = current_time - start_time
            
            # Get readings
            cpm = sensor.get_reading()
            instant_cpm = sensor.get_instant_cpm()
            microsieverts = sensor.convert_to_microsieverts(cpm)
            total_pulses = sensor.pulse_count
            
            # Display status
            print(f"Time: {elapsed:6.1f}s | "
                  f"CPM: {cpm:6.1f} | "
                  f"Instant: {instant_cpm:3.0f} | "
                  f"µSv/h: {microsieverts:6.2f} | "
                  f"Total pulses: {total_pulses}")
            
            # Check for new pulses
            if total_pulses > last_pulse_count:
                print(f"  >>> PULSE DETECTED! (+{total_pulses - last_pulse_count})")
                last_pulse_count = total_pulses
            
            # Radiation level assessment
            if cpm > 100:
                print("  ⚠️  HIGH RADIATION DETECTED!")
            elif cpm > 50:
                print("  ⚡ Elevated radiation")
            elif cpm < 5:
                print("  📡 Check sensor connection")
            
            time.sleep(2)
            
    except ImportError:
        print("RPi.GPIO not available - running in mock mode")
        print("Install on Raspberry Pi for real sensor testing")
        
        # Mock test
        sensor = RadiationSensor(pin=18)
        for i in range(10):
            mock_reading = sensor.get_mock_reading(0, 0)
            print(f"Mock reading {i+1}: {mock_reading:.1f} CPM")
            time.sleep(1)
            
    except Exception as e:
        print(f"Error: {e}")
        print("Check wiring and connections!")

if __name__ == "__main__":
    main()