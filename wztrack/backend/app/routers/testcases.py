from __future__ import annotations

import math
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.testcase import TestCase, TestPlan, TestRun, RequirementTestCase
from app.models.user import User
from app.schemas.testcase import (
    TestCaseCreate,
    TestCaseOut,
    TestPlanCreate,
    TestPlanOut,
    TestRunCreate,
    TestRunOut,
)

router = APIRouter()


# ── Test Plans ────────────────────────────────────────────────────────────────

@router.get("/plans/project/{project_id}", response_model=dict)
async def list_plans(
    project_id: uuid.UUID,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    total = (
        await db.execute(
            select(func.count()).select_from(TestPlan).where(TestPlan.project_id == project_id, TestPlan.deleted_at.is_(None))
        )
    ).scalar_one()
    rows = (
        await db.execute(
            select(TestPlan)
            .where(TestPlan.project_id == project_id, TestPlan.deleted_at.is_(None))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()

    return {
        "data": [TestPlanOut.model_validate(p) for p in rows],
        "meta": {"total": total, "page": page, "page_size": page_size, "pages": math.ceil(total / page_size)},
    }


@router.post("/plans/project/{project_id}", response_model=TestPlanOut, status_code=status.HTTP_201_CREATED)
async def create_plan(
    project_id: uuid.UUID,
    body: TestPlanCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TestPlan:
    plan = TestPlan(id=uuid.uuid4(), project_id=project_id, created_by=current_user.id, **body.model_dump())
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan


# ── Test Cases ────────────────────────────────────────────────────────────────

@router.post("/cases/plan/{plan_id}", response_model=TestCaseOut, status_code=status.HTTP_201_CREATED)
async def create_case(
    plan_id: uuid.UUID,
    body: TestCaseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TestCase:
    plan = (await db.execute(select(TestPlan).where(TestPlan.id == plan_id, TestPlan.deleted_at.is_(None)))).scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test plan not found")

    case = TestCase(
        id=uuid.uuid4(),
        project_id=plan.project_id,
        test_plan_id=plan_id,
        created_by=current_user.id,
        **body.model_dump(),
    )
    db.add(case)
    await db.commit()
    await db.refresh(case)
    return case


@router.get("/cases/{case_id}", response_model=TestCaseOut)
async def get_case(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TestCase:
    result = await db.execute(select(TestCase).where(TestCase.id == case_id, TestCase.deleted_at.is_(None)))
    case = result.scalar_one_or_none()
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test case not found")
    return case


# ── Test Runs ─────────────────────────────────────────────────────────────────

@router.post("/runs/case/{case_id}", response_model=TestRunOut, status_code=status.HTTP_201_CREATED)
async def create_run(
    case_id: uuid.UUID,
    body: TestRunCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TestRun:
    if body.status == "pass" and current_user.role not in ("qa", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only qa or admin may mark a test run as pass")

    case = (await db.execute(select(TestCase).where(TestCase.id == case_id, TestCase.deleted_at.is_(None)))).scalar_one_or_none()
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test case not found")

    run = TestRun(
        id=uuid.uuid4(),
        test_case_id=case_id,
        executed_by=current_user.id,
        **body.model_dump(),
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    return run


@router.get("/runs/case/{case_id}", response_model=list[TestRunOut])
async def list_runs(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[TestRun]:
    rows = (
        await db.execute(
            select(TestRun).where(TestRun.test_case_id == case_id).order_by(TestRun.executed_at.desc())
        )
    ).scalars().all()
    return list(rows)


# ── Requirement ↔ Test Case links ─────────────────────────────────────────────

@router.post("/links/requirement/{req_id}/case/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def link_requirement(
    req_id: uuid.UUID,
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(RequirementTestCase).where(
            RequirementTestCase.requirement_id == req_id,
            RequirementTestCase.test_case_id == case_id,
        )
    )
    if existing.scalar_one_or_none():
        return  # idempotent

    db.add(RequirementTestCase(requirement_id=req_id, test_case_id=case_id))
    await db.commit()
