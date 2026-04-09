from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.database import get_db
from app.dependencies import get_current_user
from app.models.issue import Issue
from app.models.requirement import Requirement, RequirementIssue
from app.models.testcase import RequirementTestCase, TestRun
from app.models.user import User

router = APIRouter()


@router.get("/project/{project_id}")
async def traceability_matrix(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Returns the full traceability matrix for a project:
    requirement → linked issues → linked test cases → latest test run result
    """
    reqs = (
        await db.execute(
            select(Requirement)
            .where(Requirement.project_id == project_id, Requirement.deleted_at.is_(None))
            .order_by(Requirement.sequence_number)
        )
    ).scalars().all()

    rows = []
    for req in reqs:
        # Linked issues
        issue_links = (
            await db.execute(
                select(RequirementIssue).where(RequirementIssue.requirement_id == req.id)
            )
        ).scalars().all()
        issue_ids = [lnk.issue_id for lnk in issue_links]

        issues = []
        if issue_ids:
            issue_rows = (
                await db.execute(select(Issue).where(Issue.id.in_(issue_ids), Issue.deleted_at.is_(None)))
            ).scalars().all()
            issues = [{"id": str(i.id), "sequence_number": i.sequence_number, "title": i.title, "status_id": str(i.status_id)} for i in issue_rows]

        # Linked test cases and their latest run
        tc_links = (
            await db.execute(
                select(RequirementTestCase).where(RequirementTestCase.requirement_id == req.id)
            )
        ).scalars().all()
        tc_ids = [lnk.test_case_id for lnk in tc_links]

        test_coverage = []
        for tc_id in tc_ids:
            latest_run = (
                await db.execute(
                    select(TestRun)
                    .where(TestRun.test_case_id == tc_id)
                    .order_by(TestRun.executed_at.desc())
                    .limit(1)
                )
            ).scalar_one_or_none()

            test_coverage.append({
                "test_case_id": str(tc_id),
                "latest_run_status": latest_run.status if latest_run else None,
                "latest_run_at": latest_run.executed_at.isoformat() if latest_run else None,
            })

        flags = []
        if not issue_ids:
            flags.append("unplanned")
        if not tc_ids:
            flags.append("untested")

        rows.append({
            "req_id": req.req_id,
            "title": req.title,
            "status": req.status,
            "issues": issues,
            "test_coverage": test_coverage,
            "flags": flags,
        })

    return {"data": rows, "meta": {"project_id": str(project_id), "total": len(rows)}}
