from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.requirement import Requirement, RequirementVersion
from app.models.user import User
from app.schemas.requirement import RequirementCreate, RequirementOut, RequirementUpdate

router = APIRouter()


async def _next_seq(project_id: uuid.UUID, db: AsyncSession) -> int:
    result = await db.execute(
        select(func.coalesce(func.max(Requirement.sequence_number), 0)).where(Requirement.project_id == project_id)
    )
    return result.scalar_one() + 1


async def _get_project_key(project_id: uuid.UUID, db: AsyncSession) -> str:
    from app.models.project import Project
    result = await db.execute(select(Project.key).where(Project.id == project_id))
    key = result.scalar_one_or_none()
    if key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return key


@router.get("/project/{project_id}", response_model=dict)
async def list_requirements(
    project_id: uuid.UUID,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    total = (
        await db.execute(
            select(func.count())
            .select_from(Requirement)
            .where(Requirement.project_id == project_id, Requirement.deleted_at.is_(None))
        )
    ).scalar_one()
    rows = (
        await db.execute(
            select(Requirement)
            .where(Requirement.project_id == project_id, Requirement.deleted_at.is_(None))
            .order_by(Requirement.sequence_number)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()

    return {
        "data": [RequirementOut.model_validate(r) for r in rows],
        "meta": {"total": total, "page": page, "page_size": page_size, "pages": math.ceil(total / page_size)},
    }


@router.post("/project/{project_id}", response_model=RequirementOut, status_code=status.HTTP_201_CREATED)
async def create_requirement(
    project_id: uuid.UUID,
    body: RequirementCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Requirement:
    key = await _get_project_key(project_id, db)
    seq = await _next_seq(project_id, db)
    req_id = f"REQ-{key}-{seq:03d}"

    req = Requirement(
        id=uuid.uuid4(),
        project_id=project_id,
        sequence_number=seq,
        req_id=req_id,
        created_by=current_user.id,
        **body.model_dump(),
    )
    db.add(req)
    await db.commit()
    await db.refresh(req)
    return req


@router.get("/{req_id}", response_model=RequirementOut)
async def get_requirement(
    req_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Requirement:
    result = await db.execute(select(Requirement).where(Requirement.id == req_id, Requirement.deleted_at.is_(None)))
    req = result.scalar_one_or_none()
    if req is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requirement not found")
    return req


@router.patch("/{req_id}", response_model=RequirementOut)
async def update_requirement(
    req_id: uuid.UUID,
    body: RequirementUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Requirement:
    result = await db.execute(select(Requirement).where(Requirement.id == req_id, Requirement.deleted_at.is_(None)))
    req = result.scalar_one_or_none()
    if req is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requirement not found")

    if req.status in ("approved", "implemented", "verified") and current_user.role not in ("admin", "manager"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager approval required to change this requirement")

    # Save version snapshot
    version_snapshot = RequirementVersion(
        id=uuid.uuid4(),
        requirement_id=req.id,
        version=req.current_version,
        title=req.title,
        description=req.description,
        acceptance_criteria=req.acceptance_criteria,
        changed_by=current_user.id,
        change_note=body.change_note,
    )
    db.add(version_snapshot)

    update_data = body.model_dump(exclude={"change_note"}, exclude_none=True)
    for field, value in update_data.items():
        setattr(req, field, value)
    req.current_version += 1

    await db.commit()
    await db.refresh(req)
    return req
