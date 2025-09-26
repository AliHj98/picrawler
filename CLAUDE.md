# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Picrawler is a Python library for controlling a quadruped spider robot on Raspberry Pi. The robot uses 12 servos (3 per leg) and provides gait-based walking, preset actions, and interactive control capabilities.

## Core Architecture

### Main Components
- `picrawler/picrawler.py` - Main Picrawler class inheriting from robot_hat.Robot
- `picrawler/__init__.py` - Package exports and version
- `examples/` - Demonstration scripts showing robot capabilities
- `gpt_examples/` - GPT integration examples

### Key Dependencies
- `robot_hat>=2.0.0` - Hardware abstraction layer for servo control
- `readchar` - Keyboard input handling for interactive examples

### Robot Hardware Model
- 12 servos arranged in 4 legs (3 servos per leg)
- Coordinate system: [x, y, z] where default position is [60, 0, -30]
- Configuration file: `/opt/picrawler/picrawler.config` for servo offsets
- PIN_LIST: [9, 10, 11, 3, 4, 5, 0, 1, 2, 6, 7, 8] - servo pin mapping

## Development Commands

### Installation
```bash
git clone --depth 1 https://github.com/sunfounder/picrawler.git
cd picrawler
sudo python3 setup.py install
```

### Running Examples
```bash
# Basic movement demo
python3 examples/move.py

# Servo calibration (essential for proper operation)
python3 examples/calibration/calibration.py

# Keyboard control
python3 examples/keyboard_control.py

# Emotional behaviors
python3 examples/emotional_robot.py
```

## Core Classes and Methods

### Picrawler Class
- Inherits from `robot_hat.Robot`
- Key constants: A=48, B=78, C=33 (kinematic parameters)
- Coordinate conversion: `coord2polar()` - converts cartesian to servo angles
- Movement: `do_action()`, `do_step()` - execute predefined or custom movements
- Built-in actions: 'forward', 'backward', 'turn left', 'turn right', 'stand', 'sit'

### Important Files for Development
- `examples/calibration/calibration.py` - Servo calibration utility (run first)
- `examples/preset_actions.py` - Predefined movement sequences
- `examples/record_new_step_by_keyboard.py` - Tool for creating custom gaits

## Development Patterns

### Basic Robot Initialization
```python
from picrawler import Picrawler
crawler = Picrawler()
```

### Movement Control
- Actions use `do_action(action_name, steps, speed)` format
- Steps use `do_step(coordinate_list, speed)` format
- Coordinates are 4-element lists: [[x,y,z], [x,y,z], [x,y,z], [x,y,z]] for each leg

### Calibration Workflow
1. Run `examples/calibration/calibration.py` first
2. Manually adjust each servo to proper position
3. Save calibration to `/opt/picrawler/picrawler.config`
4. Test with basic movement examples

## Sound and Media Integration
- Audio files in `examples/sounds/` (.wav format)
- Music files in `examples/musics/` (.mp3 format)
- Video recording capability in `examples/record_video.py`

## GPT Integration
- `gpt_examples/` contains OpenAI integration for voice/AI control
- Requires API keys configuration in `gpt_examples/keys.py`