from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel


class IssueCreate(BaseModel):
    title: str
    description: str | None = None
    type: str = "task"
    priority: str = "medium"
    status_id: uuid.UUID | None = None
    assignee_id: uuid.UUID | None = None
    sprint_id: uuid.UUID | None = None
    parent_id: uuid.UUID | None = None
    story_points: int | None = None
    due_date: date | None = None
    # Enriched story fields
    decisions: str | None = None
    investigations: str | None = None
    test_requirements: str | None = None
    uat_criteria: str | None = None


class IssueUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    type: str | None = None
    priority: str | None = None
    status_id: uuid.UUID | None = None
    assignee_id: uuid.UUID | None = None
    sprint_id: uuid.UUID | None = None
    story_points: int | None = None
    due_date: date | None = None
    decisions: str | None = None
    investigations: str | None = None
    test_requirements: str | None = None
    uat_criteria: str | None = None
    override_reason: str | None = None


class UATSignoffCreate(BaseModel):
    note: str | None = None


class AuditLogOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    action: str
    actor_id: uuid.UUID
    old_value: dict | None
    new_value: dict | None
    note: str | None
    created_at: datetime


class IssueOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    project_id: uuid.UUID
    sequence_number: int
    title: str
    description: str | None
    type: str
    priority: str
    status_id: uuid.UUID | None
    assignee_id: uuid.UUID | None
    reporter_id: uuid.UUID
    sprint_id: uuid.UUID | None
    parent_id: uuid.UUID | None
    story_points: int | None
    due_date: date | None
    decisions: str | None
    investigations: str | None
    test_requirements: str | None
    uat_criteria: str | None
    uat_approved: bool
    uat_approved_by: uuid.UUID | None
    uat_approved_at: datetime | None
    created_at: datetime
    updated_at: datetime


class CommentCreate(BaseModel):
    body: str


class CommentOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    issue_id: uuid.UUID
    author_id: uuid.UUID
    body: str
    created_at: datetime


class SprintCreate(BaseModel):
    name: str
    goal: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class SprintOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    goal: str | None
    status: str
    start_date: date | None
    end_date: date | None
