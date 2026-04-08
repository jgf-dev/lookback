import asyncio
from collections.abc import Sequence

import anyio
from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_async_db, get_db
from app.models.db_models import (
    AuditLog,
    CapturedItem,
    CapturedItemEnrichedContent,
    CapturedItemUserContent,
    ItemRelationship,
)
from app.models.schemas import CapturedItemCreate, CapturedItemRead, CapturedItemUpdate

router = APIRouter(prefix="/api")


def db_dependency(request: Request):
    yield from get_db(request.app.state.session_factory)


async def async_db_dependency(request: Request):
    async for db in get_async_db(request.app.state.async_session_factory):
        yield db


def serialize_relationships(
    relationships: Sequence[ItemRelationship],
) -> list[dict]:
    serialized: list[dict] = []
    for relation in relationships:
        serialized.append(
            {
                "target_item_id": relation.target_item_id,
                "relationship_type": relation.relationship_type,
                "confidence": relation.confidence,
                "provenance": relation.provenance or {},
            }
        )
    return serialized


def get_item_with_content(db: Session, item_id: int) -> CapturedItem:
    item = (
        db.query(CapturedItem)
        .options(joinedload(CapturedItem.user_content), joinedload(CapturedItem.enriched_content))
        .filter(CapturedItem.id == item_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


async def async_get_item_with_content(db: AsyncSession, item_id: int) -> CapturedItem:
    result = await db.execute(
        select(CapturedItem)
        .options(joinedload(CapturedItem.user_content), joinedload(CapturedItem.enriched_content))
        .filter(CapturedItem.id == item_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


def get_outbound_relationships(db: Session, item_id: int) -> list[ItemRelationship]:
    return db.query(ItemRelationship).filter(ItemRelationship.source_item_id == item_id).all()


async def async_get_outbound_relationships(db: AsyncSession, item_id: int) -> list[ItemRelationship]:
    result = await db.execute(
        select(ItemRelationship).filter(ItemRelationship.source_item_id == item_id)
    )
    return list(result.scalars().all())


def filtered_update_changes(payload: CapturedItemUpdate) -> dict:
    raw_changes = payload.model_dump(mode="json", exclude_unset=True)
    return {
        key: value
        for key, value in raw_changes.items()
        if value is not None and value not in ({}, [])
    }


@router.post("/items", response_model=CapturedItemRead, status_code=201)
async def create_item(
    payload: CapturedItemCreate,
    request: Request,
    db: AsyncSession = Depends(async_db_dependency),
):
    item = CapturedItem(
        timestamp=payload.timestamp,
        source_type=payload.source_type,
        tags=payload.tags,
        inferred_project_task=payload.inferred_project_task,
        confidence=payload.confidence,
        user_edits=payload.user_edits,
        provenance=payload.provenance,
    )
    item.user_content = CapturedItemUserContent(
        raw_content=payload.raw_content,
        provenance={**payload.provenance, "origin": "user"},
    )
    if payload.enriched_content:
        item.enriched_content.append(
            CapturedItemEnrichedContent(
                enriched_content=payload.enriched_content,
                provenance={**payload.enriched_provenance, "origin": "enrichment"},
            )
        )

    db.add(item)
    await db.flush()

    for relation in payload.relationships:
        db.add(
            ItemRelationship(
                source_item_id=item.id,
                target_item_id=relation.target_item_id,
                relationship_type=relation.relationship_type,
                confidence=relation.confidence,
                provenance=relation.provenance,
            )
        )

    db.add(
        AuditLog(
            item_id=item.id,
            action="created",
            actor="api",
            changes=payload.model_dump(mode="json"),
        )
    )
    await db.commit()
    item = await async_get_item_with_content(db, item.id)

    await request.app.state.timeline.publish(
        {"event": "created", "item_id": item.id}
    )
    item_relationships = await async_get_outbound_relationships(db, item.id)
    return CapturedItemRead(
        id=item.id,
        timestamp=item.timestamp,
        source_type=item.source_type,
        raw_content=item.user_content.raw_content,
        enriched_content=(
            item.enriched_content[-1].enriched_content if item.enriched_content else None
        ),
        tags=item.tags,
        inferred_project_task=item.inferred_project_task,
        relationships=serialize_relationships(item_relationships),
        confidence=item.confidence,
        user_edits=item.user_edits,
        provenance=item.provenance,
    )


@router.put("/items/{item_id}", response_model=CapturedItemRead)
def update_item(
    item_id: int,
    payload: CapturedItemUpdate,
    request: Request,
    db: Session = Depends(db_dependency),
):
    item = get_item_with_content(db, item_id)

    if payload.raw_content is not None:
        if item.user_content is None:
            item.user_content = CapturedItemUserContent(
                raw_content=payload.raw_content,
                provenance={**(payload.provenance or {}), "origin": "user"},
            )
        else:
            item.user_content.raw_content = payload.raw_content
    if payload.tags is not None:
        item.tags = payload.tags
    if payload.confidence is not None:
        item.confidence = payload.confidence
    if payload.user_edits is not None:
        item.user_edits = payload.user_edits
    if payload.provenance is not None:
        item.provenance = payload.provenance
    if payload.enriched_content is not None:
        item.enriched_content.append(
            CapturedItemEnrichedContent(
                enriched_content=payload.enriched_content,
                provenance={**payload.enriched_provenance, "origin": "enrichment"},
            )
        )

    audit_changes = filtered_update_changes(payload)
    db.add(
        AuditLog(
            item_id=item.id,
            action="updated",
            actor="api",
            changes=audit_changes,
        )
    )
    db.commit()
    item = get_item_with_content(db, item.id)

    anyio.from_thread.run(
        request.app.state.timeline.publish,
        {"event": "updated", "item_id": item.id},
    )
    item_relationships = get_outbound_relationships(db, item.id)
    return CapturedItemRead(
        id=item.id,
        timestamp=item.timestamp,
        source_type=item.source_type,
        raw_content=item.user_content.raw_content,
        enriched_content=(
            item.enriched_content[-1].enriched_content if item.enriched_content else None
        ),
        tags=item.tags,
        inferred_project_task=item.inferred_project_task,
        relationships=serialize_relationships(item_relationships),
        confidence=item.confidence,
        user_edits=item.user_edits,
        provenance=item.provenance,
    )


@router.websocket("/ws/timeline")
async def timeline_stream(websocket: WebSocket) -> None:
    await websocket.accept()
    queue = websocket.app.state.timeline.subscribe()
    try:
        while True:
            next_event = asyncio.create_task(queue.get())
            disconnect_probe = asyncio.create_task(websocket.receive())
            done, pending = await asyncio.wait(
                {next_event, disconnect_probe},
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()
            if next_event in done:
                await websocket.send_json(next_event.result())
            elif disconnect_probe in done:
                message = disconnect_probe.result()
                if message.get("type") == "websocket.disconnect":
                    break
    except WebSocketDisconnect:
        pass
    finally:
        websocket.app.state.timeline.unsubscribe(queue)