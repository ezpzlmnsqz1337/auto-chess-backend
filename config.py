"""
Configuration for the stepper motor control system.
"""

# GPIO Pin Configuration
# Motor X (horizontal axis)
MOTOR_X_STEP_PIN = 17
MOTOR_X_DIR_PIN = 18

# Motor Y (vertical axis)
MOTOR_Y_STEP_PIN = 27
MOTOR_Y_DIR_PIN = 22

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
# Example: With 16x microstepping, 200 steps/rev motor, and 20mm/rev lead screw:
# Steps per mm = (200 * 16) / 20 = 160 steps/mm
STEPS_PER_MM = 160.0  # Adjust based on your pulley/belt/leadscrew setup

# Calculate board dimensions in steps
BOARD_WIDTH_STEPS = int(BOARD_COLS * SQUARE_SIZE_MM * STEPS_PER_MM)
BOARD_HEIGHT_STEPS = int(BOARD_ROWS * SQUARE_SIZE_MM * STEPS_PER_MM)

# Maximum positions (in steps)
# These define the limits of movement after homing
# Should be larger than board dimensions to allow margin
MAX_X_POSITION = max(5000, BOARD_WIDTH_STEPS + 1000)  # Board width + margin
MAX_Y_POSITION = max(5000, BOARD_HEIGHT_STEPS + 1000)  # Board height + margin

# Step timing
# Pulse duration in seconds (default: 1ms)
STEP_PULSE_DURATION = 0.001

# Delay between steps in seconds (adjust for speed, lower = faster)
# Default is 0.002s (500 steps/second)
# Note: Keep below 2000 steps/second (~0.0005s delay) for StealthChop to remain active
STEP_DELAY = 0.002

# Acceleration Configuration
# Enable/disable acceleration (set to False for constant speed)
ENABLE_ACCELERATION = True

# Minimum step delay (maximum speed) in seconds
# Must be > 0.0005s to maintain StealthChop operation
MIN_STEP_DELAY = 0.0008  # ~1250 steps/second max speed

# Maximum step delay (starting/ending speed) in seconds
MAX_STEP_DELAY = 0.004  # ~250 steps/second starting speed

# Acceleration steps - number of steps to ramp up/down
# Larger value = smoother but slower acceleration
# Recommended: 200-500 for mechanical systems (chess board)
# 200 steps = ~0.5s ramp, 300 steps = ~0.7s ramp, 500 steps = ~1.2s ramp
ACCELERATION_STEPS = 300

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
