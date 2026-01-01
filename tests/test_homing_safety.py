"""Tests for homing safety features."""

from unittest.mock import patch

import pytest

import config
from motor_controller import StepperMotor


def test_homing_exceeds_max_position() -> None:
    """Test that homing throws an error when it exceeds MAX_X_POSITION without hitting endstop."""
    # Create a motor with actual GPIO mocking
    motor = StepperMotor(
        step_pin=config.MOTOR_X_STEP_PIN,
        dir_pin=config.MOTOR_X_DIR_PIN,
        home_pin=config.MOTOR_X_HOME_PIN,
        enable_pin=config.MOTOR_X_ENABLE_PIN,
        invert_direction=config.MOTOR_X_INVERT,
        max_position=config.MAX_X_POSITION,
        step_delay=config.STEP_DELAY,
        step_pulse_duration=config.STEP_PULSE_DURATION,
    )

    # Track how many steps were actually taken
    step_count = [0]
    original_pulse = motor._pulse_step

    def count_steps() -> None:
        step_count[0] += 1
        original_pulse()

    # Mock the endstop to never be pressed (simulate disconnected or broken endstop)
    # Set the underlying pin to HIGH (not pressed, since pull_up=True means active_low)
    motor._home_device.pin.drive_high()

    # Patch Device.pin_factory to not be MockFactory to force real homing logic
    from gpiozero import Device

    original_pin_factory = Device.pin_factory

    # Create a fake pin factory that's not MockFactory
    class FakePinFactory:
        pass

    Device.pin_factory = FakePinFactory()

    try:
        with (
            patch.object(motor, "_pulse_step", side_effect=count_steps),
            pytest.raises(
                RuntimeError,
                match=r"Homing failed: limit switch not triggered after \d+ steps.*safety limit",
            ),
        ):
            # Homing should fail and throw RuntimeError
            motor.home()
    finally:
        Device.pin_factory = original_pin_factory

    # Verify that it stopped at exactly max_position steps (not beyond)
    assert step_count[0] == config.MAX_X_POSITION, (
        f"Expected exactly {config.MAX_X_POSITION} steps, "
        f"but took {step_count[0]} steps during homing"
    )

    # Verify motor is not marked as homed
    assert not motor.is_homed, "Motor should not be marked as homed after failed homing"

    print(
        f"✓ Homing safety test passed - stopped at {step_count[0]} steps "
        f"(max: {config.MAX_X_POSITION})"
    )


def test_homing_success_within_limits() -> None:
    """Test that homing succeeds when endstop is triggered before max_position."""
    motor = StepperMotor(
        step_pin=config.MOTOR_X_STEP_PIN,
        dir_pin=config.MOTOR_X_DIR_PIN,
        home_pin=config.MOTOR_X_HOME_PIN,
        enable_pin=config.MOTOR_X_ENABLE_PIN,
        invert_direction=config.MOTOR_X_INVERT,
        max_position=config.MAX_X_POSITION,
        step_delay=config.STEP_DELAY,
        step_pulse_duration=config.STEP_PULSE_DURATION,
    )

    # Track steps taken
    step_count = [0]
    trigger_at_step = 1000  # Trigger endstop after 1000 steps

    original_pulse = motor._pulse_step

    def count_and_trigger_endstop() -> None:
        step_count[0] += 1
        original_pulse()
        # Simulate endstop being pressed after trigger_at_step steps
        if step_count[0] >= trigger_at_step:
            motor._home_device.pin.drive_low()  # Active low with pull_up=True

    # Initially endstop is not pressed (pin HIGH)
    motor._home_device.pin.drive_high()

    # Patch Device.pin_factory to not be MockFactory
    from gpiozero import Device

    original_pin_factory = Device.pin_factory

    class FakePinFactory:
        pass

    Device.pin_factory = FakePinFactory()

    try:
        with patch.object(motor, "_pulse_step", side_effect=count_and_trigger_endstop):
            # Homing should succeed
            motor.home()
    finally:
        Device.pin_factory = original_pin_factory

    # Verify homing succeeded
    assert motor.is_homed, "Motor should be marked as homed"
    assert motor.current_position == 0, "Motor position should be reset to 0 after homing"
    assert step_count[0] == trigger_at_step, (
        f"Expected {trigger_at_step} steps, but took {step_count[0]} steps"
    )

    print(f"✓ Homing success test passed - endstop triggered at {step_count[0]} steps")


def test_homing_y_axis_exceeds_max_position() -> None:
    """Test that Y axis homing also respects MAX_Y_POSITION safety limit."""
    motor_y = StepperMotor(
        step_pin=config.MOTOR_Y_STEP_PIN,
        dir_pin=config.MOTOR_Y_DIR_PIN,
        home_pin=config.MOTOR_Y_HOME_PIN,
        enable_pin=config.MOTOR_Y_ENABLE_PIN,
        invert_direction=config.MOTOR_Y_INVERT,
        max_position=config.MAX_Y_POSITION,
        step_delay=config.STEP_DELAY,
        step_pulse_duration=config.STEP_PULSE_DURATION,
    )

    step_count = [0]
    original_pulse = motor_y._pulse_step

    def count_steps() -> None:
        step_count[0] += 1
        original_pulse()

    # Mock endstop to never be pressed (pin HIGH)
    motor_y._home_device.pin.drive_high()

    # Patch Device.pin_factory to not be MockFactory
    from gpiozero import Device

    original_pin_factory = Device.pin_factory

    class FakePinFactory:
        pass

    Device.pin_factory = FakePinFactory()

    try:
        with (
            patch.object(motor_y, "_pulse_step", side_effect=count_steps),
            pytest.raises(
                RuntimeError,
                match=r"Homing failed: limit switch not triggered after \d+ steps.*safety limit",
            ),
        ):
            motor_y.home()
    finally:
        Device.pin_factory = original_pin_factory

    # Verify it stopped at exactly max_position
    assert step_count[0] == config.MAX_Y_POSITION, (
        f"Y axis: Expected exactly {config.MAX_Y_POSITION} steps, but took {step_count[0]} steps"
    )

    assert not motor_y.is_homed, "Y motor should not be marked as homed after failed homing"

    print(
        f"✓ Y axis homing safety test passed - stopped at {step_count[0]} steps "
        f"(max: {config.MAX_Y_POSITION})"
    )
