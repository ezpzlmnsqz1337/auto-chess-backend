"""Motor controller fixtures for testing."""

from typing import Any

import config
from motor import MotorController, StepperMotor


def create_test_controller() -> MotorController:
    """
    Create a motor controller for testing with mock GPIO.

    Returns:
        Configured MotorController ready for testing
    """
    motor_x = create_test_motor("X")
    motor_y = create_test_motor("Y")

    controller = MotorController(
        motor_x,
        motor_y,
        enable_acceleration=config.ENABLE_ACCELERATION,
        min_step_delay=config.MIN_STEP_DELAY,
        max_step_delay=config.MAX_STEP_DELAY,
        accel_steps=config.ACCELERATION_STEPS,
    )
    # Simulate homing
    controller.motor_x.is_homed = True
    controller.motor_y.is_homed = True
    return controller


def create_test_motor(
    axis: str = "X", max_position: int | None = None, **kwargs: Any
) -> StepperMotor:
    """
    Create a single motor for testing with mock GPIO.

    Args:
        axis: "X" or "Y" to select motor configuration
        max_position: Override max_position (useful for fast tests)
        **kwargs: Additional StepperMotor parameters to override

    Returns:
        Configured StepperMotor ready for testing
    """
    if axis.upper() == "X":
        defaults: dict[str, Any] = {
            "step_pin": config.MOTOR_X_STEP_PIN,
            "dir_pin": config.MOTOR_X_DIR_PIN,
            "home_pin": config.MOTOR_X_HOME_PIN,
            "enable_pin": config.MOTOR_X_ENABLE_PIN,
            "invert_direction": config.MOTOR_X_INVERT,
            "max_position": max_position or config.MAX_X_POSITION,
        }
    else:  # Y axis
        defaults = {
            "step_pin": config.MOTOR_Y_STEP_PIN,
            "dir_pin": config.MOTOR_Y_DIR_PIN,
            "home_pin": config.MOTOR_Y_HOME_PIN,
            "enable_pin": config.MOTOR_Y_ENABLE_PIN,
            "invert_direction": config.MOTOR_Y_INVERT,
            "max_position": max_position or config.MAX_Y_POSITION,
        }

    # Add common defaults
    defaults.update(
        {
            "step_delay": config.STEP_DELAY,
            "step_pulse_duration": config.STEP_PULSE_DURATION,
        }
    )

    # Override with any provided kwargs
    defaults.update(kwargs)

    return StepperMotor(**defaults)
