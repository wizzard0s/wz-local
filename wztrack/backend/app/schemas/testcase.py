from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class TestPlanCreate(BaseModel):
    name: str
    description: str | None = None
    sprint_id: uuid.UUID | None = None


class TestPlanOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    project_id: uuid.UUID
    sprint_id: uuid.UUID | None
    name: str
    description: str | None
    status: str
    created_by: uuid.UUID
    created_at: datetime


class TestCaseCreate(BaseModel):
    title: str
    preconditions: str | None = None
    steps: list[dict[str, Any]] | None = None
    expected_result: str | None = None


class TestCaseOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    project_id: uuid.UUID
    test_plan_id: uuid.UUID
    title: str
    preconditions: str | None
    steps: list[dict[str, Any]] | None
    expected_result: str | None
    created_by: uuid.UUID
    created_at: datetime


class TestRunCreate(BaseModel):
    status: str
    notes: str | None = None
    issue_id: uuid.UUID | None = None


class TestRunOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    test_case_id: uuid.UUID
    issue_id: uuid.UUID | None
    status: str
    notes: str | None
    executed_by: uuid.UUID
    executed_at: datetime
