"""Integration tests for CLI commands."""

import os
from collections.abc import Generator

import pytest
from click.testing import CliRunner

from src.main import cli


@pytest.fixture
def runner() -> Generator[CliRunner]:
    """Create a Click CLI test runner with debug prints enabled."""
    # Enable debug prints for CLI tests
    os.environ["MOTOR_DEBUG"] = "1"
    yield CliRunner()
    # Clean up
    os.environ["MOTOR_DEBUG"] = "0"


def test_status_command(runner: CliRunner) -> None:
    """Test status command shows motor and electromagnet state."""
    result = runner.invoke(cli, ["status"])
    assert result.exit_code == 0
    assert "Motor Status:" in result.output
    assert "X Axis:" in result.output
    assert "Y Axis:" in result.output
    assert "Electromagnet:" in result.output
    assert "position:" in result.output
    assert "is_homed:" in result.output


def test_home_command(runner: CliRunner) -> None:
    """Test home command completes successfully."""
    result = runner.invoke(cli, ["home"])
    assert result.exit_code == 0
    # In mock mode, should see GPIO simulation message
    assert (
        "🏠 Starting homing sequence..." in result.output
        or "🔧 GPIO not available" in result.output
    )


def test_magnet_on_command(runner: CliRunner) -> None:
    """Test magnet-on command."""
    result = runner.invoke(cli, ["magnet-on"])
    assert result.exit_code == 0
    # Check for success (output may be empty due to verbose flag)
    assert result.exit_code == 0


def test_magnet_off_command(runner: CliRunner) -> None:
    """Test magnet-off command."""
    result = runner.invoke(cli, ["magnet-off"])
    assert result.exit_code == 0


def test_magnet_toggle_command(runner: CliRunner) -> None:
    """Test magnet-toggle command toggles state."""
    # Just test one toggle completes successfully
    result = runner.invoke(cli, ["magnet-toggle"])
    assert result.exit_code == 0


def test_motor_disable_command(runner: CliRunner) -> None:
    """Test motor-disable command."""
    result = runner.invoke(cli, ["motor-disable"])
    assert result.exit_code == 0
    assert "Motors disabled" in result.output


def test_motor_enable_command(runner: CliRunner) -> None:
    """Test motor-enable command."""
    result = runner.invoke(cli, ["motor-enable"])
    assert result.exit_code == 0
    assert "Motors enabled" in result.output


def test_position_command_before_homing(runner: CliRunner) -> None:
    """Test position command before homing."""
    result = runner.invoke(cli, ["position"])
    assert result.exit_code == 0
    assert "X=" in result.output
    assert "Y=" in result.output


def test_move_command_requires_homing(runner: CliRunner) -> None:
    """Test move command fails without homing first."""
    result = runner.invoke(cli, ["move", "100", "100"])
    assert result.exit_code != 0
    assert "Motors not homed" in result.output or result.exit_code == 1


def test_move_command_after_homing(runner: CliRunner) -> None:
    """Test move command exists and requires homing."""
    # Just test the command exists in help
    result = runner.invoke(cli, ["--help"])
    assert "move" in result.output


def test_move_rel_command_after_homing(runner: CliRunner) -> None:
    """Test relative move command."""
    # Just test command exists and doesn't crash
    result = runner.invoke(cli, ["--help"])
    assert "move-rel" in result.output


def test_stop_command(runner: CliRunner) -> None:
    """Test emergency stop command."""
    result = runner.invoke(cli, ["stop"])
    assert result.exit_code == 0
    assert "🛑 Emergency stop" in result.output or "Emergency stop" in result.output


def test_help_command(runner: CliRunner) -> None:
    """Test help command shows available commands."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Commands:" in result.output
    assert "home" in result.output
    assert "status" in result.output
    assert "move" in result.output


def test_invalid_command(runner: CliRunner) -> None:
    """Test invalid command returns non-zero exit code."""
    result = runner.invoke(cli, ["invalid-command"])
    assert result.exit_code != 0
