"""
Hardware-timed step generation using pigpio waves.

This module provides precise timing for stepper motor control by generating
hardware-timed waveforms through the pigpio daemon. This overcomes the
~1ms timing resolution limit of Python's time.sleep() on Linux.

Benefits:
- Microsecond precision (much better than time.sleep)
- Allows higher step rates (several kHz vs ~1 kHz with time.sleep)
- Smoother motion with consistent timing
- No CPU spinning - hardware handles the timing
"""

import errno as _errno
from typing import Any, Protocol

try:
    import pigpio

    PIGPIO_AVAILABLE = True
except ImportError:
    PIGPIO_AVAILABLE = False
    pigpio = None


class WaveGenerator(Protocol):
    """Protocol for wave generation backends."""

    def generate_coordinated_wave(
        self,
        x_steps: list[tuple[int, float]],
        y_steps: list[tuple[int, float]],
        x_step_pin: int,
        y_step_pin: int,
        x_dir_pin: int,
        y_dir_pin: int,
        x_dir: int,
        y_dir: int,
        pulse_width_us: int,
    ) -> None:
        """Generate and send a coordinated wave for both motors."""
        ...


class PigpioWaveGenerator:
    """Generate hardware-timed stepper motor pulses using pigpio waves."""

    def __init__(self) -> None:
        """Initialize pigpio connection."""
        if not PIGPIO_AVAILABLE:
            raise ImportError("pigpio library not available")

        self.pi: Any | None = None
        self._connect()

    def _connect(self) -> None:
        """Connect to pigpio daemon."""
        if pigpio is None:
            raise ImportError("pigpio library not available")

        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise RuntimeError(
                "Could not connect to pigpio daemon. "
                "Is pigpiod running? Try: sudo pigpiod"
            )

    def close(self) -> None:
        """Close pigpio connection."""
        if self.pi:
            self.pi.stop()
            self.pi = None

    def generate_coordinated_wave(
        self,
        x_steps: list[tuple[int, float]],
        y_steps: list[tuple[int, float]],
        x_step_pin: int,
        y_step_pin: int,
        x_dir_pin: int,
        y_dir_pin: int,
        x_dir: int,
        y_dir: int,
        pulse_width_us: int = 5,
    ) -> None:
        """
        Generate and execute a coordinated wave for both motors.

        This merges step events from both motors into a single timeline,
        respecting the acceleration profile and Bresenham's algorithm.

        Args:
            x_steps: List of (step_number, delay_seconds) for X motor
            y_steps: List of (step_number, delay_seconds) for Y motor
            x_step_pin: GPIO pin for X step signal
            y_step_pin: GPIO pin for Y step signal
            x_dir_pin: GPIO pin for X direction signal
            y_dir_pin: GPIO pin for Y direction signal
            x_dir: Direction for X motor (0 or 1)
            y_dir: Direction for Y motor (0 or 1)
            pulse_width_us: Width of step pulse in microseconds
        """
        if not self.pi:
            raise RuntimeError("Not connected to pigpio daemon")

        # Configure pins as outputs and set directions
        self.pi.set_mode(x_step_pin, pigpio.OUTPUT)
        self.pi.set_mode(y_step_pin, pigpio.OUTPUT)
        self.pi.set_mode(x_dir_pin, pigpio.OUTPUT)
        self.pi.set_mode(y_dir_pin, pigpio.OUTPUT)
        # Ensure step pins start LOW to avoid spurious highs
        self.pi.write(x_step_pin, 0)
        self.pi.write(y_step_pin, 0)
        self.pi.write(x_dir_pin, x_dir)
        self.pi.write(y_dir_pin, y_dir)

        # Build merged timeline of step events
        events = self._merge_step_timelines(x_steps, y_steps, x_step_pin, y_step_pin)

        # Chunk and send waves to respect pigpio pulse limits
        try:
            self._send_wave_in_chunks(events, pulse_width_us)
        except OSError as e:
            # Handle daemon reset/connection loss
            if (e.errno == _errno.ECONNRESET) or ("Connection reset by peer" in str(e)):
                # Attempt one reconnect and retry
                self._connect()
                assert self.pi is not None
                self.pi.set_mode(x_step_pin, pigpio.OUTPUT)
                self.pi.set_mode(y_step_pin, pigpio.OUTPUT)
                self.pi.set_mode(x_dir_pin, pigpio.OUTPUT)
                self.pi.set_mode(y_dir_pin, pigpio.OUTPUT)
                self.pi.write(x_dir_pin, x_dir)
                self.pi.write(y_dir_pin, y_dir)
                self._send_wave_in_chunks(events, pulse_width_us)
            else:
                raise

    def _merge_step_timelines(
        self,
        x_steps: list[tuple[int, float]],
        y_steps: list[tuple[int, float]],
        x_step_pin: int,
        y_step_pin: int,
    ) -> list[tuple[float, int]]:
        """
        Merge X and Y step timelines into a single sorted timeline.

        Args:
            x_steps: List of (step_number, delay_seconds) for X motor
            y_steps: List of (step_number, delay_seconds) for Y motor
            x_step_pin: GPIO pin for X step signal
            y_step_pin: GPIO pin for Y step signal

        Returns:
            List of (time_seconds, pin_number) events sorted by time
        """
        events: list[tuple[float, int]] = []
        current_time = 0.0

        # Convert X steps to time-based events
        for _, delay in x_steps:
            current_time += delay
            events.append((current_time, x_step_pin))

        # Convert Y steps to time-based events
        current_time = 0.0
        for _, delay in y_steps:
            current_time += delay
            events.append((current_time, y_step_pin))

        # Sort by time
        events.sort(key=lambda x: x[0])

        return events

    def _send_wave_in_chunks(self, events: list[tuple[float, int]], pulse_width_us: int) -> None:
        """Send the wave in manageable chunks to avoid pigpio limits.

        pigpio imposes a limit on the number of pulses per wave. Large moves easily
        exceed this, so we build and send multiple smaller waves sequentially.
        Timing accuracy is preserved via running time deltas across chunks.

        Args:
            events: List of (time_seconds, pin_number) events for the entire move
            pulse_width_us: Width of each step pulse in microseconds
        """
        import time

        assert self.pi is not None

        max_pulses_per_wave = 3000  # Conservative limit to avoid daemon stress
        last_time = 0.0
        pulses: list[object] = []
        all_pins: set[int] = set()

        def _flush_pulses() -> None:
            if not pulses:
                return
            pi = self.pi
            assert pi is not None
            pi.wave_clear()
            pi.wave_add_generic(pulses)
            wave_id = pi.wave_create()
            if wave_id < 0:
                raise RuntimeError(f"Failed to create wave: error code {wave_id}")
            pi.wave_send_once(wave_id)
            # Yield CPU during hardware transmission (no impact on timing)
            while pi.wave_tx_busy():
                time.sleep(0.0005)
            pi.wave_delete(wave_id)
            pi.wave_clear()

        for event_time, pin in events:
            all_pins.add(pin)
            delay_us = int((event_time - last_time) * 1_000_000)

            if delay_us > 0:
                pulses.append(pigpio.pulse(0, 0, delay_us))

            # HIGH pulse for step
            pulses.append(pigpio.pulse(1 << pin, 0, pulse_width_us))
            # LOW pulse (1us minimum to avoid zero-length pulses)
            pulses.append(pigpio.pulse(0, 1 << pin, 1))

            last_time = event_time

            if len(pulses) >= max_pulses_per_wave:
                _flush_pulses()
                pulses = []

        _flush_pulses()

        # Ensure all step pins end LOW
        pi = self.pi
        assert pi is not None
        for p in all_pins:
            pi.write(p, 0)


def create_wave_generator() -> PigpioWaveGenerator | None:
    """
    Create a wave generator if pigpio is available.

    Returns:
        PigpioWaveGenerator instance or None if unavailable
    """
    if not PIGPIO_AVAILABLE:
        return None

    try:
        return PigpioWaveGenerator()
    except (ImportError, RuntimeError) as e:
        print(f"⚠️  Could not initialize pigpio: {e}")
        print("⚠️  Falling back to time.sleep() based timing")
        return None
