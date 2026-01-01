"""
Stepper motor controller module.
Provides control for XY axis movement with homing functionality.
"""

import os
import time
from enum import Enum

try:
    from gpiozero import Button, DigitalOutputDevice

    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False

# Disable debug prints during testing
DEBUG_PRINTS = os.getenv("MOTOR_DEBUG", "1") == "1"


class Axis(Enum):
    """Enumeration for motor axes."""

    X = "X"
    Y = "Y"


class Electromagnet:
    """Control an electromagnet via GPIO pin."""

    def __init__(self, pin: int, active_high: bool = True):
        """
        Initialize electromagnet controller.

        Args:
            pin: GPIO pin number for electromagnet control
            active_high: If True, magnet ON when GPIO HIGH. If False, magnet ON when GPIO LOW.
        """
        self.pin = pin
        self.active_high = active_high
        self.is_on = False

        if GPIO_AVAILABLE:
            self._device = DigitalOutputDevice(pin, active_high=active_high, initial_value=False)
        else:
            self._device = None

    def on(self) -> None:
        """Turn the electromagnet on."""
        if GPIO_AVAILABLE and self._device:
            self._device.on()
        self.is_on = True
        if DEBUG_PRINTS:
            print("Electromagnet: ON")

    def off(self) -> None:
        """Turn the electromagnet off."""
        if GPIO_AVAILABLE and self._device:
            self._device.off()
        self.is_on = False
        if DEBUG_PRINTS:
            print("Electromagnet: OFF")

    def toggle(self) -> None:
        """Toggle the electromagnet state."""
        if self.is_on:
            self.off()
        else:
            self.on()

    def get_status(self) -> dict[str, bool]:
        """Get current electromagnet status."""
        return {"is_on": self.is_on}


class StepperMotor:
    """Control a single stepper motor with step and direction pins."""

    def __init__(
        self,
        step_pin: int,
        dir_pin: int,
        home_pin: int,
        enable_pin: int | None = None,
        invert_direction: bool = False,
        max_position: int = 5000,
        step_delay: float = 0.002,
        step_pulse_duration: float = 0.001,
    ):
        """
        Initialize a stepper motor controller.

        Args:
            step_pin: GPIO pin for step signal
            dir_pin: GPIO pin for direction signal
            home_pin: GPIO pin for home/limit switch
            enable_pin: GPIO pin for enable signal (LOW=enabled, HIGH=disabled)
            invert_direction: If True, inverts the direction of movement
            max_position: Maximum position in steps
            step_delay: Delay between steps in seconds
            step_pulse_duration: Duration of step pulse in seconds
        """
        self.step_pin = step_pin
        self.dir_pin = dir_pin
        self.home_pin = home_pin
        self.enable_pin = enable_pin
        self.invert_direction = invert_direction
        self.max_position = max_position
        self.step_delay = step_delay
        self.step_pulse_duration = step_pulse_duration
        self.current_position = 0
        self.is_homed = False
        self.is_enabled = True  # Track enable state

        if GPIO_AVAILABLE:
            self._step_device = DigitalOutputDevice(step_pin)
            self._dir_device = DigitalOutputDevice(dir_pin)
            self._home_device = Button(home_pin, pull_up=True)
            # Enable pin: LOW = enabled, HIGH = disabled
            if enable_pin is not None:
                self._enable_device = DigitalOutputDevice(enable_pin, initial_value=False)
            else:
                self._enable_device = None
        else:
            self._step_device = None
            self._dir_device = None
            self._home_device = None
            self._enable_device = None

    def _set_direction(self, direction: int) -> None:
        """
        Set motor direction.

        Args:
            direction: 0 for backward, 1 for forward
        """
        if self.invert_direction:
            direction = 1 - direction

        if GPIO_AVAILABLE and self._dir_device:
            self._dir_device.value = direction

    def enable(self) -> None:
        """Enable the motor (LOW signal)."""
        if GPIO_AVAILABLE and self._enable_device:
            self._enable_device.off()  # LOW = enabled
        self.is_enabled = True

    def disable(self) -> None:
        """Disable the motor (HIGH signal) - saves power and allows manual movement."""
        if GPIO_AVAILABLE and self._enable_device:
            self._enable_device.on()  # HIGH = disabled
        self.is_enabled = False

    def _pulse_step(self) -> None:
        """Send a single step pulse to the motor."""
        if GPIO_AVAILABLE and self._step_device:
            self._step_device.on()
            time.sleep(self.step_pulse_duration)
            self._step_device.off()
            time.sleep(self.step_delay)

    def move(self, steps: int, direction: int = 1) -> None:
        """
        Move motor by specified number of steps.

        Args:
            steps: Number of steps to move
            direction: 0 for negative direction, 1 for positive direction

        Raises:
            ValueError: If movement would exceed max position
            RuntimeError: If motor is disabled
        """
        if not self.is_enabled:
            raise RuntimeError("Motor is disabled. Enable motor before moving.")

        if direction == 1 and self.current_position + steps > self.max_position:
            raise ValueError(
                f"Movement would exceed max position. "
                f"Current: {self.current_position}, "
                f"Max: {self.max_position}, "
                f"Requested steps: {steps}"
            )

        if direction == 0 and self.current_position - steps < 0:
            raise ValueError(
                f"Movement would go below 0. "
                f"Current: {self.current_position}, "
                f"Requested steps: {steps}"
            )

        self._set_direction(direction)

        for _ in range(steps):
            self._pulse_step()

        # Update position
        if direction == 1:
            self.current_position += steps
        else:
            self.current_position -= steps

    def move_to_position(self, target_position: int) -> None:
        """
        Move to an absolute position.

        Args:
            target_position: Target position in steps

        Raises:
            ValueError: If target position is invalid
        """
        if target_position < 0 or target_position > self.max_position:
            raise ValueError(
                f"Invalid target position: {target_position}. "
                f"Must be between 0 and {self.max_position}"
            )

        if target_position > self.current_position:
            steps = target_position - self.current_position
            self.move(steps, direction=1)
        elif target_position < self.current_position:
            steps = self.current_position - target_position
            self.move(steps, direction=0)

    def home(self, home_direction: int = 0, home_step_delay: float = 0.005) -> None:
        """
        Home the motor by moving until the limit switch is pressed.

        Args:
            home_direction: Direction to move during homing (0 or 1)
            home_step_delay: Step delay during homing (usually slower)

        Raises:
            RuntimeError: If homing fails (limit switch never triggered)
        """
        if not GPIO_AVAILABLE or not self._home_device:
            print("GPIO not available. Simulating home at position 0.")
            self.current_position = 0
            self.is_homed = True
            return

        # Check if using mock pin factory
        try:
            from gpiozero import Device
            from gpiozero.pins.mock import MockFactory

            if isinstance(Device.pin_factory, MockFactory):
                print("Mock GPIO detected. Simulating home at position 0.")
                self.current_position = 0
                self.is_homed = True
                return
        except ImportError:
            pass

        original_step_delay = self.step_delay
        self.step_delay = home_step_delay
        self._set_direction(home_direction)

        # Safety: Don't home beyond the physical limits of the axis
        max_steps = self.max_position
        steps_taken = 0

        try:
            while steps_taken < max_steps:
                # Check if home switch is pressed (pin reads 0 when pressed)
                if not self._home_device.is_pressed:
                    self._pulse_step()
                    steps_taken += 1
                else:
                    # Home switch pressed
                    self.current_position = 0
                    self.is_homed = True
                    print(f"Homing complete after {steps_taken} steps")
                    return
        finally:
            self.step_delay = original_step_delay

        raise RuntimeError(
            f"Homing failed: limit switch not triggered after {max_steps} steps. "
            f"This is a safety limit to prevent damage. Check endstop wiring and position."
        )

    def get_position(self) -> int:
        """Get current position in steps."""
        return self.current_position

    def get_status(self) -> dict[str, int | bool]:
        """Get current motor status."""
        return {
            "position": self.current_position,
            "max_position": self.max_position,
            "is_homed": self.is_homed,
            "direction_inverted": self.invert_direction,
            "endstop_pressed": not self._home_device.is_pressed if GPIO_AVAILABLE else False,
        }

    def emergency_stop(self) -> None:
        """Stop all movement immediately."""
        if GPIO_AVAILABLE and self._step_device:
            self._step_device.off()
        print("Emergency stop triggered")

    @staticmethod
    def calculate_step_delay(
        step_number: int,
        total_steps: int,
        min_delay: float,
        max_delay: float,
        accel_steps: int,
    ) -> float:
        """
        Calculate step delay for trapezoidal acceleration profile.

        Uses linear velocity ramping (constant acceleration) rather than
        linear delay ramping. Since velocity = 1/delay, we interpolate
        in velocity space then convert back to delay.

        The velocity profile has three phases:
        1. Acceleration: linearly increase speed (constant acceleration)
        2. Constant: maintain max speed
        3. Deceleration: linearly decrease speed (constant deceleration)

        Args:
            step_number: Current step number (0-indexed)
            total_steps: Total number of steps in the move
            min_delay: Minimum delay (max speed)
            max_delay: Maximum delay (starting/ending speed)
            accel_steps: Number of steps for acceleration/deceleration ramp

        Returns:
            Step delay in seconds for this step
        """
        # Convert delays to speeds (steps per second)
        min_speed = 1.0 / max_delay  # Starting/ending speed
        max_speed = 1.0 / min_delay  # Maximum speed

        # If move is too short for full acceleration, reduce ramp
        effective_accel_steps = min(accel_steps, total_steps // 2)

        if step_number < effective_accel_steps:
            # Acceleration phase: linearly interpolate speed from min to max
            ratio = step_number / effective_accel_steps
            current_speed = min_speed + (max_speed - min_speed) * ratio
            return 1.0 / current_speed
        elif step_number >= total_steps - effective_accel_steps:
            # Deceleration phase: linearly interpolate speed from max to min
            steps_into_decel = step_number - (total_steps - effective_accel_steps)
            ratio = steps_into_decel / effective_accel_steps
            current_speed = max_speed - (max_speed - min_speed) * ratio
            return 1.0 / current_speed
        else:
            # Constant speed phase: use maximum speed (minimum delay)
            return min_delay


class MotorController:
    """Control both X and Y stepper motors."""

    def __init__(
        self,
        motor_x: StepperMotor,
        motor_y: StepperMotor,
        electromagnet: Electromagnet | None = None,
        enable_acceleration: bool = True,
        min_step_delay: float = 0.0008,
        max_step_delay: float = 0.004,
        accel_steps: int = 50,
    ):
        """
        Initialize the dual-axis motor controller.

        Args:
            motor_x: StepperMotor instance for X axis
            motor_y: StepperMotor instance for Y axis
            electromagnet: Optional Electromagnet instance
            enable_acceleration: Enable trapezoidal acceleration profile
            min_step_delay: Minimum delay between steps (max speed)
            max_step_delay: Maximum delay between steps (start/end speed)
            accel_steps: Number of steps for acceleration/deceleration ramps
        """
        self.motor_x = motor_x
        self.motor_y = motor_y
        self.electromagnet = electromagnet
        self.enable_acceleration = enable_acceleration
        self.min_step_delay = min_step_delay
        self.max_step_delay = max_step_delay
        self.accel_steps = accel_steps

    def home_all(
        self,
        home_direction_x: int = 0,
        home_direction_y: int = 0,
        home_step_delay: float = 0.005,
    ) -> None:
        """
        Home all motors sequentially.

        Args:
            home_direction_x: Home direction for X motor
            home_direction_y: Home direction for Y motor
            home_step_delay: Step delay during homing
        """
        if DEBUG_PRINTS:
            print("Starting homing sequence...")
            print("Homing X axis...")
        self.motor_x.home(home_direction_x, home_step_delay)
        if DEBUG_PRINTS:
            print("Homing Y axis...")
        self.motor_y.home(home_direction_y, home_step_delay)
        if DEBUG_PRINTS:
            print("Homing complete!")

    def move_to(self, x: int, y: int) -> None:
        """
        Move to absolute XY position with coordinated motion.

        Both motors move simultaneously using Bresenham's algorithm
        for straight-line diagonal movement.

        Args:
            x: Target X position
            y: Target Y position
        """
        if not self.motor_x.is_homed or not self.motor_y.is_homed:
            raise RuntimeError("Motors must be homed before moving to position")

        # Calculate steps needed for each axis
        x_current = self.motor_x.current_position
        y_current = self.motor_y.current_position
        dx = x - x_current
        dy = y - y_current

        if DEBUG_PRINTS:
            print(f"Moving to X={x}, Y={y}")
        self._move_coordinated(dx, dy)
        if DEBUG_PRINTS:
            print("Reached target position")

    def _move_coordinated(self, dx: int, dy: int) -> None:
        """
        Move both motors simultaneously using Bresenham's line algorithm.

        This ensures diagonal movements follow a straight line and both
        motors finish at the same time. Includes optional acceleration.

        Args:
            dx: Steps to move on X axis (signed)
            dy: Steps to move on Y axis (signed)
        """
        # Handle no movement
        if dx == 0 and dy == 0:
            return

        # Determine directions
        x_dir = 1 if dx > 0 else 0
        y_dir = 1 if dy > 0 else 0

        # Use absolute values for step counts
        abs_dx = abs(dx)
        abs_dy = abs(dy)

        # Check bounds before starting
        target_x = self.motor_x.current_position + dx
        target_y = self.motor_y.current_position + dy

        if target_x < 0 or target_x > self.motor_x.max_position:
            raise ValueError(f"X target {target_x} out of bounds (0-{self.motor_x.max_position})")
        if target_y < 0 or target_y > self.motor_y.max_position:
            raise ValueError(f"Y target {target_y} out of bounds (0-{self.motor_y.max_position})")

        # Set directions
        self.motor_x._set_direction(x_dir)
        self.motor_y._set_direction(y_dir)

        # Total steps is the dominant axis (Bresenham takes max(dx, dy) steps)
        total_steps = max(abs_dx, abs_dy)

        # Save original step delays
        original_x_delay = self.motor_x.step_delay
        original_y_delay = self.motor_y.step_delay

        # Bresenham's line algorithm with acceleration
        step_count = 0

        if abs_dx > abs_dy:
            # X-dominant movement
            error = abs_dx / 2
            for _ in range(abs_dx):
                # Calculate step delay with acceleration if enabled
                if self.enable_acceleration:
                    delay = StepperMotor.calculate_step_delay(
                        step_count,
                        total_steps,
                        self.min_step_delay,
                        self.max_step_delay,
                        self.accel_steps,
                    )
                    self.motor_x.step_delay = delay
                    self.motor_y.step_delay = delay

                self.motor_x._pulse_step()
                # Update X position manually since _pulse_step doesn't do it
                self.motor_x.current_position += 1 if x_dir else -1
                error -= abs_dy
                if error < 0:
                    self.motor_y._pulse_step()
                    # Update Y position manually
                    self.motor_y.current_position += 1 if y_dir else -1
                    error += abs_dx
                step_count += 1
        else:
            # Y-dominant movement
            error = abs_dy / 2
            for _ in range(abs_dy):
                # Calculate step delay with acceleration if enabled
                if self.enable_acceleration:
                    delay = StepperMotor.calculate_step_delay(
                        step_count,
                        total_steps,
                        self.min_step_delay,
                        self.max_step_delay,
                        self.accel_steps,
                    )
                    self.motor_x.step_delay = delay
                    self.motor_y.step_delay = delay

                self.motor_y._pulse_step()
                # Update Y position manually since _pulse_step doesn't do it
                self.motor_y.current_position += 1 if y_dir else -1
                error -= abs_dx
                if error < 0:
                    self.motor_x._pulse_step()
                    # Update X position manually
                    self.motor_x.current_position += 1 if x_dir else -1
                    error += abs_dy
                step_count += 1

        # Restore original step delays
        self.motor_x.step_delay = original_x_delay
        self.motor_y.step_delay = original_y_delay

        # Update positions (Bresenham ensures we took exactly dx and dy steps)
        self.motor_x.current_position = target_x
        self.motor_y.current_position = target_y

    def move_relative(self, dx: int = 0, dy: int = 0) -> None:
        """
        Move relative to current position with coordinated motion.

        Both motors move simultaneously for diagonal movements.

        Args:
            dx: Steps to move on X axis (positive = forward)
            dy: Steps to move on Y axis (positive = forward)
        """
        self._move_coordinated(dx, dy)

    def get_position(self) -> tuple[int, int]:
        """Get current XY position."""
        return (self.motor_x.get_position(), self.motor_y.get_position())

    def get_status(self) -> dict[str, dict[str, int | bool] | dict[str, bool]]:
        """Get status of all motors and electromagnet."""
        status: dict[str, dict[str, int | bool] | dict[str, bool]] = {
            "x_axis": self.motor_x.get_status(),
            "y_axis": self.motor_y.get_status(),
        }
        if self.electromagnet:
            status["electromagnet"] = self.electromagnet.get_status()
        return status

    def magnet_on(self) -> None:
        """Turn electromagnet on."""
        if self.electromagnet:
            self.electromagnet.on()
        else:
            print("Warning: No electromagnet configured")

    def magnet_off(self) -> None:
        """Turn electromagnet off."""
        if self.electromagnet:
            self.electromagnet.off()
        else:
            print("Warning: No electromagnet configured")

    def magnet_toggle(self) -> None:
        """Toggle electromagnet state."""
        if self.electromagnet:
            self.electromagnet.toggle()
        else:
            print("Warning: No electromagnet configured")

    def emergency_stop(self) -> None:
        """Emergency stop all motors and turn off electromagnet."""
        self.motor_x.emergency_stop()
        self.motor_y.emergency_stop()
        if self.electromagnet:
            self.electromagnet.off()
