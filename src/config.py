"""
Configuration for the stepper motor control system.
"""

# GPIO Pin Configuration
# Motor X (horizontal axis)
MOTOR_X_STEP_PIN = 17
MOTOR_X_DIR_PIN = 18
MOTOR_X_ENABLE_PIN = 5  # LOW = enabled, HIGH = disabled

# Motor Y (vertical axis)
MOTOR_Y_STEP_PIN = 27
MOTOR_Y_DIR_PIN = 22
MOTOR_Y_ENABLE_PIN = 6  # LOW = enabled, HIGH = disabled

# Homing switch pins (connect to GPIO with pullup resistors)
# These should be connected to the limit switches on each axis
MOTOR_X_HOME_PIN = 23
MOTOR_Y_HOME_PIN = 24

# Direction inversion flags
# Set to True if motor moves in opposite direction than expected
MOTOR_X_INVERT = False
MOTOR_Y_INVERT = False

# Chess Board Configuration
# Square size in millimeters
SQUARE_SIZE_MM = 31.0  # Standard tournament size is 50-60mm, adjust to your board

# Board dimensions (standard chess board is 8x8)
BOARD_ROWS = 8
BOARD_COLS = 8

# Steps per millimeter (calibrate based on your mechanical setup)
# GT2 belt: With 16x microstepping, 200 steps/rev motor, and 20-tooth pulley (40mm/rev):
# Steps per mm = (200 * 16) / 40 = 80 steps/mm
# Lead screw: With 16x microstepping, 200 steps/rev motor, and 20mm/rev lead screw:
# Steps per mm = (200 * 16) / 20 = 160 steps/mm
STEPS_PER_MM = 80.0  # GT2 belt with 20-tooth pulley

# Calculate board dimensions in steps
BOARD_WIDTH_STEPS = int(BOARD_COLS * SQUARE_SIZE_MM * STEPS_PER_MM)
BOARD_HEIGHT_STEPS = int(BOARD_ROWS * SQUARE_SIZE_MM * STEPS_PER_MM)

# Maximum positions (in steps)
# These define the limits of movement after homing
# Should be larger than board dimensions to allow margin
MAX_X_POSITION = max(5000, BOARD_WIDTH_STEPS + 1000)  # Board width + margin
MAX_Y_POSITION = max(5000, BOARD_HEIGHT_STEPS + 1000)  # Board height + margin

# Step timing
# Pulse duration in seconds
# TMC2208 requires minimum 1-5 microseconds (per datasheet)
# Using 5 microseconds for reliability
STEP_PULSE_DURATION = 0.000005  # 5 microseconds

# Delay between steps in seconds (adjust for speed, lower = faster)
# Default is 0.002s (500 steps/second)
# Note: Keep below 2000 steps/second (~0.0005s delay) for StealthChop to remain active
STEP_DELAY = 0.002

# Acceleration Configuration
# Enable/disable acceleration (set to False for constant speed)
ENABLE_ACCELERATION = True

# Minimum step delay (maximum speed) in seconds
# StealthChop remains quiet up to ~10kHz
# 60mm/s = 4800 steps/s, 100mm/s = 8000 steps/s, 150mm/s = 12000 steps/s
MIN_STEP_DELAY = 0.000125  # 8000 steps/second = 100mm/s max speed

# Maximum step delay (starting/ending speed) in seconds
MAX_STEP_DELAY = 0.002  # 500 steps/second starting speed (faster ramp-up)

# Acceleration steps - number of steps to ramp up/down
# Larger value = smoother but slower acceleration
# Recommended: 200-500 for mechanical systems (chess board)
# 200 steps = ~0.5s ramp, 300 steps = ~0.7s ramp, 500 steps = ~1.2s ramp
ACCELERATION_STEPS = 200  # Reduced for quicker acceleration

# Microstepping Configuration (set via TMC2208 MS1/MS2 pins)
# 16x microstepping recommended for smooth, quiet operation
# See README.md for MS1/MS2 pin configuration table
MICROSTEPPING = 16  # Documentation only - set via hardware pins

# Homing configuration
# Speed during homing (delay between steps)
HOME_STEP_DELAY = 0.005  # Slower than normal speed for safety

# Direction of homing movement
# 0 = move towards negative (decreasing positions)
# 1 = move towards positive (increasing positions)
HOME_DIRECTION_X = 0
HOME_DIRECTION_Y = 0

# Electromagnet configuration
# GPIO pin to control electromagnet (via transistor/relay)
ELECTROMAGNET_PIN = 25

# Active high/low configuration
# True = magnet ON when GPIO is HIGH (default for NPN transistor)
# False = magnet ON when GPIO is LOW (for PNP or active-low relay)
ELECTROMAGNET_ACTIVE_HIGH = True

# Reed Switch Multiplexer Configuration
# 64 reed switches (one under each square) connected via 4× CD74HC4067 multiplexers
# Each multiplexer handles 16 channels (2 rows of the chess board)

# Multiplexer address pins (shared across all 4 multiplexers)
MUX_S0_PIN = 12  # Address bit 0
MUX_S1_PIN = 16  # Address bit 1
MUX_S2_PIN = 20  # Address bit 2
MUX_S3_PIN = 21  # Address bit 3

# Multiplexer signal pins (one per multiplexer)
MUX_SIG_PINS = [
    13,  # Mux 1: rows 1-2 (a1-h1, a2-h2)
    19,  # Mux 2: rows 3-4 (a3-h3, a4-h4)
    26,  # Mux 3: rows 5-6 (a5-h5, a6-h6)
    4,  # Mux 4: rows 7-8 (a7-h7, a8-h8)
]

# Reed switch scan rate (scans per second)
# Higher = more responsive but more CPU usage
# 10-50 Hz is usually sufficient for human moves
REED_SWITCH_SCAN_RATE = 20  # Hz

# Debounce settings
# Time to wait before confirming a piece placement/removal (seconds)
REED_SWITCH_DEBOUNCE_TIME = 0.1  # 100ms

# Move detection timeout
# Maximum time to wait for a move to complete (piece picked up then placed)
MOVE_DETECTION_TIMEOUT = 30.0  # 30 seconds
