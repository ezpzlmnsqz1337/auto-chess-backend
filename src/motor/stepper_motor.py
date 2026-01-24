"""Stepper motor control module."""

import os
import time

try:
    from gpiozero import Button, Device, DigitalOutputDevice
    GPIO_AVAILABLE = True
    # Prefer pigpio pin factory to align with hardware-timed wave generation
    try:
        from gpiozero.pins.pigpio import PiGPIOFactory

        Device.pin_factory = PiGPIOFactory()
    except Exception:
        # If pigpio pin factory is not available or pigpiod not running,
        # gpiozero will fall back automatically; warnings are benign.
        pass
except ImportError:
    GPIO_AVAILABLE = False

# Disable debug prints during testing
DEBUG_PRINTS = os.getenv("MOTOR_DEBUG", "1") == "1"


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

        self._validate_move(steps, direction)
        self._set_direction(direction)

        for _ in range(steps):
            self._pulse_step()

        self._update_position(steps, direction)

    def _validate_move(self, steps: int, direction: int) -> None:
        """
        Validate that a move is within bounds.

        Args:
            steps: Number of steps to move
            direction: Movement direction (0 or 1)

        Raises:
            ValueError: If movement would exceed limits
        """
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

    def _update_position(self, steps: int, direction: int) -> None:
        """
        Update position after a move.

        Args:
            steps: Number of steps moved
            direction: Direction moved (0 or 1)
        """
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
        if self._is_mock_gpio():
            self._simulate_homing()
            return

        self._execute_homing(home_direction, home_step_delay)

    def _is_mock_gpio(self) -> bool:
        """Check if GPIO is available or mocked."""
        if not GPIO_AVAILABLE or not self._home_device:
            return True

        try:
            from gpiozero import Device
            from gpiozero.pins.mock import MockFactory

            if isinstance(Device.pin_factory, MockFactory):
                return True
        except ImportError:
            pass

        return False

    def _simulate_homing(self) -> None:
        """Simulate homing when GPIO is not available."""
        print("🔧 GPIO not available or mock detected. Simulating home at position 0.")
        self.current_position = 0
        self.is_homed = True

    def _execute_homing(self, home_direction: int, home_step_delay: float) -> None:
        """
        Execute the actual homing sequence.

        Args:
            home_direction: Direction to move during homing
            home_step_delay: Step delay during homing

        Raises:
            RuntimeError: If limit switch never triggered
        """
        original_step_delay = self.step_delay
        self.step_delay = home_step_delay
        self._set_direction(home_direction)

        max_steps = self.max_position
        steps_taken = 0

        try:
            while steps_taken < max_steps:
                if not self._home_device.is_pressed:
                    self._pulse_step()
                    steps_taken += 1
                else:
                    self.current_position = 0
                    self.is_homed = True
                    print(f"✅ Homing complete after {steps_taken} steps")
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
        print("🛑 Emergency stop triggered")

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
