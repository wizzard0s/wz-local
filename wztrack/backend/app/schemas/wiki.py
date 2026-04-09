from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class WikiPageCreate(BaseModel):
    title: str
    content: str | None = None
    template_type: str = "blank"
    parent_id: uuid.UUID | None = None


class WikiPageUpdate(BaseModel):
    title: str | None = None
    content: str | None = None


class WikiPageOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    project_id: uuid.UUID
    parent_id: uuid.UUID | None
    slug: str
    title: str
    content: str | None
    template_type: str
    current_version: int
    created_by: uuid.UUID
    updated_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
