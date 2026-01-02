"""Electromagnet control module."""

import os

try:
    from gpiozero import DigitalOutputDevice

    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False

# Disable debug prints during testing
DEBUG_PRINTS = os.getenv("MOTOR_DEBUG", "1") == "1"


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
            print("🧲 Electromagnet: ON")

    def off(self) -> None:
        """Turn the electromagnet off."""
        if GPIO_AVAILABLE and self._device:
            self._device.off()
        self.is_on = False
        if DEBUG_PRINTS:
            print("⭕ Electromagnet: OFF")

    def toggle(self) -> None:
        """Toggle the electromagnet state."""
        if self.is_on:
            self.off()
        else:
            self.on()

    def get_status(self) -> dict[str, bool]:
        """Get current electromagnet status."""
        return {"is_on": self.is_on}
