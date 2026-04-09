from __future__ import annotations

import math
import re
import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.wiki import WikiPage, WikiPageVersion
from app.models.user import User
from app.schemas.wiki import WikiPageCreate, WikiPageOut, WikiPageUpdate

router = APIRouter()


def _slugify(title: str) -> str:
    slug = title.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    return slug[:200]


@router.get("/project/{project_id}", response_model=dict)
async def list_pages(
    project_id: uuid.UUID,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    total = (
        await db.execute(
            select(func.count())
            .select_from(WikiPage)
            .where(WikiPage.project_id == project_id, WikiPage.deleted_at.is_(None))
        )
    ).scalar_one()
    rows = (
        await db.execute(
            select(WikiPage)
            .where(WikiPage.project_id == project_id, WikiPage.deleted_at.is_(None))
            .order_by(WikiPage.title)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()

    return {
        "data": [WikiPageOut.model_validate(p) for p in rows],
        "meta": {"total": total, "page": page, "page_size": page_size, "pages": math.ceil(total / page_size)},
    }


@router.post("/project/{project_id}", response_model=WikiPageOut, status_code=status.HTTP_201_CREATED)
async def create_page(
    project_id: uuid.UUID,
    body: WikiPageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WikiPage:
    base_slug = _slugify(body.title)
    slug = base_slug
    n = 1
    while True:
        existing = await db.execute(
            select(WikiPage).where(WikiPage.project_id == project_id, WikiPage.slug == slug, WikiPage.deleted_at.is_(None))
        )
        if existing.scalar_one_or_none() is None:
            break
        slug = f"{base_slug}-{n}"
        n += 1

    page = WikiPage(
        id=uuid.uuid4(),
        project_id=project_id,
        slug=slug,
        created_by=current_user.id,
        updated_by=current_user.id,
        **body.model_dump(),
    )
    db.add(page)
    await db.commit()
    await db.refresh(page)
    return page


@router.get("/{page_id}", response_model=WikiPageOut)
async def get_page(
    page_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WikiPage:
    result = await db.execute(select(WikiPage).where(WikiPage.id == page_id, WikiPage.deleted_at.is_(None)))
    page = result.scalar_one_or_none()
    if page is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wiki page not found")
    return page


@router.patch("/{page_id}", response_model=WikiPageOut)
async def update_page(
    page_id: uuid.UUID,
    body: WikiPageUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WikiPage:
    result = await db.execute(select(WikiPage).where(WikiPage.id == page_id, WikiPage.deleted_at.is_(None)))
    page = result.scalar_one_or_none()
    if page is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wiki page not found")

    snapshot = WikiPageVersion(
        id=uuid.uuid4(),
        page_id=page.id,
        version=page.current_version,
        title=page.title,
        content=page.content,
        changed_by=current_user.id,
    )
    db.add(snapshot)

    if body.title is not None:
        page.title = body.title
    if body.content is not None:
        page.content = body.content
    page.updated_by = current_user.id
    page.current_version += 1

    await db.commit()
    await db.refresh(page)
    return page


@router.delete("/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_page(
    page_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(WikiPage).where(WikiPage.id == page_id, WikiPage.deleted_at.is_(None)))
    page = result.scalar_one_or_none()
    if page is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wiki page not found")
    page.deleted_at = datetime.now(timezone.utc)
    await db.commit()
