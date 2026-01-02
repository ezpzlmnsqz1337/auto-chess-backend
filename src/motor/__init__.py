"""Motor control package for stepper motors and electromagnet.

This package provides classes for controlling stepper motors and an electromagnet
via GPIO pins on a Raspberry Pi.
"""

from .electromagnet import Electromagnet
from .motor_controller import MotorController
from .stepper_motor import StepperMotor

__all__ = ["Electromagnet", "StepperMotor", "MotorController"]
