#!/usr/bin/env python3
"""
Interactive Radiation Bot Controller
Manual control and testing interface for radiation detection spider bot
"""

from radiation_bot import RadiationBot
import readchar
import time

def print_menu():
    print("\n=== RADIATION BOT CONTROLLER ===")
    print("Movement Controls:")
    print("  w/s - Forward/Backward")
    print("  a/d - Turn Left/Right")
    print("  q/e - Stand/Sit")
    print()
    print("Radiation Controls:")
    print("  r - Take radiation reading")
    print("  g - Start grid exploration")
    print("  f - Find radiation source")
    print("  h - Generate heatmap")
    print("  v - Save data")
    print()
    print("Demo & Info:")
    print("  SPACE - Full demo mode")
    print("  i - Show current info")
    print("  ESC - Quit")
    print("=====================================")

def main():
    print("Initializing Radiation Bot...")
    bot = RadiationBot()
    
    print_menu()
    
    try:
        while True:
            print(f"\nPosition: {bot.tracker.get_position()}")
            print("Command: ", end="", flush=True)
            
            key = readchar.readchar()
            
            if key == '\x1b':  # ESC
                break
            elif key == 'w':
                bot.move_and_track('forward', 2, 60)
            elif key == 's':
                bot.move_and_track('backward', 2, 60)
            elif key == 'a':
                bot.move_and_track('turn left', 1, 60)
            elif key == 'd':
                bot.move_and_track('turn right', 1, 60)
            elif key == 'q':
                bot.do_action('stand', 1, 80)
            elif key == 'e':
                bot.do_action('sit', 1, 80)
            elif key == 'r':
                radiation = bot.collect_radiation_sample(3)
                print(f"Radiation reading: {radiation:.1f} CPM")
            elif key == 'g':
                print("Starting grid exploration...")
                bot.explore_grid(grid_size=3, step_distance=2)
            elif key == 'f':
                print("Starting source detection...")
                bot.find_radiation_source(max_steps=10)
            elif key == 'h':
                bot.generate_heatmap()
            elif key == 'v':
                bot.save_data()
            elif key == ' ':
                print("Starting full demo...")
                bot.demo_mode()
            elif key == 'i':
                pos = bot.tracker.get_position()
                print(f"Position: ({pos[0]:.1f}, {pos[1]:.1f}), Heading: {pos[2]:.0f}°")
                print(f"Samples collected: {len(bot.radiation_data)}")
                if bot.max_radiation > 0:
                    print(f"Max radiation: {bot.max_radiation:.1f} CPM at {bot.max_radiation_pos}")
            elif key == '?':
                print_menu()
            else:
                print(f"Unknown command: {key}. Press '?' for help.")
                
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        bot.do_action('sit', 1, 80)
        print("Bot safely parked. Goodbye!")

if __name__ == "__main__":
    main()