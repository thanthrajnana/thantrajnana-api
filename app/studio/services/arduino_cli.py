from __future__ import annotations

import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from app.studio.boards import SUPPORTED_BOARDS
from app.core.config import settings
from app.studio.schemas import ToolchainResult


class ArduinoCliUnavailableError(RuntimeError):
    pass


class DeviceUploadDisabledError(RuntimeError):
    pass


def _cli_executable() -> str:
    configured = settings.arduino_cli_path
    resolved = shutil.which(configured)
    if resolved:
        return resolved

    configured_path = Path(configured)
    if configured_path.is_file():
        return str(configured_path.resolve())

    raise ArduinoCliUnavailableError(
        "arduino-cli was not found. Install Arduino CLI or set ARDUINO_CLI_PATH."
    )


def toolchain_status() -> tuple[bool, str | None, str]:
    try:
        executable = _cli_executable()
        completed = subprocess.run(
            [executable, "version"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        output = (completed.stdout or completed.stderr).strip()
        if completed.returncode == 0:
            return True, output or None, "Arduino CLI is ready for compilation."
        return False, output or None, "Arduino CLI returned an error."
    except (ArduinoCliUnavailableError, OSError, subprocess.SubprocessError) as exc:
        return False, None, str(exc)


def _write_sketch(temp_root: str, code: str) -> Path:
    sketch_dir = Path(temp_root) / "ThantrajnanaSketch"
    sketch_dir.mkdir(parents=True, exist_ok=True)
    (sketch_dir / "ThantrajnanaSketch.ino").write_text(code, encoding="utf-8")
    return sketch_dir


def _run(command: list[str]) -> ToolchainResult:
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=settings.arduino_cli_timeout_seconds,
            check=False,
        )
        duration_ms = int((time.perf_counter() - started) * 1000)
        return ToolchainResult(
            success=completed.returncode == 0,
            command=command,
            stdout=completed.stdout,
            stderr=completed.stderr,
            duration_ms=duration_ms,
        )
    except subprocess.TimeoutExpired as exc:
        duration_ms = int((time.perf_counter() - started) * 1000)
        return ToolchainResult(
            success=False,
            command=command,
            stdout=(exc.stdout or "") if isinstance(exc.stdout, str) else "",
            stderr=f"Command timed out after {settings.arduino_cli_timeout_seconds} seconds.",
            duration_ms=duration_ms,
        )


def compile_sketch(board_id: str, code: str) -> ToolchainResult:
    executable = _cli_executable()
    board = SUPPORTED_BOARDS[board_id]

    with tempfile.TemporaryDirectory(prefix="thantrajnana-compile-") as temp_root:
        sketch_dir = _write_sketch(temp_root, code)
        command = [
            executable,
            "compile",
            "--fqbn",
            board.fqbn,
            "--warnings",
            "default",
            str(sketch_dir),
        ]
        return _run(command)


def upload_sketch(board_id: str, port: str, code: str) -> ToolchainResult:
    if not settings.enable_device_upload:
        raise DeviceUploadDisabledError(
            "Device upload is disabled. Set ENABLE_DEVICE_UPLOAD=true in .env."
        )

    executable = _cli_executable()
    board = SUPPORTED_BOARDS[board_id]

    with tempfile.TemporaryDirectory(prefix="thantrajnana-upload-") as temp_root:
        sketch_dir = _write_sketch(temp_root, code)
        command = [
            executable,
            "compile",
            "--upload",
            "--port",
            port,
            "--fqbn",
            board.fqbn,
            "--warnings",
            "default",
            str(sketch_dir),
        ]
        return _run(command)
