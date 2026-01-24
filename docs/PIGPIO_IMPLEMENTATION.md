# Pigpio Hardware-Timed Step Generation - Implementation Summary

## What Was Changed

### 1. New Module: `src/motor/pigpio_wave.py`
- Implements hardware-timed step pulse generation using pigpio waves
- Converts acceleration-profiled step timelines into microsecond-precision pulses
- Automatically merges X and Y motor step events into a single timeline
- Gracefully handles pigpio unavailability (returns None if can't connect)

### 2. Updated: `src/motor/motor_controller.py`
- Added optional pigpio wave generator with automatic fallback
- New methods:
  - `_move_coordinated_with_pigpio()` - Hardware-timed coordinated moves
  - `_move_coordinated_with_sleep()` - Software-timed fallback (existing behavior)
  - `_build_step_timeline()` - Converts acceleration profile to timeline format
- Modified `_move_coordinated()` to choose between hardware/software timing
- Maintains full backward compatibility

### 3. Updated: `src/config.py`
- Added `USE_PIGPIO = True` configuration option
- Updated speed comments to reflect pigpio capabilities

### 4. Updated: `src/main.py`
- Passes `use_pigpio` parameter to MotorController initialization

### 5. New Files:
- `setup-pigpio.sh` - Automated setup script for Raspberry Pi
- Installs pigpio daemon, enables service, starts on boot

### 6. Updated: `README.md`
- Added pigpio installation instructions
- Updated speed specifications (8000 steps/s vs 1000 steps/s)
- Added configuration documentation for `USE_PIGPIO`

### 7. Updated: `pyproject.toml`
- Added `pigpio>=1.78` dependency

## How It Works

### Speed Improvement Explained

**Before (software timing with time.sleep)**:
- Python's `time.sleep()` on Linux has ~1ms minimum resolution
- Configured for 0.000125s (125µs) → actually gets ~1ms floor
- Effective step rate: ~1000 steps/s
- Linear speed at 80 steps/mm: ~12.5 mm/s

**After (hardware timing with pigpio)**:
- pigpio generates pulses with microsecond precision
- Can achieve configured 0.000125s (125µs) delays
- Effective step rate: ~8000 steps/s (8× improvement)
- Linear speed at 80 steps/mm: ~100 mm/s (8× faster!)

### Technical Details

**Pigpio Wave Generation**:
1. Pre-compute entire move as a timeline of events with precise delays
2. Convert to pigpio pulse format (GPIO high/low + delay_us)
3. Upload to DMA hardware on the Pi
4. Hardware executes pulses with microsecond precision
5. No Python sleep() calls in the hot path

**Acceleration Profile Preserved**:
- Both motors still use trapezoidal velocity profiles
- Bresenham algorithm still ensures straight diagonal paths
- Diagonal speed boost (30% faster) still applied
- All existing motion planning logic unchanged

## Testing on Raspberry Pi

### 1. Deploy to Pi

```bash
# From your development machine
./deploy.sh
```

### 2. SSH to Pi and Setup pigpio

```bash
ssh pizero2-2
cd ~/workspace/auto-chess-backend
./setup-pigpio.sh
```

### 3. Install Dependencies

```bash
~/.local/bin/uv sync
```

### 4. Test Movement

```bash
# Home motors
~/.local/bin/uv run python src/main.py home

# Move to a position (will show if using pigpio or fallback)
~/.local/bin/uv run python src/main.py move 2000 2000
```

**Expected output**:
```
✅ Using pigpio for hardware-timed step generation
🏠 Starting homing sequence...
...
```

OR (if pigpio daemon not running):
```
⚠️  Could not initialize pigpio: Could not connect to pigpio daemon...
⚠️  Falling back to time.sleep() based timing
...
```

### 5. Verify Speed Improvement

You should see noticeably faster movement compared to before. The motion should be smooth and much quicker than the ~10-12 mm/s you were experiencing.

## Troubleshooting

### "Could not connect to pigpio daemon"

**Check if pigpiod is running**:
```bash
sudo systemctl status pigpiod
```

**If not running**:
```bash
sudo systemctl start pigpiod
```

**If not installed**:
```bash
./setup-pigpio.sh
```

### Permission Issues

If you get permission errors, ensure your user is in the `gpio` group:
```bash
sudo usermod -a -G gpio $USER
# Logout and login again
```

### Fallback Mode Works Fine

If pigpio doesn't work for some reason, the system will automatically fall back to software timing. It will be slower (~10-12 mm/s) but functional.

## Configuration Options

In `src/config.py`:

```python
# Enable pigpio hardware timing (recommended)
USE_PIGPIO = True  # Set to False to force software timing

# Speed settings (with pigpio these are achievable)
MIN_STEP_DELAY = 0.000125  # 8000 steps/s = 100 mm/s at 80 steps/mm
MAX_STEP_DELAY = 0.002     # 500 steps/s starting speed
ACCELERATION_STEPS = 200    # Ramp length
```

## Performance Expectations

With pigpio enabled:
- **Maximum speed**: ~100 mm/s (8000 steps/s at 80 steps/mm)
- **Starting speed**: ~6 mm/s (500 steps/s)
- **Acceleration time**: ~0.5 seconds (200 steps)
- **Timing precision**: Microsecond level
- **Smoothness**: Very smooth due to precise timing

Without pigpio (fallback):
- **Maximum speed**: ~12 mm/s (limited by OS scheduler)
- **Starting speed**: ~6 mm/s
- **Timing jitter**: ~1ms variations
- **Still functional**: Just slower

## Next Steps

1. Deploy and test on the Pi
2. Run setup-pigpio.sh to install daemon
3. Test movement and verify speed improvement
4. Adjust `MIN_STEP_DELAY` if needed for your specific motors/mechanics
5. Keep `USE_PIGPIO = True` for best performance
