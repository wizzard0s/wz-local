from __future__ import annotations

import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.project import Project, ProjectMember, WorkflowState
from app.models.user import User
from app.schemas.project import (
    ProjectCreate,
    ProjectMemberAdd,
    ProjectOut,
    ProjectUpdate,
    WorkflowStateCreate,
    WorkflowStateOut,
)

router = APIRouter()


async def _get_project_or_404(project_id: uuid.UUID, db: AsyncSession) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id, Project.deleted_at.is_(None)))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.get("/", response_model=dict)
async def list_projects(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    # Admins see all projects; others see only projects they are members of
    if current_user.role == "admin":
        base = select(Project).where(Project.deleted_at.is_(None))
        count_q = select(func.count()).select_from(Project).where(Project.deleted_at.is_(None))
    else:
        base = (
            select(Project)
            .join(ProjectMember, ProjectMember.project_id == Project.id)
            .where(Project.deleted_at.is_(None), ProjectMember.user_id == current_user.id)
        )
        count_q = (
            select(func.count())
            .select_from(Project)
            .join(ProjectMember, ProjectMember.project_id == Project.id)
            .where(Project.deleted_at.is_(None), ProjectMember.user_id == current_user.id)
        )

    total = (await db.execute(count_q)).scalar_one()
    rows = (await db.execute(base.offset((page - 1) * page_size).limit(page_size))).scalars().all()

    return {
        "data": [ProjectOut.model_validate(p) for p in rows],
        "meta": {"total": total, "page": page, "page_size": page_size, "pages": math.ceil(total / page_size)},
    }


@router.post("/", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreate,
    current_user: User = Depends(require_roles("admin", "manager")),
    db: AsyncSession = Depends(get_db),
) -> Project:
    existing = await db.execute(select(Project).where(Project.key == body.key.upper()))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Project key already exists")

    project = Project(id=uuid.uuid4(), key=body.key.upper(), name=body.name, description=body.description, owner_id=current_user.id)
    db.add(project)
    await db.flush()

    # Add creator as member with manager role
    db.add(ProjectMember(project_id=project.id, user_id=current_user.id, role="manager"))

    # Create default workflow states
    defaults = [
        WorkflowState(id=uuid.uuid4(), project_id=project.id, name="Backlog", category="backlog", position=0, color="#6B7280"),
        WorkflowState(id=uuid.uuid4(), project_id=project.id, name="In Progress", category="in_progress", position=1, color="#3B82F6"),
        WorkflowState(id=uuid.uuid4(), project_id=project.id, name="In Review", category="review", position=2, color="#F59E0B"),
        WorkflowState(id=uuid.uuid4(), project_id=project.id, name="Done", category="done", position=3, color="#10B981"),
    ]
    db.add_all(defaults)
    await db.commit()
    await db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Project:
    return await _get_project_or_404(project_id, db)


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: uuid.UUID,
    body: ProjectUpdate,
    current_user: User = Depends(require_roles("admin", "manager")),
    db: AsyncSession = Depends(get_db),
) -> Project:
    project = await _get_project_or_404(project_id, db)
    if body.name is not None:
        project.name = body.name
    if body.description is not None:
        project.description = body.description
    if body.status is not None:
        project.status = body.status
    await db.commit()
    await db.refresh(project)
    return project


@router.post("/{project_id}/members", status_code=status.HTTP_204_NO_CONTENT)
async def add_member(
    project_id: uuid.UUID,
    body: ProjectMemberAdd,
    current_user: User = Depends(require_roles("admin", "manager")),
    db: AsyncSession = Depends(get_db),
):
    await _get_project_or_404(project_id, db)
    existing = await db.execute(
        select(ProjectMember).where(ProjectMember.project_id == project_id, ProjectMember.user_id == body.user_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already a member")
    db.add(ProjectMember(project_id=project_id, user_id=body.user_id, role=body.role))
    await db.commit()


@router.get("/{project_id}/states", response_model=list[WorkflowStateOut])
async def list_states(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[WorkflowState]:
    rows = (
        await db.execute(
            select(WorkflowState)
            .where(WorkflowState.project_id == project_id)
            .order_by(WorkflowState.position)
        )
    ).scalars().all()
    return list(rows)


@router.post("/{project_id}/states", response_model=WorkflowStateOut, status_code=status.HTTP_201_CREATED)
async def create_state(
    project_id: uuid.UUID,
    body: WorkflowStateCreate,
    current_user: User = Depends(require_roles("admin", "manager")),
    db: AsyncSession = Depends(get_db),
) -> WorkflowState:
    await _get_project_or_404(project_id, db)
    state = WorkflowState(id=uuid.uuid4(), project_id=project_id, **body.model_dump())
    db.add(state)
    await db.commit()
    await db.refresh(state)
    return state
