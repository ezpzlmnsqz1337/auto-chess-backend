# Acceleration Feature

## Overview

Added **trapezoidal acceleration profile** to motor movement for smoother, faster, and quieter operation.

## How It Works

### Velocity Profile

```
Velocity
   ↑
   │     ┌─────────────┐  ← Max speed (1250 steps/s)
   │    /               \
   │   /                 \
   │  /                   \
   │ /                     \
   └──────────────────────────→ Time
     ↑         ↑          ↑
  Accel   Constant    Decel
```

The motor follows three phases:

1. **Acceleration Phase**
   - Starts at `MAX_STEP_DELAY` (250 steps/s)
   - Linearly ramps up to `MIN_STEP_DELAY` (1250 steps/s)
   - Takes `ACCELERATION_STEPS` (50) steps to complete

2. **Constant Speed Phase**
   - Maintains maximum speed (`MIN_STEP_DELAY`)
   - Duration depends on total move distance

3. **Deceleration Phase**
   - Linearly ramps down from max speed
   - Returns to starting speed over `ACCELERATION_STEPS`
   - Ensures smooth stop

### Benefits

✅ **Prevents Missed Steps**: Starting slow allows motor to overcome inertia  
✅ **Higher Max Speed**: Can safely run at 1250 steps/s (vs 500 constant)  
✅ **Smoother Movement**: Gradual speed changes reduce vibration  
✅ **Quieter Operation**: Less mechanical shock = less noise  
✅ **Reduced Wear**: Gentler on motors, bearings, and carriage  
✅ **Faster Overall**: ~20% speed improvement for typical moves

## Configuration

Edit [`config.py`](config.py):

```python
# Enable/disable acceleration
ENABLE_ACCELERATION = True

# Speed limits
MIN_STEP_DELAY = 0.0008  # Max speed (1250 steps/s)
MAX_STEP_DELAY = 0.004   # Start/end speed (250 steps/s)

# Ramp length
ACCELERATION_STEPS = 50  # Steps for accel/decel ramps
```

### Tuning Guide

**If motors skip steps:**
- Increase `MAX_STEP_DELAY` (slower start)
- Increase `ACCELERATION_STEPS` (longer ramp)
- Decrease `MIN_STEP_DELAY` (lower max speed)

**For faster movement:**
- Decrease `MIN_STEP_DELAY` (higher max speed)
- Keep above 0.0005s to maintain StealthChop

**For smoother movement:**
- Increase `ACCELERATION_STEPS` (gentler ramp)
- Recommended: 50-100 steps

**For short moves:**
- Ramp automatically adjusts to fit available steps
- If move < 2× `ACCELERATION_STEPS`, ramp length reduces

## Performance Comparison

### 200-Step Diagonal Move

**With Acceleration:**
- Time: **0.32 seconds**
- Max speed: 1250 steps/s
- Start/end: 250 steps/s
- Profile: Smooth ramp

**Without Acceleration:**
- Time: **0.40 seconds** 
- Speed: 500 steps/s constant
- Profile: Instant start/stop

**Result**: 20% faster + smoother!

## Implementation Details

### Code Changes

1. **`config.py`**: Added 4 new configuration parameters
2. **`motor_controller.py`**: 
   - New `calculate_step_delay()` static method
   - Updated `MotorController.__init__()` to accept acceleration params
   - Modified `_move_coordinated()` to apply acceleration profile
3. **`main.py`**: Updated controller creation to use config values

### Algorithm

Uses linear interpolation to calculate per-step delay:

```python
# Acceleration phase
ratio = step_number / accel_steps
delay = max_delay - (max_delay - min_delay) * ratio

# Deceleration phase  
ratio = steps_into_decel / accel_steps
delay = min_delay + (max_delay - min_delay) * ratio
```

For coordinated XY movement, both motors use the **same delay** at each step to maintain synchronization.

## Testing

Run the CLI with default settings (acceleration enabled):

```bash
# Home motors
python main.py home

# Test smooth diagonal movement
python main.py move 1000 1000

# Watch for:
# - Gradual speed increase at start
# - Smooth high-speed middle section
# - Gradual slowdown before stop
# - No motor skipping or stuttering
```

### Disable for Testing

To compare with constant speed:

```python
# In config.py
ENABLE_ACCELERATION = False
```

## Safety Notes

⚠️ **StealthChop Compatibility**: Keep `MIN_STEP_DELAY > 0.0005s` to stay below 2000 Hz  
⚠️ **Motor Limits**: Test your specific motors to find safe max speed  
⚠️ **Load Sensitivity**: Heavier loads may require slower max speeds  
⚠️ **Mechanical Limits**: Watch for resonance frequencies causing vibration

## Future Enhancements

Possible improvements:
- **S-curve acceleration**: Smoother than linear (jerk limiting)
- **Dynamic adjustment**: Adapt to load/resistance
- **Per-axis tuning**: Different speeds for X vs Y
- **Look-ahead**: Optimize multiple sequential moves
