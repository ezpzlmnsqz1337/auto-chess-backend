"""Dual-axis motor controller with coordinated movement."""

import os

from .electromagnet import Electromagnet
from .stepper_motor import StepperMotor

# Disable debug prints during testing
DEBUG_PRINTS = os.getenv("MOTOR_DEBUG", "1") == "1"


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
            print("🏠 Starting homing sequence...")
            print("➡️  Homing X axis...")
        self.motor_x.home(home_direction_x, home_step_delay)
        if DEBUG_PRINTS:
            print("⬆️  Homing Y axis...")
        self.motor_y.home(home_direction_y, home_step_delay)
        if DEBUG_PRINTS:
            print("✅ Homing complete!")

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
            print(f"🎯 Moving to X={x}, Y={y}")
        self._move_coordinated(dx, dy)
        if DEBUG_PRINTS:
            print("✅ Reached target position")

    def _move_coordinated(self, dx: int, dy: int) -> None:
        """
        Move both motors simultaneously using Bresenham's line algorithm.

        This ensures diagonal movements follow a straight line. Each motor
        uses its own acceleration profile based on its individual step count.

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

        # Validate and prepare for movement
        target_x, target_y = self._prepare_coordinated_move(dx, dy, x_dir, y_dir)

        # Save original step delays
        original_x_delay = self.motor_x.step_delay
        original_y_delay = self.motor_y.step_delay

        # Diagonal speed optimization
        is_diagonal = abs_dx > 0 and abs_dy > 0
        diagonal_speed_boost = 0.7 if is_diagonal else 1.0  # 30% faster on diagonals

        # Execute Bresenham algorithm
        if abs_dx > abs_dy:
            self._execute_x_dominant_move(
                abs_dx, abs_dy, x_dir, y_dir, diagonal_speed_boost
            )
        else:
            self._execute_y_dominant_move(
                abs_dx, abs_dy, x_dir, y_dir, diagonal_speed_boost
            )

        # Restore original step delays
        self.motor_x.step_delay = original_x_delay
        self.motor_y.step_delay = original_y_delay

        # Ensure positions are correct
        self.motor_x.current_position = target_x
        self.motor_y.current_position = target_y

    def _prepare_coordinated_move(
        self, dx: int, dy: int, x_dir: int, y_dir: int
    ) -> tuple[int, int]:
        """
        Validate bounds and prepare for coordinated movement.

        Args:
            dx: Steps to move on X axis
            dy: Steps to move on Y axis
            x_dir: X direction (0 or 1)
            y_dir: Y direction (0 or 1)

        Returns:
            Tuple of (target_x, target_y) positions

        Raises:
            ValueError: If movement would exceed bounds
        """
        target_x = self.motor_x.current_position + dx
        target_y = self.motor_y.current_position + dy

        if target_x < 0 or target_x > self.motor_x.max_position:
            raise ValueError(
                f"X target {target_x} out of bounds (0-{self.motor_x.max_position})"
            )
        if target_y < 0 or target_y > self.motor_y.max_position:
            raise ValueError(
                f"Y target {target_y} out of bounds (0-{self.motor_y.max_position})"
            )

        # Set directions
        self.motor_x._set_direction(x_dir)
        self.motor_y._set_direction(y_dir)

        return target_x, target_y

    def _execute_x_dominant_move(
        self,
        abs_dx: int,
        abs_dy: int,
        x_dir: int,
        y_dir: int,
        diagonal_speed_boost: float,
    ) -> None:
        """
        Execute Bresenham's algorithm for X-dominant movement.

        Args:
            abs_dx: Absolute X steps
            abs_dy: Absolute Y steps
            x_dir: X direction (0 or 1)
            y_dir: Y direction (0 or 1)
            diagonal_speed_boost: Speed multiplier for diagonal moves
        """
        error = abs_dx / 2
        x_step_count = 0
        y_step_count = 0

        for _ in range(abs_dx):
            # Calculate and apply X motor delay
            if self.enable_acceleration:
                x_delay = StepperMotor.calculate_step_delay(
                    x_step_count,
                    abs_dx,
                    self.min_step_delay,
                    self.max_step_delay,
                    self.accel_steps,
                )
                self.motor_x.step_delay = x_delay * diagonal_speed_boost

            self.motor_x._pulse_step()
            self.motor_x.current_position += 1 if x_dir else -1
            x_step_count += 1  # noqa: SIM113 - Bresenham requires conditional increments

            error -= abs_dy
            if error < 0:
                # Calculate and apply Y motor delay
                if self.enable_acceleration:
                    y_delay = StepperMotor.calculate_step_delay(
                        y_step_count,
                        abs_dy,
                        self.min_step_delay,
                        self.max_step_delay,
                        self.accel_steps,
                    )
                    self.motor_y.step_delay = y_delay * diagonal_speed_boost

                self.motor_y._pulse_step()
                self.motor_y.current_position += 1 if y_dir else -1
                y_step_count += 1  # noqa: SIM113 - Bresenham requires conditional increments
                error += abs_dx

    def _execute_y_dominant_move(
        self,
        abs_dx: int,
        abs_dy: int,
        x_dir: int,
        y_dir: int,
        diagonal_speed_boost: float,
    ) -> None:
        """
        Execute Bresenham's algorithm for Y-dominant movement.

        Args:
            abs_dx: Absolute X steps
            abs_dy: Absolute Y steps
            x_dir: X direction (0 or 1)
            y_dir: Y direction (0 or 1)
            diagonal_speed_boost: Speed multiplier for diagonal moves
        """
        error = abs_dy / 2
        x_step_count = 0
        y_step_count = 0

        for _ in range(abs_dy):
            # Calculate and apply Y motor delay
            if self.enable_acceleration:
                y_delay = StepperMotor.calculate_step_delay(
                    y_step_count,
                    abs_dy,
                    self.min_step_delay,
                    self.max_step_delay,
                    self.accel_steps,
                )
                self.motor_y.step_delay = y_delay * diagonal_speed_boost

            self.motor_y._pulse_step()
            self.motor_y.current_position += 1 if y_dir else -1
            y_step_count += 1  # noqa: SIM113 - Bresenham requires conditional increments

            error -= abs_dx
            if error < 0:
                # Calculate and apply X motor delay
                if self.enable_acceleration:
                    x_delay = StepperMotor.calculate_step_delay(
                        x_step_count,
                        abs_dx,
                        self.min_step_delay,
                        self.max_step_delay,
                        self.accel_steps,
                    )
                    self.motor_x.step_delay = x_delay * diagonal_speed_boost

                self.motor_x._pulse_step()
                self.motor_x.current_position += 1 if x_dir else -1
                x_step_count += 1  # noqa: SIM113 - Bresenham requires conditional increments
                error += abs_dy

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
            print("⚠️  Warning: No electromagnet configured")

    def magnet_off(self) -> None:
        """Turn electromagnet off."""
        if self.electromagnet:
            self.electromagnet.off()
        else:
            print("⚠️  Warning: No electromagnet configured")

    def magnet_toggle(self) -> None:
        """Toggle electromagnet state."""
        if self.electromagnet:
            self.electromagnet.toggle()
        else:
            print("⚠️  Warning: No electromagnet configured")

    def emergency_stop(self) -> None:
        """Emergency stop all motors and turn off electromagnet."""
        self.motor_x.emergency_stop()
        self.motor_y.emergency_stop()
        if self.electromagnet:
            self.electromagnet.off()
