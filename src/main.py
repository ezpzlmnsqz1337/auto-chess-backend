#!/usr/bin/env python3
"""Main application for controlling the XY carriage with stepper motors.

Controls movement of electromagnet under a chess board.
"""

import sys

import click
from gpiozero import Device
from gpiozero.pins.mock import MockFactory

from src import config
from src.motor import Electromagnet, MotorController, StepperMotor
from src.reed_switch_controller import ReedSwitchController

# Use mock pin factory if no real GPIO hardware is available
try:
    Device.ensure_pin_factory()
except Exception:
    Device.pin_factory = MockFactory()


def create_controller() -> MotorController:
    """Create and initialize the motor controller with configuration."""
    motor_x = StepperMotor(
        step_pin=config.MOTOR_X_STEP_PIN,
        dir_pin=config.MOTOR_X_DIR_PIN,
        home_pin=config.MOTOR_X_HOME_PIN,
        enable_pin=config.MOTOR_X_ENABLE_PIN,
        invert_direction=config.MOTOR_X_INVERT,
        max_position=config.MAX_X_POSITION,
        step_delay=config.STEP_DELAY,
        step_pulse_duration=config.STEP_PULSE_DURATION,
    )

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

    electromagnet = Electromagnet(
        pin=config.ELECTROMAGNET_PIN,
        active_high=config.ELECTROMAGNET_ACTIVE_HIGH,
    )

    return MotorController(
        motor_x,
        motor_y,
        electromagnet,
        enable_acceleration=config.ENABLE_ACCELERATION,
        min_step_delay=config.MIN_STEP_DELAY,
        max_step_delay=config.MAX_STEP_DELAY,
        accel_steps=config.ACCELERATION_STEPS,
    )


@click.group()
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Control XY carriage with stepper motors for chess board electromagnet."""
    ctx.ensure_object(dict)
    ctx.obj["controller"] = create_controller()


@cli.command()
@click.option(
    "--step-delay",
    type=float,
    default=config.HOME_STEP_DELAY,
    help="Step delay during homing (seconds)",
)
@click.pass_context
def home(ctx: click.Context, step_delay: float) -> None:
    """Home all motors."""
    controller: MotorController = ctx.obj["controller"]
    try:
        controller.home_all(
            home_direction_x=config.HOME_DIRECTION_X,
            home_direction_y=config.HOME_DIRECTION_Y,
            home_step_delay=step_delay,
        )
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("x", type=int)
@click.argument("y", type=int)
@click.pass_context
def move(ctx: click.Context, x: int, y: int) -> None:
    """Move to absolute position."""
    controller: MotorController = ctx.obj["controller"]
    try:
        controller.move_to(x, y)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command("move-rel")
@click.option("--dx", type=int, default=0, help="Steps on X axis")
@click.option("--dy", type=int, default=0, help="Steps on Y axis")
@click.pass_context
def move_rel(ctx: click.Context, dx: int, dy: int) -> None:
    """Move relative to current position."""
    controller: MotorController = ctx.obj["controller"]
    try:
        click.echo(f"Moving relative: dx={dx}, dy={dy}")
        controller.move_relative(dx, dy)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def position(ctx: click.Context) -> None:
    """Get current position."""
    controller: MotorController = ctx.obj["controller"]
    try:
        x, y = controller.get_position()
        click.echo(f"Current position: X={x}, Y={y}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Get detailed motor and electromagnet status."""
    controller: MotorController = ctx.obj["controller"]
    try:
        status = controller.get_status()
        click.echo("Motor Status:")
        click.echo("  X Axis:")
        for key, value in status["x_axis"].items():
            click.echo(f"    {key}: {value}")
        click.echo("  Y Axis:")
        for key, value in status["y_axis"].items():
            click.echo(f"    {key}: {value}")
        if "electromagnet" in status:
            click.echo("  Electromagnet:")
            for key, value in status["electromagnet"].items():
                click.echo(f"    {key}: {value}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command("magnet-on")
@click.pass_context
def magnet_on(ctx: click.Context) -> None:
    """Turn electromagnet on."""
    controller: MotorController = ctx.obj["controller"]
    try:
        controller.magnet_on()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command("magnet-off")
@click.pass_context
def magnet_off(ctx: click.Context) -> None:
    """Turn electromagnet off."""
    controller: MotorController = ctx.obj["controller"]
    try:
        controller.magnet_off()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command("magnet-toggle")
@click.pass_context
def magnet_toggle(ctx: click.Context) -> None:
    """Toggle electromagnet."""
    controller: MotorController = ctx.obj["controller"]
    try:
        controller.magnet_toggle()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def stop(ctx: click.Context) -> None:
    """Emergency stop all motors and turn off electromagnet."""
    controller: MotorController = ctx.obj["controller"]
    try:
        controller.emergency_stop()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command("motor-enable")
@click.pass_context
def motor_enable(ctx: click.Context) -> None:
    """Enable motors (allows movement)."""
    controller: MotorController = ctx.obj["controller"]
    try:
        controller.motor_x.enable()
        controller.motor_y.enable()
        click.echo("Motors enabled")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command("motor-disable")
@click.pass_context
def motor_disable(ctx: click.Context) -> None:
    """Disable motors (saves power, allows manual movement)."""
    controller: MotorController = ctx.obj["controller"]
    try:
        controller.motor_x.disable()
        controller.motor_y.disable()
        click.echo("Motors disabled - you can now move carriage manually")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command("reed-scan")
@click.option("--continuous", "-c", is_flag=True, help="Continuously scan and display changes")
@click.option("--rate", "-r", type=int, default=5, help="Scans per second for continuous mode")
def reed_scan(continuous: bool, rate: int) -> None:
    """Scan reed switches to detect piece positions."""
    reed = ReedSwitchController()
    try:
        if continuous:
            click.echo(f"📡 Continuous scanning at {rate} Hz. Press Ctrl+C to stop.\n")
            scan_interval = 1.0 / rate
            previous_state = [False] * 64

            while True:
                current_state = reed.scan_with_debounce()

                # Check for changes
                changes = []
                for i in range(64):
                    if current_state[i] != previous_state[i]:
                        row, col = reed._index_to_square(i)
                        square = f"{chr(97 + col)}{row + 1}"
                        if current_state[i]:
                            changes.append(f"✅ {square} occupied")
                        else:
                            changes.append(f"❌ {square} empty")

                if changes:
                    for change in changes:
                        click.echo(change)

                previous_state = current_state
                click.pause(scan_interval)
        else:
            # Single scan
            reed.scan_with_debounce()
            occupied = reed.get_occupied_squares()
            click.echo(f"\n📊 Board state ({len(occupied)} pieces detected):\n")
            click.echo(reed.get_board_state_fen_like())

            if occupied:
                click.echo("\n✅ Occupied squares:")
                for row, col in occupied:
                    square = f"{chr(97 + col)}{row + 1}"
                    click.echo(f"  - {square}")
    except KeyboardInterrupt:
        click.echo("\n\n⏹️  Scanning stopped")
    finally:
        reed.close()


@cli.command("reed-wait-move")
@click.option("--timeout", "-t", type=float, default=30.0, help="Timeout in seconds")
def reed_wait_move(timeout: float) -> None:
    """Wait for a human player to make a move."""
    reed = ReedSwitchController()
    try:
        result = reed.wait_for_move(timeout)
        if result:
            from_square, to_square = result
            from_sq = f"{chr(97 + from_square[1])}{from_square[0] + 1}"
            to_sq = f"{chr(97 + to_square[1])}{to_square[0] + 1}"
            click.echo(f"\n🎯 Move detected: {from_sq} → {to_sq}")
        else:
            click.echo("\n⏱️ Timeout - no move detected")
            sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\n\n⏹️  Move detection cancelled")
        sys.exit(1)
    finally:
        reed.close()


@cli.command("reed-test")
@click.argument("square", type=str)
def reed_test(square: str) -> None:
    """Test a specific square's reed switch (e.g., 'e4', 'a1')."""
    if len(square) != 2 or square[0] not in "abcdefgh" or square[1] not in "12345678":
        click.echo("❌ Invalid square format. Use notation like 'e4', 'a1', 'h8'")
        sys.exit(1)

    col = ord(square[0]) - 97  # a=0, b=1, ..., h=7
    row = int(square[1]) - 1  # 1=0, 2=1, ..., 8=7

    reed = ReedSwitchController()
    try:
        click.echo(f"🔍 Testing square {square} (row={row}, col={col})...")
        click.echo("Place a magnetic piece on the square and remove it repeatedly.\n")

        for _ in range(20):
            state = reed.read_square(row, col)
            symbol = "🟢" if state else "⚫"
            click.echo(f"{symbol} {square}: {'OCCUPIED' if state else 'EMPTY'}")
            click.pause(0.2)

    except KeyboardInterrupt:
        click.echo("\n\n⏹️  Test stopped")
    finally:
        reed.close()


@cli.command()
@click.option(
    "--pattern",
    type=click.Choice(["square", "diagonals", "snake", "all"], case_sensitive=False),
    default="all",
    help="Pattern to execute (default: all)",
)
@click.option(
    "--no-home",
    is_flag=True,
    help="Skip automatic homing (use if already homed)",
)
@click.pass_context
def demo(ctx: click.Context, pattern: str, no_home: bool) -> None:
    """Execute calibration demo patterns (square, diagonals, snake).

    This command automatically homes the motors first (unless --no-home is used),
    then executes the selected movement pattern for calibration and testing.
    """
    from demo_patterns import (
        execute_pattern,
        get_diagonal_patterns,
        get_edge_square_pattern,
        get_snake_pattern,
    )

    controller: MotorController = ctx.obj["controller"]

    try:
        # Auto-home unless explicitly skipped
        if not no_home:
            click.echo("Homing motors first...")
            controller.home_all(
                home_direction_x=config.HOME_DIRECTION_X,
                home_direction_y=config.HOME_DIRECTION_Y,
                home_step_delay=config.HOME_STEP_DELAY,
            )
            click.echo("✓ Homing complete\n")

        # Execute requested pattern(s)
        if pattern in ("square", "all"):
            click.echo("Executing SQUARE pattern (board perimeter)...")
            positions = get_edge_square_pattern()
            execute_pattern(controller, positions)
            click.echo()

        if pattern in ("diagonals", "all"):
            click.echo("Executing DIAGONALS pattern (4 major diagonals)...")
            diagonals = get_diagonal_patterns()
            for start, end, name in diagonals:
                click.echo(f"  Diagonal: {name}")
                execute_pattern(controller, [start, end], verbose=False)
            click.echo("✓ All diagonals complete")
            click.echo()

        if pattern in ("snake", "all"):
            click.echo("Executing SNAKE pattern (all 64 squares)...")
            positions = get_snake_pattern()
            execute_pattern(controller, positions)
            click.echo()

        click.echo("✓ Demo complete!")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def interactive(ctx: click.Context) -> None:
    """Interactive control mode."""
    controller: MotorController = ctx.obj["controller"]
    interactive_mode(controller)


def interactive_mode(controller: MotorController) -> None:
    """Interactive control mode for testing and manual movement."""
    click.echo("Interactive Mode - Type 'help' for commands")
    click.echo(f"Max positions: X={config.MAX_X_POSITION}, Y={config.MAX_Y_POSITION}")

    while True:
        try:
            cmd = input("\n> ").strip().lower()

            if not cmd or cmd == "help":
                click.echo(
                    """
Commands:
  home              - Home all motors
  pos               - Show current position
  move X Y          - Move to absolute position
  movex STEPS       - Move X axis by steps (relative)
  movey STEPS       - Move Y axis by steps (relative)
  magnet on         - Turn electromagnet on
  magnet off        - Turn electromagnet off
  magnet toggle     - Toggle electromagnet
  motor enable      - Enable motors
  motor disable     - Disable motors (manual movement allowed)
  status            - Show motor and magnet status
  stop              - Emergency stop
  exit              - Exit interactive mode
"""
                )

            elif cmd == "exit":
                break

            elif cmd == "home":
                controller.home_all(
                    home_direction_x=config.HOME_DIRECTION_X,
                    home_direction_y=config.HOME_DIRECTION_Y,
                    home_step_delay=config.HOME_STEP_DELAY,
                )

            elif cmd == "pos":
                x, y = controller.get_position()
                click.echo(f"Position: X={x}, Y={y}")

            elif cmd.startswith("move "):
                parts = cmd.split()
                if len(parts) == 3:
                    x, y = int(parts[1]), int(parts[2])
                    controller.move_to(x, y)
                else:
                    click.echo("Usage: move X Y")

            elif cmd.startswith("movex "):
                steps = int(cmd.split()[1])
                controller.move_relative(dx=steps)

            elif cmd.startswith("movey "):
                steps = int(cmd.split()[1])
                controller.move_relative(dy=steps)

            elif cmd == "status":
                status = controller.get_status()
                click.echo("Motor Status:")
                click.echo("  X Axis:")
                for key, value in status["x_axis"].items():
                    click.echo(f"    {key}: {value}")
                click.echo("  Y Axis:")
                for key, value in status["y_axis"].items():
                    click.echo(f"    {key}: {value}")
                if "electromagnet" in status:
                    click.echo("  Electromagnet:")
                    for key, value in status["electromagnet"].items():
                        click.echo(f"    {key}: {value}")

            elif cmd == "magnet on":
                controller.magnet_on()

            elif cmd == "magnet off":
                controller.magnet_off()

            elif cmd == "magnet toggle":
                controller.magnet_toggle()

            elif cmd == "motor enable":
                controller.motor_x.enable()
                controller.motor_y.enable()
                click.echo("Motors enabled")

            elif cmd == "motor disable":
                controller.motor_x.disable()
                controller.motor_y.disable()
                click.echo("Motors disabled - you can now move carriage manually")

            elif cmd == "stop":
                controller.emergency_stop()

            else:
                click.echo("Unknown command. Type 'help' for available commands.")

        except ValueError as e:
            click.echo(f"Invalid input: {e}", err=True)
        except Exception as e:
            click.echo(f"Error: {e}", err=True)


if __name__ == "__main__":
    cli()
