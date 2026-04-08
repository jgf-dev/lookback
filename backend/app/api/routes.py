from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect
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


@router.post("/items", response_model=CapturedItemRead, status_code=201)
async def create_item(
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
        provenance={"origin": "user", **payload.provenance},
    )
    if payload.enriched_content:
        item.enriched_content.append(
            CapturedItemEnrichedContent(
                enriched_content=payload.enriched_content,
                provenance={"origin": "automated", **payload.enriched_provenance},
            )
        )

    db.add(item)
    db.flush()

    for relation in payload.relationships:
        db.add(
            ItemRelationship(
                source_item_id=item.id,
                target_item_id=relation["target_item_id"],
                relationship_type=relation["relationship_type"],
                confidence=relation.get("confidence"),
                provenance=relation.get("provenance", {}),
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
    db.refresh(item)

    await request.app.state.timeline.publish({"event": "created", "item_id": item.id})
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
        relationships=payload.relationships,
        confidence=item.confidence,
        user_edits=item.user_edits,
        provenance=item.provenance,
    )


@router.put("/items/{item_id}", response_model=CapturedItemRead)
async def update_item(
    item_id: int,
    payload: CapturedItemUpdate,
    request: Request,
    db: Session = Depends(db_dependency),
):
    item = (
        db.query(CapturedItem)
        .options(joinedload(CapturedItem.user_content), joinedload(CapturedItem.enriched_content))
        .filter(CapturedItem.id == item_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if payload.raw_content is not None:
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
                provenance={"origin": "automated", **(payload.provenance or {})},
            )
        )

    db.add(
        AuditLog(
            item_id=item.id,
            action="updated",
            actor="api",
            changes=payload.model_dump(mode="json"),
        )
    )
    db.commit()
    db.refresh(item)

    await request.app.state.timeline.publish({"event": "updated", "item_id": item.id})
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


@router.websocket("/ws/timeline")
async def timeline_stream(websocket: WebSocket) -> None:
    await websocket.accept()
    queue = websocket.app.state.timeline.subscribe()
    try:
        while True:
            event = await queue.get()
            await websocket.send_json(event)
    except WebSocketDisconnect:
        websocket.app.state.timeline.unsubscribe(queue)
