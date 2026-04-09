from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.issue import AuditLog, Issue
from app.models.project import WorkflowState
from app.models.testcase import TestRun
from app.models.user import User
from app.schemas.issue import IssueCreate, IssueOut, IssueUpdate, UATSignoffCreate, AuditLogOut

router = APIRouter()


async def _next_sequence(project_id: uuid.UUID, db: AsyncSession) -> int:
    result = await db.execute(
        select(func.coalesce(func.max(Issue.sequence_number), 0)).where(Issue.project_id == project_id)
    )
    return result.scalar_one() + 1


async def _check_done_gate(issue: Issue, new_status_id: uuid.UUID, db: AsyncSession) -> None:
    state = (await db.execute(select(WorkflowState).where(WorkflowState.id == new_status_id))).scalar_one_or_none()
    if state is None or state.category != "done":
        return

    pass_count = (
        await db.execute(
            select(func.count())
            .select_from(TestRun)
            .where(TestRun.issue_id == issue.id, TestRun.status == "pass")
        )
    ).scalar_one()

    errors = []
    if pass_count == 0:
        errors.append("no linked passing test run")
    if not issue.uat_approved:
        errors.append("UAT has not been signed off")

    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": {"code": "DONE_GATE_BLOCKED", "message": f"Cannot mark Done: {' and '.join(errors)}"}},
        )


@router.get("/project/{project_id}", response_model=dict)
async def list_issues(
    project_id: uuid.UUID,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    total = (
        await db.execute(
            select(func.count()).select_from(Issue).where(Issue.project_id == project_id, Issue.deleted_at.is_(None))
        )
    ).scalar_one()
    rows = (
        await db.execute(
            select(Issue)
            .where(Issue.project_id == project_id, Issue.deleted_at.is_(None))
            .order_by(Issue.sequence_number)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()

    return {
        "data": [IssueOut.model_validate(i) for i in rows],
        "meta": {"total": total, "page": page, "page_size": page_size, "pages": math.ceil(total / page_size)},
    }


@router.post("/project/{project_id}", response_model=IssueOut, status_code=status.HTTP_201_CREATED)
async def create_issue(
    project_id: uuid.UUID,
    body: IssueCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Issue:
    seq = await _next_sequence(project_id, db)
    issue = Issue(
        id=uuid.uuid4(),
        project_id=project_id,
        sequence_number=seq,
        reporter_id=current_user.id,
        **body.model_dump(),
    )
    db.add(issue)
    await db.commit()
    await db.refresh(issue)
    return issue


@router.get("/{issue_id}", response_model=IssueOut)
async def get_issue(
    issue_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Issue:
    result = await db.execute(select(Issue).where(Issue.id == issue_id, Issue.deleted_at.is_(None)))
    issue = result.scalar_one_or_none()
    if issue is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")
    return issue


@router.patch("/{issue_id}", response_model=IssueOut)
async def update_issue(
    issue_id: uuid.UUID,
    body: IssueUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Issue:
    result = await db.execute(select(Issue).where(Issue.id == issue_id, Issue.deleted_at.is_(None)))
    issue = result.scalar_one_or_none()
    if issue is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")

    old_status = issue.status_id

    update_data = body.model_dump(exclude={"override_reason"}, exclude_none=True)
    for field, value in update_data.items():
        setattr(issue, field, value)

    # Enforce QA gate on status transition to done
    if body.status_id is not None and body.status_id != old_status:
        if body.override_reason:
            if current_user.role not in ("admin", "manager"):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin or manager may override the done gate")
            db.add(AuditLog(
                id=uuid.uuid4(),
                entity_type="issue",
                entity_id=issue.id,
                action="done_gate_override",
                actor_id=current_user.id,
                old_value={"status_id": str(old_status)},
                new_value={"status_id": str(body.status_id)},
                note=body.override_reason,
            ))
        else:
            await _check_done_gate(issue, body.status_id, db)

        db.add(AuditLog(
            id=uuid.uuid4(),
            entity_type="issue",
            entity_id=issue.id,
            action="state_transition",
            actor_id=current_user.id,
            old_value={"status_id": str(old_status)},
            new_value={"status_id": str(body.status_id)},
        ))

    await db.commit()
    await db.refresh(issue)
    return issue


@router.delete("/{issue_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_issue(
    issue_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Issue).where(Issue.id == issue_id, Issue.deleted_at.is_(None)))
    issue = result.scalar_one_or_none()
    if issue is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")
    issue.deleted_at = datetime.now(timezone.utc)
    await db.commit()


@router.post("/{issue_id}/uat-signoff", response_model=IssueOut)
async def uat_signoff(
    issue_id: uuid.UUID,
    body: UATSignoffCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Issue:
    if current_user.role not in ("admin", "manager"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin or manager may sign off UAT")
    result = await db.execute(select(Issue).where(Issue.id == issue_id, Issue.deleted_at.is_(None)))
    issue = result.scalar_one_or_none()
    if issue is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")
    if issue.uat_approved:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="UAT already signed off")
    issue.uat_approved = True
    issue.uat_approved_by = current_user.id
    issue.uat_approved_at = datetime.now(timezone.utc)
    db.add(AuditLog(
        id=uuid.uuid4(),
        entity_type="issue",
        entity_id=issue.id,
        action="uat_signoff",
        actor_id=current_user.id,
        old_value={"uat_approved": False},
        new_value={"uat_approved": True},
        note=body.note,
    ))
    await db.commit()
    await db.refresh(issue)
    return issue


@router.get("/{issue_id}/history", response_model=list[AuditLogOut])
async def issue_history(
    issue_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list:
    result = await db.execute(select(Issue).where(Issue.id == issue_id, Issue.deleted_at.is_(None)))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")
    from app.models.issue import AuditLog as AuditLogModel
    rows = (
        await db.execute(
            select(AuditLogModel)
            .where(AuditLogModel.entity_type == "issue", AuditLogModel.entity_id == issue_id)
            .order_by(AuditLogModel.created_at)
        )
    ).scalars().all()
    return rows
