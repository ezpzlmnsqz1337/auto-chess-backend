"""
Configuration for the stepper motor control system.
"""

# GPIO Pin Configuration
# Motor X (horizontal axis)
MOTOR_X_STEP_PIN = 17
MOTOR_X_DIR_PIN = 15  # Changed from 18 (now used for LEDs)
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

# Capture area configuration
# Each side has a 2x8 area for captured pieces, offset from main board
CAPTURE_COLS = 2
CAPTURE_ROWS = 8
CAPTURE_OFFSET_MM = 24.0  # Gap between main board and capture area

# Total board dimensions including capture areas
TOTAL_COLS = CAPTURE_COLS + BOARD_COLS + CAPTURE_COLS  # 2 + 8 + 2 = 12
TOTAL_ROWS = BOARD_ROWS  # 8

# Calculate positions (in millimeters from board origin at a1)
LEFT_CAPTURE_START_MM = -(CAPTURE_COLS * SQUARE_SIZE_MM + CAPTURE_OFFSET_MM)
MAIN_BOARD_START_MM = 0.0
RIGHT_CAPTURE_START_MM = BOARD_COLS * SQUARE_SIZE_MM + CAPTURE_OFFSET_MM

# Total width and height in millimeters
TOTAL_WIDTH_MM = (
    CAPTURE_COLS * SQUARE_SIZE_MM  # Left capture area
    + CAPTURE_OFFSET_MM  # Left gap
    + BOARD_COLS * SQUARE_SIZE_MM  # Main board
    + CAPTURE_OFFSET_MM  # Right gap
    + CAPTURE_COLS * SQUARE_SIZE_MM  # Right capture area
)
TOTAL_HEIGHT_MM = BOARD_ROWS * SQUARE_SIZE_MM

# Steps per millimeter (calibrate based on your mechanical setup)
# GT2 belt: With 16x microstepping, 200 steps/rev motor, and 20-tooth pulley (40mm/rev):
# Steps per mm = (200 * 16) / 40 = 80 steps/mm
# Lead screw: With 16x microstepping, 200 steps/rev motor, and 20mm/rev lead screw:
# Steps per mm = (200 * 16) / 20 = 160 steps/mm
STEPS_PER_MM = 80.0  # GT2 belt with 20-tooth pulley

# Motor coordinate offset
# Motor homes at far left edge (before left capture area)
# This offset converts board coordinates (where a1=0) to motor coordinates (where home=0)
# Motor position 0 = homed position at far left
# Motor position MOTOR_X_OFFSET_STEPS = board coordinate x=0 (a1)
MOTOR_X_OFFSET_MM = abs(LEFT_CAPTURE_START_MM) + 10.0  # Capture area width + gap + margin
MOTOR_X_OFFSET_STEPS = int(MOTOR_X_OFFSET_MM * STEPS_PER_MM)

# Calculate board dimensions in steps
BOARD_WIDTH_STEPS = int(BOARD_COLS * SQUARE_SIZE_MM * STEPS_PER_MM)
BOARD_HEIGHT_STEPS = int(BOARD_ROWS * SQUARE_SIZE_MM * STEPS_PER_MM)

# Calculate extended dimensions in steps (including capture areas)
LEFT_CAPTURE_START_STEPS = int(LEFT_CAPTURE_START_MM * STEPS_PER_MM)
RIGHT_CAPTURE_END_STEPS = int(
    (RIGHT_CAPTURE_START_MM + CAPTURE_COLS * SQUARE_SIZE_MM) * STEPS_PER_MM
)
TOTAL_WIDTH_STEPS = int(TOTAL_WIDTH_MM * STEPS_PER_MM)
TOTAL_HEIGHT_STEPS = int(TOTAL_HEIGHT_MM * STEPS_PER_MM)

# Maximum positions (in steps)
# These define the limits of movement after homing
# X-axis must accommodate left capture area (negative) and right capture area
# Homing position is at left edge, before left capture area
MAX_X_POSITION = RIGHT_CAPTURE_END_STEPS + 1000  # Right capture area + margin
MAX_Y_POSITION = TOTAL_HEIGHT_STEPS + 1000  # Board height + margin

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
# WS2812B LED Configuration
# 96 individually addressable RGB LEDs for visual feedback
# - LEDs 0-15: Left capture area (2 columns × 8 rows)
# - LEDs 16-79: Main chess board (8 columns × 8 rows)
# - LEDs 80-95: Right capture area (2 columns × 8 rows)

# GPIO pin for LED data signal (must support hardware PWM)
# GPIO 18 is PWM0 - required for precise WS2812B timing
LED_DATA_PIN = 18  # Hardware PWM0

# Number of LEDs in the strip
LED_COUNT = 96  # 2×8 (left) + 8×8 (main) + 2×8 (right) = 96 total

# LED brightness (0-255)
# 255 = full brightness (15W power consumption)
# 128 = half brightness (4W)
# 64 = quarter brightness (1W)
# Start low to avoid power issues
LED_BRIGHTNESS = 64  # Quarter brightness, adjust based on power supply

# LED strip frequency (Hz)
# WS2812B uses 800kHz timing, library handles this
LED_FREQ_HZ = 800000  # Do not change

# LED DMA channel (for hardware PWM)
# Use channel 10 (safe, not used by audio)
LED_DMA = 10

# LED invert signal (usually False for WS2812B)
LED_INVERT = False

# LED channel (0 for GPIO 18/PWM0)
LED_CHANNEL = 0


# Color scheme for different board states (RGB tuples)
class LEDColors:
    """Predefined colors for LED feedback."""

    # Basic colors
    OFF = (0, 0, 0)  # No light
    WHITE = (255, 255, 255)  # Full white
    BLACK_DIM = (10, 10, 10)  # Dim white for black pieces

    # Player colors (whose turn)
    WHITE_PLAYER = (240, 240, 200)  # Warm white for white's turn
    BLACK_PLAYER = (180, 180, 220)  # Cool white for black's turn

    # Move feedback
    VALID_MOVE = (0, 100, 0)  # Green for legal moves
    VALID_CAPTURE = (100, 50, 0)  # Orange for captures
    INVALID_MOVE = (100, 0, 0)  # Red for illegal moves
    SELECTED = (0, 50, 100)  # Blue for selected piece

    # Game states
    CHECK = (150, 0, 0)  # Bright red for check
    CHECKMATE = (200, 0, 0)  # Very bright red for checkmate
    STALEMATE = (100, 100, 0)  # Yellow for stalemate

    # Special
    LAST_MOVE_FROM = (50, 30, 0)  # Dim orange for last move start
    LAST_MOVE_TO = (50, 50, 0)  # Dim yellow for last move end
