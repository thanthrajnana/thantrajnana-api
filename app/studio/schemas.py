from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.studio.boards import SUPPORTED_BOARDS


class ProjectBase(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    board_id: str
    workspace: dict[str, Any]
    generated_code: str = Field(default="", max_length=300_000)

    @field_validator("board_id")
    @classmethod
    def validate_board(cls, value: str) -> str:
        if value not in SUPPORTED_BOARDS:
            raise ValueError("Unsupported board")
        return value


class ProjectCreate(ProjectBase):
    pass


class ProjectResponse(ProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime


class BoardResponse(BaseModel):
    id: str
    name: str
    family: str
    fqbn: str


class ToolchainStatusResponse(BaseModel):
    available: bool
    version: str | None
    upload_enabled: bool
    message: str


class CompileRequest(BaseModel):
    board_id: str
    code: str = Field(min_length=1, max_length=300_000)

    @field_validator("board_id")
    @classmethod
    def validate_board(cls, value: str) -> str:
        if value not in SUPPORTED_BOARDS:
            raise ValueError("Unsupported board")
        return value


class UploadRequest(CompileRequest):
    port: str = Field(min_length=1, max_length=260)


class ToolchainResult(BaseModel):
    success: bool
    command: list[str]
    stdout: str
    stderr: str
    duration_ms: int


class SerialPortResponse(BaseModel):
    device: str
    description: str
    hwid: str
