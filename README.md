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
- **64× Reed switches** - 2×14mm N/O (Normally Open) magnetic switches for piece detection
- **4× CD74HC4067** - 16-channel analog/digital multiplexers for reading reed switches
- **64× Pull-down resistors** - 10kΩ resistors for reed switch inputs (optional - can use Pi internal pull-downs)

## Hardware Connections

### GPIO Pins

| Function | GPIO Pin |
|----------|----------|
| Motor X - Step | GPIO 17 |
| Motor X - Direction | GPIO 18 |
| Motor X - Enable | GPIO 5 |
| Motor Y - Step | GPIO 27 |
| Motor Y - Direction | GPIO 22 |
| Motor Y - Enable | GPIO 6 |
| Motor X - Home Switch | GPIO 23 |
| Motor Y - Home Switch | GPIO 24 |
| Electromagnet Control | GPIO 25 |

### Reed Switch Multiplexer Pins

For piece detection using 64 reed switches connected via 4× CD74HC4067 multiplexers:

| Function | GPIO Pin |
|----------|----------|
| Mux Address S0 | GPIO 12 |
| Mux Address S1 | GPIO 16 |
| Mux Address S2 | GPIO 20 |
| Mux Address S3 | GPIO 21 |
| Mux 1 Signal (a1-h1, a2-h2) | GPIO 13 |
| Mux 2 Signal (a3-h3, a4-h4) | GPIO 19 |
| Mux 3 Signal (a5-h5, a6-h6) | GPIO 26 |
| Mux 4 Signal (a7-h7, a8-h8) | GPIO 4 |

**Note**: You need **4 multiplexers** to cover all 64 squares (not 2). Each CD74HC4067 handles 16 channels.

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

### Reed Switch Multiplexer Wiring

Each chess square has a reed switch underneath that closes when a magnetic chess piece is placed on top.

**CD74HC4067 Multiplexer Connections**:
```
CD74HC4067 → Raspberry Pi / Reed Switches
  VCC  → 3.3V (logic power from Pi - MUST be 3.3V, NOT 5V!)
  GND  → GND
  SIG  → GPIO (13, 19, 26, or 4 depending on multiplexer)
  S0   → GPIO 12 (shared across all 4 multiplexers)
  S1   → GPIO 16 (shared across all 4 multiplexers)
  S2   → GPIO 20 (shared across all 4 multiplexers)
  S3   → GPIO 21 (shared across all 4 multiplexers)
  EN   → GND (always enabled)
  C0-C15 → Reed switches (one side to channel, other side to 3.3V)
```

**⚠️ CRITICAL: Use 3.3V, NOT 5V!**
- Raspberry Pi GPIO pins are **NOT 5V tolerant**
- Using 5V will **damage or destroy your Pi**
- Always use 3.3V from Pi pin 1 or pin 17

**Reed Switch Wiring (per switch)**:
```
3.3V (Pi pin 1/17) → Reed Switch (one terminal)
Reed Switch (other terminal) → CD74HC4067 channel (C0-C15)

Optional: 10kΩ resistor from channel to GND (pull-down)
Note: External resistors not required - Pi has internal pull-downs enabled in software
```

**Square to Multiplexer Mapping**:
- **Mux 1 (GPIO 13)**: Squares a1-h1 (channels 0-7), a2-h2 (channels 8-15)
- **Mux 2 (GPIO 19)**: Squares a3-h3 (channels 0-7), a4-h4 (channels 8-15)
- **Mux 3 (GPIO 26)**: Squares a5-h5 (channels 0-7), a6-h6 (channels 8-15)
- **Mux 4 (GPIO 4)**: Squares a7-h7 (channels 0-7), a8-h8 (channels 8-15)

**How it works**:
1. The 4 address pins (S0-S3) select which of the 16 channels to read (shared across all muxes)
2. Each multiplexer's SIG pin is read individually to get that square's state
3. System scans all 64 squares sequentially by iterating through 0-15 on address pins
4. When a magnetic piece is on a square, the reed switch closes, pulling the channel HIGH
5. Can detect piece placement, removal, and track all moves made by human players

### TMC2208 Stepper Driver Configuration

**Connection (Standalone Mode)**:
```
TMC2208 → Raspberry Pi / Motor
  VDD  → 3.3V or 5V (logic power)
  GND  → GND
  STEP → GPIO (17 for X, 27 for Y)
  DIR  → GPIO (18 for X, 22 for Y)
  EN   → GPIO (5 for X, 6 for Y) - LOW=enabled, HIGH=disabled
  VM   → Motor power supply (12-24V)
  GND  → Motor power GND
  A1, A2, B1, B2 → Stepper motor coils
```

**Microstepping Configuration (MS1/MS2 Pins)**:

For **quiet operation with 16× microstepping** (recommended):

| MS1 | MS2 | Microstepping | Interpolation | Steps/Revolution (1.8° motor) |
|-----|-----|---------------|---------------|-------------------------------|
| VDD | VDD | 1/16          | 1/256         | 3200                          |

Other microstepping options (all with 1/256 interpolation in stealthChop2):

| MS1 | MS2 | Microstepping | Steps/Revolution |
|-----|-----|---------------|------------------|
| GND | GND | 1/8           | 1600             |
| GND | VDD | 1/2           | 400              |
| VDD | GND | 1/4           | 800              |

**StealthChop (Silent Operation)**:
- **Enabled by default** in standalone mode
- Active when step frequency < ~35,000 steps/second
- Current config (STEP_DELAY=0.002s → 500 Hz) keeps StealthChop active ✓
- No UART connection needed for basic StealthChop
- Provides extremely quiet operation ideal for chess piece movement

**Physical Setup**:
1. Add small heatsink to TMC2208 chip
2. Set MS1=VDD, MS2=VDD for 16× microstepping (solder jumpers or via pins)
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
cd ~/workspace/auto-chess-backend
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

**GPIO Pins**:
- `MOTOR_X_STEP_PIN`, `MOTOR_X_DIR_PIN`, `MOTOR_Y_STEP_PIN`, `MOTOR_Y_DIR_PIN`
- `MOTOR_X_HOME_PIN`, `MOTOR_Y_HOME_PIN`, `ELECTROMAGNET_PIN`

**Chess Board Configuration**:
- `SQUARE_SIZE_MM` - Size of each chess square in millimeters (default: 31mm)
- `BOARD_ROWS`, `BOARD_COLS` - Board dimensions (default: 8×8 for standard chess)
- `STEPS_PER_MM` - Motor steps per millimeter (calibrate based on your setup)
- `BOARD_WIDTH_STEPS`, `BOARD_HEIGHT_STEPS` - Auto-calculated board dimensions

**Motor Settings**:
- `MOTOR_X_INVERT`, `MOTOR_Y_INVERT` - Set to `True` if motor spins opposite direction
- `MAX_X_POSITION`, `MAX_Y_POSITION` - Auto-sized to fit board + margin
- `STEP_DELAY` - Base delay between steps (used when acceleration disabled)

**Acceleration Settings** ✨:
- `ENABLE_ACCELERATION` - Enable trapezoidal acceleration profile (`True` recommended)
- `MIN_STEP_DELAY` - Minimum delay (maximum speed) - default `0.0008s` = 1250 steps/second
- `MAX_STEP_DELAY` - Maximum delay (starting/ending speed) - default `0.004s` = 250 steps/second
- `ACCELERATION_STEPS` - Number of steps for ramp up/down - default `300` steps

**Homing**:
- `HOME_DIRECTION_X`, `HOME_DIRECTION_Y` - Direction to move during homing (0 or 1)
- `HOME_STEP_DELAY` - Slower speed for safe homing

**Electromagnet**:
- `ELECTROMAGNET_ACTIVE_HIGH` - `True` for NPN transistor/MOSFET, `False` for active-low relay

**Reed Switch Configuration**:
- `MUX_S0_PIN`, `MUX_S1_PIN`, `MUX_S2_PIN`, `MUX_S3_PIN` - Multiplexer address pins (shared)
- `MUX_SIG_PINS` - List of 4 signal pins, one per multiplexer
- `REED_SWITCH_SCAN_RATE` - Scans per second (10-50 Hz recommended)
- `REED_SWITCH_DEBOUNCE_TIME` - Debounce time in seconds (0.1s default)
- `MOVE_DETECTION_TIMEOUT` - Max time to wait for move completion (30s default)

**Acceleration Benefits**:
- **Prevents missed steps** by starting slow
- **Smoother movement** with gradual speed changes
- **Reduced mechanical stress** on motors and carriage
- **Quieter operation** with less vibration
- **Faster overall** due to higher maximum speed (1250 steps/s vs 500 steps/s constant)

## Usage

### Command Line Interface

```bash
# Home all motors (must do this first!)
python main.py home

# Demo mode - Execute calibration patterns (automatically homes first)
python main.py demo                    # Run all patterns (square, diagonals, snake)
python main.py demo --pattern square   # Just the board perimeter
python main.py demo --pattern diagonals # Just the 4 major diagonals
python main.py demo --pattern snake    # Just the snake pattern (all 64 squares)
python main.py demo --no-home          # Skip auto-homing if already homed

# Move to absolute position (in steps)
python main.py move 1000 2000

# Move relative to current position
python main.py move-rel --dx 100 --dy -50

# Chess board navigation (via Python API)
from board_navigation import square_to_steps, chess_notation_to_steps
from motor_controller import MotorController

# Move to e4 square using chess notation
x, y = chess_notation_to_steps('e4')
controller.move_to(x, y)

# Or use row/column (0-indexed, 0=bottom-left)
x, y = square_to_steps(row=3, col=4)  # Same as e4
controller.move_to(x, y)

# Electromagnet control
python main.py magnet-on       # Turn magnet on
python main.py magnet-off      # Turn magnet off
python main.py magnet-toggle   # Toggle magnet state

# Motor control
python main.py motor-enable    # Enable motors (allows movement)
python main.py motor-disable   # Disable motors (saves power, manual movement allowed)

# Reed switch commands (piece detection)
python main.py reed-scan               # Single scan - show all occupied squares
python main.py reed-scan --continuous  # Continuous monitoring (Ctrl+C to stop)
python main.py reed-wait-move          # Wait for human player to make a move
python main.py reed-test e4            # Test a specific square's sensor

# Get current position
python main.py position

# Get detailed motor and magnet status
python main.py status

# Emergency stop (also turns off magnet)
python main.py stop
```

## Testing

### Board Navigation Tests

Run the test suite to validate chess board navigation and generate visualizations:

```bash
# Run all tests
pytest tests/test_board_navigation.py -v

# Run specific test
pytest tests/test_board_navigation.py::test_snake_pattern_all_squares -v
```

**Generated Visualizations** (in `tests/output/`):
- `edge_square.png` - Board perimeter movement
- `all_diagonals.png` - Four major diagonal paths
- `snake_pattern.png` - Complete 64-square coverage

**Test Coverage**:
- Board edge navigation
- Diagonal movements (all 4 directions)
- Snake pattern through all squares
- Configuration validation

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

### Reed Switch API

Use the reed switch controller to detect piece positions:

```python
from reed_switch_controller import ReedSwitchController

# Create controller
reed = ReedSwitchController()

# Scan all 64 squares
board_state = reed.scan_with_debounce()  # Returns list of 64 booleans

# Get list of occupied squares
occupied = reed.get_occupied_squares()  # Returns [(row, col), ...]

# Read specific square
is_occupied = reed.read_square(row=3, col=4)  # e4 square

# Detect changes since last scan
added, removed = reed.detect_changes()
for row, col in added:
    print(f"Piece added at {chr(97 + col)}{row + 1}")

# Wait for human player move
result = reed.wait_for_move(timeout=30.0)
if result:
    from_square, to_square = result
    print(f"Move: {from_square} -> {to_square}")

# Get visual board representation
print(reed.get_board_state_fen_like())

# Clean up
reed.close()
```

**Reed Switch Features**:
- **Automatic debouncing** to filter electrical noise
- **Real-time move detection** for human players
- **64-square coverage** using 4 multiplexers
- **Fast scanning** up to 50 Hz
- **Visual board display** showing occupied squares

## Key Features

- **Homing**: Automatic homing to limit switches
- **Position Tracking**: Maintains current position state
- **Absolute & Relative Movement**: Move to exact positions or by step increments
- **Coordinated Motion**: Bresenham's algorithm ensures straight diagonal paths
- **Per-Motor Acceleration**: Each motor uses independent acceleration profiles for optimal speed
- **Diagonal Speed Optimization**: 30% faster diagonal movements while maintaining straight paths
- **Trapezoidal Velocity Profiles**: Smooth acceleration and deceleration
- **Direction Control**: Easily invert motor directions via configuration
- **Safety Limits**: Prevents movement beyond max positions
- **Reed Switch Integration**: 64 magnetic sensors detect piece positions on every square
- **Human Move Detection**: Automatically detects when players pick up and place pieces
- **Real-time Board Monitoring**: Continuous scanning with debouncing for reliable detection
- **Error Handling**: Validates moves and provides detailed error messages
- **GPIO-free Simulation**: Works on non-Pi systems for development (limits switch not available)

## Project Structure

```
auto-chess-backend/
├── src/
│   ├── main.py                    # CLI interface
│   ├── config.py                  # Configuration constants
│   ├── board_navigation.py        # Chess coordinate conversion
│   ├── demo_patterns.py           # Calibration patterns
│   ├── reed_switch_controller.py  # Reed switch multiplexer control
│   └── motor/
│       ├── motor_controller.py    # Motor coordination
│       ├── stepper_motor.py       # Individual motor control
│       └── electromagnet.py       # Magnet control
├── tests/                         # Test suite
├── analysis/                      # Performance analysis
├── README.md                      # This file
├── AGENTS.md                      # Development notes
└── pyproject.toml                 # Project metadata
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
