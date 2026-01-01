"""Pytest configuration and shared fixtures."""

import os
from collections.abc import Generator

import pytest
from gpiozero import Device
from gpiozero.pins.mock import MockFactory

# Disable motor debug prints for faster test execution
os.environ["MOTOR_DEBUG"] = "0"


@pytest.fixture(autouse=True)
def reset_gpio_factory() -> Generator[None]:
    """Reset GPIO factory before each test to avoid pin conflicts."""
    Device.pin_factory = MockFactory()
    yield
    Device.pin_factory.reset()
