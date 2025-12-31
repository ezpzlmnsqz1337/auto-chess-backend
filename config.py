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

# Maximum positions (in steps)
# These define the limits of movement after homing
MAX_X_POSITION = 5000  # Adjust based on your actual carriage range
MAX_Y_POSITION = 5000  # Adjust based on your actual carriage range

# Step timing
# Pulse duration in seconds (default: 1ms)
STEP_PULSE_DURATION = 0.001

# Delay between steps in seconds (adjust for speed, lower = faster)
# Default is 0.002s (500 steps/second)
# Note: Keep below 2000 steps/second (~0.0005s delay) for StealthChop to remain active
STEP_DELAY = 0.002

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
