# Cajoe Radiation Detector D-v1.1 Wiring Guide

## ⚠️ IMPORTANT SAFETY WARNING
The Cajoe D-v1.1 contains HIGH VOLTAGE (~500V) across the Geiger tube. Handle with extreme care!

## Hardware Requirements
- Cajoe Radiation Detector D-v1.1 with J305ß Geiger tube
- Voltage divider resistors (10kΩ and 20kΩ) OR logic level converter
- Breadboard and jumper wires
- Raspberry Pi (already in your Picrawler)

## Pin Connections on Cajoe D-v1.1

| Cajoe Pin | Function | Notes |
|-----------|----------|-------|
| VCC | +5V Power | Connect to Pi 5V |
| GND | Ground | Connect to Pi GND |
| VIN | Signal Output | **This is the pulse output pin** (confusing label!) |

## Direct Connection (Standard Setup)

Since the Cajoe module is powered by Pi 5V, it's designed for Pi compatibility:

```
Cajoe VCC ---- Pi 5V (Pin 2)
Cajoe GND ---- Pi GND (Pin 6)  
Cajoe VIN ---- Pi GPIO18 (Pin 12)
```

That's it! No voltage dividers or level converters needed.

## Raspberry Pi Connections

| Pi Pin | Pi GPIO | Function |
|--------|---------|----------|
| 2 | 5V | Power for Cajoe |
| 6 | GND | Ground |
| 12 | GPIO18 | Signal input (via voltage divider) |

## Expected Behavior
- **Background radiation**: ~15-30 CPM
- **With radioactive source**: 100+ CPM
- **Pulse detection**: Rising edge on GPIO18
- **Tube sensitivity**: 65 cps/(μR/s) for gamma radiation

## Testing Commands

### 1. Basic sensor test:
```bash
python3 -c "
from radiation_bot import RadiationSensor
import time
sensor = RadiationSensor(pin=18)
for i in range(10):
    print(f'CPM: {sensor.get_reading():.1f}')
    time.sleep(2)
"
```

### 2. Interactive control:
```bash
python3 radiation_control.py
# Press 'r' to take readings
```

### 3. Full demo:
```bash
python3 radiation_bot.py
```

## Troubleshooting

### No pulses detected:
1. Check voltage divider wiring
2. Verify 5V power to Cajoe
3. Test with multimeter on VIN pin
4. Try different GPIO pin

### Erratic readings:
1. Add 100nF capacitor across GPIO and GND
2. Use shielded cable for VIN connection
3. Increase `bouncetime` in GPIO setup

### High background:
1. Normal for uncalibrated detector
2. J305ß tubes vary significantly
3. Use relative readings for source detection

## Demo Tips
- Allow 2-3 minutes for stable readings
- Use radioactive source 10-20cm from detector
- Background: ~20 CPM, Source: 100+ CPM
- Move source around to test gradient detection