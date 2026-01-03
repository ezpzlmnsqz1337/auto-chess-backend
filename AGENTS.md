# Development Notes - Auto Chess Backend

## Project Overview

This project implements an automated chess board with AI gameplay capabilities. The system features:
- **Interactive chess board**: 8×8 main playing area with LED feedback
- **Capture areas**: 2×8 squares on each side for captured pieces (24mm offset)
- **XY carriage system**: Stepper motors move electromagnet to drag pieces
- **Reed switches**: Detect piece presence on all 96 squares (main board + capture areas)
- **RGB LEDs**: Visual feedback for moves, captures, and game state (96 total)
- **Game modes**: AI vs AI, Player vs AI, Player vs Player

## Physical Layout

```
Looking from white's perspective (y-axis points up):

[Black Captures]  [Main Chess Board]  [White Captures]
   2×8 squares         8×8 squares         2×8 squares
   LEDs 0-15          LEDs 16-79          LEDs 80-95
   Columns -2,-1      Columns 0-7         Columns 8,9
        ↓ 24mm offset ↓              ↓ 24mm offset ↓
   
   Total width: ~536mm (2×40mm + 24mm + 248mm + 24mm + 2×40mm)
   Height: 248mm (8 squares)
   
   Board coordinate system: (0,0) at square a1 (main board bottom-left)
   - Left capture area uses negative board coordinates (columns -2, -1)
   - Main board uses coordinates 0-7 (a1 to h8)
   - Right capture area uses coordinates 8-9
   
   Motor coordinate system: After homing, motor position 0 = far left edge
   - Motor homes at left edge (before left capture area)
   - MOTOR_X_OFFSET = ~96mm added to convert board → motor coordinates
   - Example: board x=0 (a1) → motor x=7680 steps (96mm × 80 steps/mm)
   - All motor positions are positive after homing
```

## Core Components

**motor_controller.py**
- `StepperMotor`: Single stepper motor control with homing
  - GPIO step/direction control
  - Position tracking and limits
  - Limit switch homing
  - Direction inversion support
  
- `MotorController`: Dual-axis carriage controller
  - Manages X and Y motors together
  - Absolute and relative positioning
  - Status reporting

**config.py**
- Centralized configuration for all GPIO pins
- Extended board configuration:
  - Main chess board: 8×8 squares
  - Capture areas: 2×8 squares on each side (24mm offset)
  - Total: 96 squares with LEDs and reed switches
- Motor limits accommodate full extended range
- Tunable parameters: step speeds, limits, directions, acceleration
- Easy hardware reconfiguration without code changes

**board_navigation.py**
- Chess board coordinate conversions
- `square_to_steps(row, col)` - Main board coordinates to motor steps
- `chess_notation_to_steps('e4')` - Chess notation to motor steps
- `extended_square_to_steps(row, col)` - Extended board with capture areas
  - Handles negative columns (-2, -1) for left capture area
  - Handles columns 8, 9 for right capture area
  - Applies 24mm offset between main board and capture areas
- `steps_to_mm(x, y)` - Steps to millimeters conversion
- `steps_to_square(x, y)` - Motor steps to square coordinates (reverse conversion)
  - Handles main board (0-7) and capture areas (-2, -1, 8, 9)
- Board dimension queries (main and extended)

**main.py**
- CLI with subcommands for all operations
- Interactive mode for manual control
- Error handling and user feedback

**chess_game/** (Modular package)
- `player.py`: Player enum (WHITE/BLACK) with opposite() method
- `piece.py`: PieceType enum and Piece dataclass
- `square.py`: Square dataclass with chess notation conversion
- `game.py`: ChessGame class with full rule validation
  - All piece movement rules (pawn, knight, bishop, rook, queen, king)
  - Check and checkmate detection
  - Castling (kingside and queenside)
  - En passant capture
  - Pawn promotion
  - Move validation ensuring king safety

**piece_movement.py**
- `travel()` - Move to position with electromagnet OFF
- `move_piece()` - Move piece with magnet control and obstacle avoidance
- `move_piece_to_capture_area()` - Move captured pieces to capture area
- `_plan_capture_area_path()` - Greedy pathfinding for capture area navigation
  - Excludes starting square from obstacle checking
  - Detects when stuck on edge rows and enters capture area directly
  - Uses diagonal moves when possible to avoid obstacles
  - Switches between inner (-1/8) and outer (-2/9) capture columns as needed
  - Horizontal → Diagonal → Vertical strategy for obstacle avoidance

**capture_management.py**
- `get_next_capture_slot()` - Determines placement for captured pieces
  - Black pieces → LEFT capture area (columns -2, -1)
  - White pieces → RIGHT capture area (columns 8, 9)
  - Maintains chess piece layout (row 0: major pieces, row 1: pawns, row 2+: overflow)
- `CaptureAreaPlacement` - Dataclass with position and LED information

**knight_pathfinding.py**
- `plan_knight_movement()` - L-shaped pathfinding for knight moves
  - Avoids occupied squares during two-step movement

**led/ws2812b_controller.py**
- `WS2812BController`: Controls 96 individually addressable RGB LEDs
  - Main board: LEDs 16-79 (8×8 = 64 LEDs)
  - Left capture area: LEDs 0-15 (2×8 = 16 LEDs)
  - Right capture area: LEDs 80-95 (2×8 = 16 LEDs)
  - Extended square-to-LED index mapping including capture areas
  - MockPixelStrip for testing without hardware
  - Game state visualization methods:
    * `show_valid_moves()` - Highlight legal moves (green) and captures (orange)
    * `show_check_state()` - Red indicator for check
    * `show_invalid_move_feedback()` - Red feedback for illegal moves
    * `show_move_feedback()` - Show last move made
    * `show_checkmate()` - Bright red for game over
    * `show_stalemate()` - Yellow center squares
    * `show_player_turn()` - Edge lighting for turn indicator
  - Capture area visualization:
    * Captured pieces shown in RED for game duration
    * Left area: black's captured pieces
    * Right area: white's captured pieces
  - Rainbow pattern generator with HSV color conversion
  - Brightness control (0-255)
  - Uses rpi_ws281x library (hardware PWM on GPIO 18)

## Code Quality Tools

### Ruff (Linting & Formatting)
Fast Python linter and formatter replacing flake8, black, isort, and more.

```bash
# Format code (modifies files in place)
uv run ruff format .

# Check for lint issues
uv run ruff check .

# Auto-fix issues where possible
uv run ruff check --fix .

# Check specific file
uv run ruff check motor_controller.py
```

**Configuration**: See `[tool.ruff]` in `pyproject.toml`
- Line length: 100 characters
- Enabled rules: pycodestyle, pyflakes, isort, pep8-naming, pyupgrade, bugbear, and more
- Target: Python 3.13+

### Mypy (Type Checking)
Static type checker for Python with strict mode enabled.

```bash
# Type check all files
uv run mypy .

# Check specific file
uv run mypy motor_controller.py

# Generate HTML report
uv run mypy --html-report ./mypy-report .
```

**Configuration**: See `[tool.mypy]` in `pyproject.toml`
- Strict mode enabled
- Disallows untyped definitions
- Warns on unused configs and redundant casts
- Configured to ignore missing gpiozero type stubs

### Pytest (Testing Framework)
Test framework for comprehensive testing with visualizations.

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_board_navigation.py -v

# Run with output
pytest tests/ -v -s
```

**Test Structure**:
- `tests/test_board_navigation.py` - Chess board navigation and movement tests
- `tests/test_extended_board.py` - Extended board coordinate system tests (capture areas)
- `tests/test_capture_handling.py` - Capture sequence visualization with obstacle avoidance
- `tests/test_path_verification.py` - Path planning verification (ensures no collisions)
- `tests/test_utils.py` - Visualization utilities with capture area rendering
- `tests/output/` - Generated visualization plots
  - `movement/` - Movement path and speed analysis (with capture areas shown)
  - `chess/` - Chess game logic visualizations
  - `leds/` - LED pattern visualizations
  - `reed_switches/` - Reed switch detection visualizations
  - `captures/` - Capture sequence visualizations with obstacle avoidance paths

### Pre-commit Workflow

Before committing code, run:
```bash
uv run ruff format . && uv run ruff check --fix . && uv run mypy . && pytest tests/
```

Or create an alias in your shell:
```bash
alias lint='uv run ruff format . && uv run ruff check --fix . && uv run mypy . && pytest tests/'
```

## Committing Changes
If committing changes, ensure that:
- code quality checks pass,
- tests pass successfully,
- update docs, README.md or AGENTS.md if necessary,
- commit using conventional commit messages (e.g., `feat: add new motor control feature`),
- make multiple smaller commits if changes are large and unrelated.
- always ask before committing and ask the user to confirm!
- do not push

## Design Decisions

### Why Python?
- Fast development cycle
- Excellent GPIO library ecosystem
- Sufficient performance for chess piece speeds
- Easy to test and iterate

### Why gpiozero?
- High-level GPIO abstraction
- Automatic pullup/pulldown handling
- Works without GPIO (simulation mode)
- Good for rapid prototyping

### Why configuration over hardcoding?
- Different motor setups without code recompilation
- Easy calibration (step counts, speeds)
- Direction inversion simple to toggle
- Future scaling to multiple boards

### Module Import Path Consistency
**CRITICAL**: Always import from the pythonpath-relative path, never with `src.` prefix.

Since `src/` is configured in pythonpath (`pyproject.toml`), all imports should use:
```python
from chess_game import Piece, Player, PieceType  # ✅ Correct
from capture_management import get_next_capture_slot  # ✅ Correct
```

**Never use**:
```python
from src.chess_game import Piece  # ❌ Wrong - creates duplicate module
from src.capture_management import ...  # ❌ Wrong
```

**Why this matters**: Python treats `chess_game` and `src.chess_game` as different modules, even if they're the same source file. This causes:
- Enum comparison failures (`Piece.player == Player.BLACK` returns `False`)
- Instance checks fail (`isinstance(obj, Piece)` returns `False`)
- Duplicate class definitions in memory

**Symptoms of mixed imports**:
- Enum comparisons mysteriously return False
- Type checks fail despite correct types
- `is` comparisons fail for what should be the same object

## Implementation Details

### Homing Algorithm

1. Move in configured direction until limit switch pressed
2. Reset position to 0
3. Mark motor as homed
4. Prevent movement before homing

Homing is sequential (X then Y) to simplify debugging.

### Position Tracking

- Maintains internal position counter
- Incremented/decremented by movement commands
- Bounds checking before moves
- Throws exception if limits exceeded

### Coordinated Movement

Uses **Bresenham's line algorithm** to move both motors simultaneously:
- Ensures straight diagonal paths (not L-shaped)
- Both axes complete at the same time
- Proportional step distribution across dominant axis
- **Per-motor acceleration**: Each motor calculates its own acceleration profile based on individual step count
- **Diagonal speed boost**: 30% faster when both axes move (0.7 delay multiplier)

### Acceleration Profile

Implements **trapezoidal velocity profile** for smooth motion:

```
Velocity
   ↑
   │     ┌─────────────┐  ← Constant max speed
   │    /               \
   │   /                 \
   │  /                   \
   │ /                     \
   └──────────────────────────→ Time
     ↑         ↑          ↑
  Accel   Constant    Decel
```

**Three phases**:
1. **Acceleration**: Linearly ramp from `MAX_STEP_DELAY` (250 steps/s) to `MIN_STEP_DELAY` (1250 steps/s)
2. **Constant Speed**: Maintain maximum velocity
3. **Deceleration**: Linearly ramp back to starting speed

**Benefits**:
- Prevents missed steps by starting slow
- Reduces mechanical stress and vibration
- Enables higher maximum speeds safely
- Smoother, quieter operation

**Configuration** (`config.py`):
- `ENABLE_ACCELERATION` - Toggle on/off
- `MIN_STEP_DELAY` - Max speed (must be >0.0005s for StealthChop)
- `MAX_STEP_DELAY` - Start/end speed
- `ACCELERATION_STEPS` - Ramp length (50 recommended)

**Per-motor implementation**: Each motor in coordinated moves calculates its acceleration independently based on its own step count, allowing both motors to accelerate smoothly even when moving different distances.

**Diagonal optimization**: When both axes move, a 0.7 multiplier is applied to step delays (30% speed increase) since Bresenham efficiently alternates motor steps.

**For short moves**: If total steps < 2× `ACCELERATION_STEPS`, ramp is automatically reduced to fit.

### Obstacle Avoidance Path Planning

The system uses **greedy local pathfinding** to navigate pieces around obstacles when moving to capture areas:

**Main Board Navigation**:
1. **Horizontal movement** - Try moving toward target edge column (0 for left, 7 for right)
2. **Diagonal moves** - If blocked, try diagonal movements (up/down + horizontal)
3. **Vertical moves** - If still blocked, move vertically toward target row
4. **Edge routing** - As last resort, find clear vertical path to edge row

**Key features**:
- Excludes starting square from obstacle checking (piece is already there)
- Detects when stuck on edge rows (0 or 7) and enters capture area directly
- Makes local decisions at each step rather than pre-computing entire path

**Capture Area Navigation**:
Once at board edge, the piece enters the capture area corridor:
1. **Enter inner column** - Start in inner capture column (-1 for left, 8 for right)
2. **Move vertically** - Travel toward target row
3. **Diagonal avoidance** - When encountering obstacle at next row:
   - First try other column at next row (diagonal move)
   - Only if both columns blocked at next row, switch columns at current row
4. **Final positioning** - Move to target column at destination row

**Design rationale**:
- Diagonal moves preferred in capture area (matches main board strategy)
- Minimizes unnecessary horizontal movements
- Avoids moving into occupied squares
- Clean, efficient paths that appear natural

### Step Timing

```
Step pulse timing:
├── GPIO HIGH for STEP_PULSE_DURATION (1ms default)
├── GPIO LOW for STEP_DELAY (varies with acceleration)
└── With acceleration: 0.8ms to 4ms = 250-1250 Hz range
```

Adjustable for different motor/driver combinations.

## GPIO Safety Considerations

- Step pins normally LOW (gpiozero default)
- Direction pin set before moving
- Limit switches use internal pullups
- No floating pins after GPIO release

Optional 4.7kΩ pulldown on step pins for EMI immunity when motors running nearby.

## Testing Strategy

### Manual Testing Checklist
1. [ ] Motors respond to step/direction signals
2. [ ] Direction inversion works correctly
3. [ ] Limit switches trigger homing
4. [ ] Position limits enforced
5. [ ] Interactive mode commands work
6. [ ] Code passes `ruff check` with no errors
7. [ ] Code passes `mypy` with no type errors
8. [ ] Acceleration profile produces smooth movement
9. [ ] Motors don't skip steps with acceleration enabled

### Unit Tests (Future)
- Test position calculations
- Test boundary conditions
- Test direction inversion logic
- Test acceleration profile calculations

### Integration Tests (Future)
- Homing with real motors
- Movement precision verification
- Load testing with continuous movement
- Acceleration stress testing

## Known Limitations

- **Homing is sequential**: X then Y (fine for slow chess movements)
- **Position lost on reboot**: No persistent storage of last position
- **Single-threaded**: Blocking movement commands

## Future Enhancements

1. **Persistence**: Save last position to file/database
## Future Enhancements

1. **Persistence**: Save last position to file/database
2. **Parallel homing**: Home both axes simultaneously
3. **UART TMC2208**: Enable monitor current/diagnostics
4. **Web API**: Control via HTTP REST endpoints
5. **Move queue**: Schedule multiple moves
6. **Position profiles**: Store named positions (e.g., "a1", "h8")

## Pin Assignment Rationale

**Motor X (horizontal)**: GPIO 17, 18
- Standard RPi Zero pins, away from special functions

**Motor Y (vertical)**: GPIO 27, 22
- Clustered together for organization

**Home switches**: GPIO 23, 24
- Consecutive pins for symmetry

**Electromagnet**: GPIO 25
- Near home switches for clean wiring

All chosen pins avoid:
- SPI/I2C buses
- UART pins
- Power/ground pins
- Pins with special boot functions

## Speed Calculations

**With Acceleration Enabled** (default):
- Start/end speed: `MAX_STEP_DELAY = 0.004s` → 250 steps/second
- Maximum speed: `MIN_STEP_DELAY = 0.0008s` → 1250 steps/second
- Acceleration time: 50 steps × average delay ≈ 0.12 seconds
- Total for 200-step move: ~0.32 seconds (includes accel + constant + decel)

**Without Acceleration**:
- Constant speed: `STEP_DELAY = 0.002s` → 500 steps/second
- Total for 200-step move: 0.40 seconds

**Result**: Acceleration is ~20% faster while being smoother and quieter!

**Microstepping**: 16× microstepping = 3200 steps per motor revolution (for 1.8° NEMA motor)

Adjust `MIN_STEP_DELAY` and `MAX_STEP_DELAY` for different speed profiles.

## Debugging Tips

```python
# Check motor status
controller.get_status()

# Manual step test
motor_x._pulse_step()  # Single step without position tracking

# Force reset position
motor_x.current_position = 0

# Test limit switch
print(motor_x._home_device.is_pressed)
```

## Dependencies

- **gpiozero**: GPIO abstraction (can be optional with fallback)
- **Python 3.13.5+**: Type hints, async features

**Development tools**:
- **ruff**: Fast linting and formatting
- **mypy**: Static type checking

No heavy dependencies - designed for embedded systems.

## Calibration Guide

To find real maximum positions:

1. Home motors: `python main.py home`
2. Move to end: `python main.py move 100000 0`
3. Note step count when carriage hits physical limit
4. Update `MAX_X_POSITION` and `MAX_Y_POSITION`
5. Test move-to-max: `python main.py move MAX_X_POSITION MAX_Y_POSITION`

Record step counts for your physical setup for repeatability.
