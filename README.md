# Auto Chess Backend - XY Carriage Motor Controller

Control stepper motors to move an electromagnet under a chess board for automatic piece movement.

## Overview

This project uses a Raspberry Pi Zero 2W to control two NEMA stepper motors (X and Y axes) via TMC2208 drivers. The system supports homing to limit switches, absolute positioning, and relative movement.

## Hardware Requirements

- **Raspberry Pi Zero 2W** - Main controller
- **2× NEMA stepper motors** - For X and Y axes
- **2× TMC2208 stepper drivers** - Motor controllers (standalone mode)
- **Limit switches** - For homing on each axis
- **Electromagnet** - P20/15 24V 3kg (with MOSFET or relay module)
- **MOSFET** - IRLZ44N or similar logic-level MOSFET, or 5V relay module
- **Diode** - 1N5408 (3A, 1000V) flyback protection
- **Power supply** - 24V 2A+ rated for motors, electromagnet, and Pi
- **Resistors** - 4.7kΩ pulldown resistors for step pins (optional), 10kΩ for MOSFET gate

## Hardware Connections

### GPIO Pins

| Function | GPIO Pin |
|----------|----------|
| Motor X - Step | GPIO 17 |
| Motor X - Direction | GPIO 18 |
| Motor Y - Step | GPIO 27 |
| Motor Y - Direction | GPIO 22 |
| Motor X - Home Switch | GPIO 23 |
| Motor Y - Home Switch | GPIO 24 |
| Electromagnet Control | GPIO 25 |

Configure limit switches with pullup resistors to GPIO pins. The system detects home position when the pin reads LOW.

### Electromagnet Wiring

**Electromagnet Specs**: P20/15 (20mm diameter, 15mm height), 24V, 3kg holding force, ~0.3-0.8A

**Option 1: MOSFET Module (Recommended for 24V)**
```
GPIO 25 → 10kΩ resistor → MOSFET Gate (IRLZ44N or similar logic-level MOSFET)
MOSFET Drain → Electromagnet (-)
MOSFET Source → GND
Electromagnet (+) → 24V power supply (+)
24V power supply (-) → GND (common with Pi GND)
1N5408 flyback diode across electromagnet (cathode to +, anode to -)
```

**Option 2: 5V Relay Module (Easiest)**
```
GPIO 25 → Relay Module IN
Relay Module VCC → 5V from Pi
Relay Module GND → GND
Relay COM → 24V power supply (+)
Relay NO → Electromagnet (+)
Electromagnet (-) → 24V power supply (-)
1N5408 flyback diode across electromagnet (cathode to +, anode to -)
```

**Parts List**:
- **MOSFET**: IRLZ44N (logic-level, 50V, 30A) or equivalent
- **Diode**: 1N5408 (3A, 1000V) for flyback protection
- **Resistor**: 10kΩ for MOSFET gate
- **Power Supply**: 24V 2A+ (for electromagnet + stepper motors)

**Critical**: The 1N5408 diode **must** be placed directly across the electromagnet coil (cathode/stripe to +, anode to -) to protect against inductive voltage spikes when switching off.

### TMC2208 Stepper Driver Configuration

**Connection (Standalone Mode)**:
```
TMC2208 → Raspberry Pi / Motor
  VDD  → 3.3V or 5V (logic power)
  GND  → GND
  STEP → GPIO (17 for X, 27 for Y)
  DIR  → GPIO (18 for X, 22 for Y)
  EN   → GND (always enabled) or GPIO for enable/disable
  VM   → Motor power supply (12-24V)
  GND  → Motor power GND
  A1, A2, B1, B2 → Stepper motor coils
```

**Microstepping Configuration (MS1/MS2 Pins)**:

For **quiet operation with 16× microstepping** (recommended):

| MS1 | MS2 | Microstepping | Steps/Revolution (1.8° motor) |
|-----|-----|---------------|-------------------------------|
| GND | VDD | 16            | 3200                          |

Other microstepping options:

| MS1 | MS2 | Microstepping | Steps/Revolution |
|-----|-----|---------------|------------------|
| GND | GND | 8             | 1600             |
| VDD | GND | 4             | 800              |
| VDD | VDD | 2             | 400              |
| Open| Open| 1/2 (default) | 400              |

**StealthChop (Silent Operation)**:
- **Enabled by default** in standalone mode
- Active when step frequency < ~35,000 steps/second
- Current config (STEP_DELAY=0.002s → 500 Hz) keeps StealthChop active ✓
- No UART connection needed for basic StealthChop
- Provides extremely quiet operation ideal for chess piece movement

**Physical Setup**:
1. Add small heatsink to TMC2208 chip
2. Set MS1=GND, MS2=VDD for 16× microstepping (solder jumpers or via pins)
3. Adjust motor current via VREF potentiometer:
   - VREF = Motor_Current × 0.5 (for standalone mode)
   - Example: For 1A motor, set VREF to 0.5V
4. Use multimeter to measure VREF on the potentiometer

**Wiring for Common Ground**:
- TMC2208 GND, Motor PSU GND, and Raspberry Pi GND **must** be connected together

## Installation

### Setup Python Environment

```bash
# Initialize project (already done)
cd /home/mazel/workspace/auto-chess-backend
uv sync

# Activate virtual environment
source .venv/bin/activate
```

### Install Dependencies

```bash
# Install production dependencies
uv sync

# Install development dependencies (ruff, mypy)
uv sync --extra dev
```

## Configuration

Edit [config.py](config.py) to customize:

- **GPIO Pins**: `MOTOR_X_STEP_PIN`, `MOTOR_X_DIR_PIN`, `MOTOR_Y_STEP_PIN`, `MOTOR_Y_DIR_PIN`, `MOTOR_X_HOME_PIN`, `MOTOR_Y_HOME_PIN`, `ELECTROMAGNET_PIN`
- **Direction Inversion**: `MOTOR_X_INVERT`, `MOTOR_Y_INVERT` - Set to `True` if motor spins opposite direction
- **Max Positions**: `MAX_X_POSITION`, `MAX_Y_POSITION` - Define carriage limits in steps
- **Speed**: `STEP_DELAY` - Delay between steps (lower = faster)
- **Homing**: `HOME_DIRECTION_X`, `HOME_DIRECTION_Y` - Direction to move during homing
- **Homing Speed**: `HOME_STEP_DELAY` - Slower speed for safe homing
- **Electromagnet**: `ELECTROMAGNET_ACTIVE_HIGH` - `True` for NPN transistor, `False` for active-low relay

## Usage

### Command Line Interface

```bash
# Home all motors (must do this first!)
python main.py home

# Move to absolute position
python main.py move 1000 2000

# Move relative to current position
python main.py move-rel --dx 100 --dy -50

# Electromagnet control
python main.py magnet-on       # Turn magnet on
python main.py magnet-off      # Turn magnet off
python main.py magnet-toggle   # Toggle magnet state

# Get current position
python main.py position

# Get detailed motor and magnet status
python main.py status

# Emergency stop (also turns off magnet)
python main.py stop
```

### Interactive Mode

```bash
python main.py interactive

# Commands:
# home              - Home all motors
# pos               - Show current position
# move X Y          - Move to absolute position
# movex STEPS       - Move X axis relative
# movey STEPS       - Move Y axis relative
# magnet on         - Turn electromagnet on
# magnet off        - Turn electromagnet off
# magnet toggle     - Toggle electromagnet
# status            - Show motor and magnet status
# stop              - Emergency stop
# help              - Show help
# exit              - Exit
```

## API Usage

Use the motor controller directly in Python:

```python
from motor_controller import StepperMotor, MotorController
import config

# Create motors
motor_x = StepperMotor(
    step_pin=config.MOTOR_X_STEP_PIN,
    dir_pin=config.MOTOR_X_DIR_PIN,
    home_pin=config.MOTOR_X_HOME_PIN,
    invert_direction=config.MOTOR_X_INVERT,
    max_position=config.MAX_X_POSITION,
    step_delay=config.STEP_DELAY,
)

motor_y = StepperMotor(
    step_pin=config.MOTOR_Y_STEP_PIN,
    dir_pin=config.MOTOR_Y_DIR_PIN,
    home_pin=config.MOTOR_Y_HOME_PIN,
    invert_direction=config.MOTOR_Y_INVERT,
    max_position=config.MAX_Y_POSITION,
    step_delay=config.STEP_DELAY,
)

# Create controller
controller = MotorController(motor_x, motor_y)

# Home motors
controller.home_all(
    home_direction_x=config.HOME_DIRECTION_X,
    home_direction_y=config.HOME_DIRECTION_Y,
)

# Move to position
controller.move_to(x=1000, y=2000)

# Get position
x, y = controller.get_position()
print(f"Current position: X={x}, Y={y}")

# Get status
status = controller.get_status()

# Emergency stop
controller.emergency_stop()
```

## Key Features

- **Homing**: Automatic homing to limit switches
- **Position Tracking**: Maintains current position state
- **Absolute & Relative Movement**: Move to exact positions or by step increments
- **Direction Control**: Easily invert motor directions via configuration
- **Safety Limits**: Prevents movement beyond max positions
- **Error Handling**: Validates moves and provides detailed error messages
- **GPIO-free Simulation**: Works on non-Pi systems for development (limits switch not available)

## Project Structure

```
auto-chess-backend/
├── main.py                 # CLI interface
├── motor_controller.py     # Motor control classes
├── config.py               # Configuration constants
├── README.md              # This file
├── AGENTS.md              # Development notes
└── pyproject.toml         # Project metadata
```

## Development

### Code Quality Tools

```bash
# Format code with ruff
uv run ruff format .

# Lint code with ruff
uv run ruff check .

# Fix auto-fixable lint issues
uv run ruff check --fix .

# Type check with mypy
uv run mypy .

# Run all checks before committing
uv run ruff format . && uv run ruff check --fix . && uv run mypy .
```

## Testing Without Hardware

The system gracefully handles missing GPIO:

- On non-Pi systems, homing succeeds without activating limit switches
- Motor movements are simulated without actual hardware
- Perfect for development and testing logic

## Performance

- **Step frequency**: Configurable via `STEP_DELAY` (default 500 Hz)
- **Microstepping**: Set via TMC2208 MS pins (default 16×)
- **Position accuracy**: Limited by stepper resolution and mechanical setup

## Troubleshooting

### Motor moves wrong direction
- Set `MOTOR_X_INVERT = True` or `MOTOR_Y_INVERT = True` in config.py

### Homing never completes
- Verify GPIO pins in config match your hardware
- Check limit switch wiring and connectivity
- Ensure pullup resistors on limit switch pins

### Movements are jerky
- Increase `STEP_DELAY` slightly (slower = more stable)
- Check power supply voltage and amperage

## License

This project is part of the Auto Chess system.
