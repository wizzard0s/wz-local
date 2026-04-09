from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class ProjectCreate(BaseModel):
    key: str
    name: str
    description: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None


class ProjectOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    key: str
    name: str
    description: str | None
    status: str
    owner_id: uuid.UUID
    created_at: datetime


class WorkflowStateCreate(BaseModel):
    name: str
    category: str
    position: int = 0
    color: str | None = None


class WorkflowStateOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    category: str
    position: int
    color: str | None


class ProjectMemberAdd(BaseModel):
    user_id: uuid.UUID
    role: str = "developer"
