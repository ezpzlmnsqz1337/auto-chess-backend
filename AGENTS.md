# Development Notes - Auto Chess Backend

## Project Architecture

### Core Components

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
- Chess board configuration (square size, board dimensions)
- Tunable parameters: step speeds, limits, directions, acceleration
- Easy hardware reconfiguration without code changes

**board_navigation.py**
- Chess board coordinate conversions
- `square_to_steps(row, col)` - Board coordinates to motor steps
- `chess_notation_to_steps('e4')` - Chess notation to motor steps
- `steps_to_mm(x, y)` - Steps to millimeters conversion
- Board dimension queries

**main.py**
- CLI with subcommands for all operations
- Interactive mode for manual control
- Error handling and user feedback

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
- `tests/test_board_navigation.py` - Chess board navigation tests
- `tests/output/` - Generated visualization plots

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

**For short moves**: If total steps < 2× `ACCELERATION_STEPS`, ramp is automatically reduced to fit.

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
