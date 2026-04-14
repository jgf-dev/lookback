import asyncio
from collections.abc import Sequence
from datetime import datetime, timezone

import anyio
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
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


def get_outbound_relationships(db: Session, item_id: int) -> list[ItemRelationship]:
    return db.query(ItemRelationship).filter(ItemRelationship.source_item_id == item_id).all()


def filtered_update_changes(payload: CapturedItemUpdate) -> dict:
    raw_changes = payload.model_dump(mode="json", exclude_unset=True)
    return {
        key: value
        for key, value in raw_changes.items()
        if value is not None and value not in ({}, [])
    }


@router.get("/items", response_model=list[CapturedItemRead])
def list_items(
    db: Session = Depends(db_dependency),
    source_type: str | None = None,
    tag: str | None = None,
) -> list[CapturedItemRead]:
    """Return all captured items, optionally filtered by source_type and/or tag."""
    query = (
        db.query(CapturedItem)
        .options(joinedload(CapturedItem.user_content), joinedload(CapturedItem.enriched_content))
        .order_by(CapturedItem.timestamp.desc())
    )
    if source_type:
        query = query.filter(CapturedItem.source_type == source_type)
    items = query.all()

    result = []
    for item in items:
        if item.user_content is None:
            continue
        if tag and tag not in (item.tags or []):
            continue
        rels = get_outbound_relationships(db, item.id)
        result.append(
            CapturedItemRead(
                id=item.id,
                timestamp=item.timestamp,
                source_type=item.source_type,
                raw_content=item.user_content.raw_content,
                enriched_content=(
                    item.enriched_content[-1].enriched_content if item.enriched_content else None
                ),
                tags=item.tags or [],
                inferred_project_task=item.inferred_project_task,
                relationships=serialize_relationships(rels),
                confidence=item.confidence,
                user_edits=item.user_edits,
                provenance=item.provenance or {},
            )
        )
    return result


@router.get("/review/today")
def get_today_review(db: Session = Depends(db_dependency)) -> dict:
    """Return the end-of-day review script for today's captured items."""
    from datetime import date  # noqa: PLC0415
    from app.services.review.pipeline import orchestrate_end_of_day_review  # noqa: PLC0415

    today = date.today()
    items = (
        db.query(CapturedItem)
        .options(joinedload(CapturedItem.user_content))
        .all()
    )
    today_items = [
        {
            "id": item.id,
            "source_type": item.source_type,
            "raw_content": item.user_content.raw_content if item.user_content else "",
            "tags": item.tags or [],
        }
        for item in items
        if item.timestamp.date() == today
    ]
    return orchestrate_end_of_day_review(today_items)


@router.post("/items", response_model=CapturedItemRead, status_code=201)
def create_item(
    payload: CapturedItemCreate,
    request: Request,
    db: Session = Depends(db_dependency),
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
    db.flush()

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
    db.commit()
    item = get_item_with_content(db, item.id)

    anyio.from_thread.run(
        request.app.state.timeline.publish,
        {"event": "created", "item_id": item.id},
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


def _build_and_persist_item(
    db: Session,
    request: Request,
    *,
    source_type: str,
    raw_content: str,
    enriched_content: str | None,
    tags: list[str],
    inferred_project_task: str | None,
    enriched_provenance: dict,
    provenance: dict,
) -> CapturedItemRead:
    """Shared helper: persist a new CapturedItem and publish a timeline event."""
    item = CapturedItem(
        timestamp=datetime.now(timezone.utc),
        source_type=source_type,
        tags=tags,
        inferred_project_task=inferred_project_task,
        provenance=provenance,
    )
    item.user_content = CapturedItemUserContent(
        raw_content=raw_content,
        provenance={**provenance, "origin": "user"},
    )
    if enriched_content:
        item.enriched_content.append(
            CapturedItemEnrichedContent(
                enriched_content=enriched_content,
                provenance={**enriched_provenance, "origin": "enrichment"},
            )
        )
    db.add(item)
    db.flush()
    db.add(
        AuditLog(
            item_id=item.id,
            action="created",
            actor="api",
            changes={
                "source_type": source_type,
                "raw_content": raw_content,
                "provenance": provenance,
            },
        )
    )
    db.commit()
    item = get_item_with_content(db, item.id)
    anyio.from_thread.run(
        request.app.state.timeline.publish,
        {"event": "created", "item_id": item.id},
    )
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
        relationships=[],
        confidence=item.confidence,
        user_edits=item.user_edits,
        provenance=item.provenance,
    )


@router.post("/items/transcribe", response_model=CapturedItemRead, status_code=201)
async def transcribe_audio_item(
    request: Request,
    audio: UploadFile,
    db: Session = Depends(db_dependency),
) -> CapturedItemRead:
    """Accept an audio file, transcribe it via OpenAI Whisper, and store as a CapturedItem.

    - Uses ``multipart/form-data`` with a single ``audio`` file field.
    - Falls back to a placeholder transcript when OPENAI_API_KEY is not set.
    """
    from app.services.ingestion.pipeline import ingest_audio  # noqa: PLC0415
    from app.services.enrichment.pipeline import enrich_with_context  # noqa: PLC0415

    audio_bytes = await audio.read()
    ingest_payload = ingest_audio(audio_bytes, filename=audio.filename or "audio.webm")

    enrich_payload = enrich_with_context(ingest_payload["raw_content"])

    return _build_and_persist_item(
        db,
        request,
        source_type="audio",
        raw_content=ingest_payload["raw_content"],
        enriched_content=enrich_payload["enriched_content"],
        tags=enrich_payload.get("tags", []),
        inferred_project_task=enrich_payload.get("inferred_project_task"),
        enriched_provenance=enrich_payload["enriched_provenance"],
        provenance=ingest_payload.get("provenance", {}),
    )


@router.post("/items/screenshot", response_model=CapturedItemRead, status_code=201)
async def analyse_screenshot_item(
    request: Request,
    image: UploadFile,
    db: Session = Depends(db_dependency),
) -> CapturedItemRead:
    """Accept a screenshot image, analyse it via Gemini vision, and store as a CapturedItem.

    - Uses ``multipart/form-data`` with a single ``image`` file field.
    - Falls back to a stub description when GEMINI_API_KEY is not set.
    """
    from app.services.enrichment.pipeline import enrich_with_screenshot  # noqa: PLC0415

    image_bytes = await image.read()
    mime_type = image.content_type or "image/png"
    enrich_payload = enrich_with_screenshot(image_bytes, mime_type=mime_type)

    raw = enrich_payload.get("ocr_text") or enrich_payload["enriched_content"]

    return _build_and_persist_item(
        db,
        request,
        source_type="screenshot",
        raw_content=raw,
        enriched_content=enrich_payload["enriched_content"],
        tags=enrich_payload.get("tags", []),
        inferred_project_task=enrich_payload.get("inferred_project_task"),
        enriched_provenance=enrich_payload["enriched_provenance"],
        provenance=enrich_payload["enriched_provenance"],
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
