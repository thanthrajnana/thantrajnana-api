from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

ALLOWED_TEMPLATE_IDS = {"landing", "portfolio", "login", "product", "blank"}


class ProjectBase(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    template_id: str = Field(default="blank", min_length=1, max_length=80)
    workspace: dict[str, Any]
    html_code: str = Field(default="", max_length=1_000_000)
    css_code: str = Field(default="", max_length=1_000_000)
    javascript_code: str = Field(default="", max_length=1_000_000)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Project name cannot be blank")
        return cleaned

    @field_validator("template_id")
    @classmethod
    def validate_template(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in ALLOWED_TEMPLATE_IDS:
            return "blank"
        return cleaned


class ProjectCreate(ProjectBase):
    pass


class ProjectResponse(ProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime
