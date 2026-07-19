from fastapi import APIRouter, HTTPException
from serial.tools import list_ports

from app.core.config import settings
from app.studio.boards import SUPPORTED_BOARDS
from app.studio.schemas import (
    BoardResponse,
    CompileRequest,
    SerialPortResponse,
    ToolchainResult,
    ToolchainStatusResponse,
    UploadRequest,
)
from app.studio.services.arduino_cli import (
    ArduinoCliUnavailableError,
    DeviceUploadDisabledError,
    compile_sketch,
    toolchain_status,
    upload_sketch,
)

router = APIRouter(prefix="/toolchain", tags=["Studio Toolchain"])


@router.get("/boards", response_model=list[BoardResponse])
def list_supported_boards() -> list[BoardResponse]:
    return [
        BoardResponse(id=board.id, name=board.name, family=board.family, fqbn=board.fqbn)
        for board in SUPPORTED_BOARDS.values()
    ]


@router.get("/status", response_model=ToolchainStatusResponse)
def get_toolchain_status() -> ToolchainStatusResponse:
    available, version, message = toolchain_status()
    return ToolchainStatusResponse(
        available=available,
        version=version,
        upload_enabled=settings.enable_device_upload,
        message=message,
    )


@router.get("/ports", response_model=list[SerialPortResponse])
def get_serial_ports() -> list[SerialPortResponse]:
    return [
        SerialPortResponse(
            device=port.device,
            description=port.description or "Serial device",
            hwid=port.hwid or "",
        )
        for port in list_ports.comports()
    ]


@router.post("/compile", response_model=ToolchainResult)
def compile_code(payload: CompileRequest) -> ToolchainResult:
    try:
        return compile_sketch(payload.board_id, payload.code)
    except ArduinoCliUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/upload", response_model=ToolchainResult)
def upload_code(payload: UploadRequest) -> ToolchainResult:
    available_ports = {port.device for port in list_ports.comports()}
    if payload.port not in available_ports:
        raise HTTPException(
            status_code=400,
            detail="The selected serial port is not currently available.",
        )
    try:
        return upload_sketch(payload.board_id, payload.port, payload.code)
    except DeviceUploadDisabledError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ArduinoCliUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
