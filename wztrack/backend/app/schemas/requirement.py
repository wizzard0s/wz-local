from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class RequirementCreate(BaseModel):
    title: str
    description: str | None = None
    acceptance_criteria: str | None = None
    priority: str = "must"


class RequirementUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    acceptance_criteria: str | None = None
    priority: str | None = None
    status: str | None = None
    change_note: str | None = None


class RequirementOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    project_id: uuid.UUID
    req_id: str
    title: str
    description: str | None
    acceptance_criteria: str | None
    priority: str
    status: str
    current_version: int
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
