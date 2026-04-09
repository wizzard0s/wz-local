from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: EmailStr
    display_name: str
    role: str
    is_active: bool
    created_at: datetime


class UserCreate(BaseModel):
    email: EmailStr
    display_name: str
    password: str
    role: str = "viewer"


class UserUpdate(BaseModel):
    display_name: str | None = None
    role: str | None = None
    is_active: bool | None = None
