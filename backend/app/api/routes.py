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
    """
    Provide a database session from the application's session factory for use as a FastAPI dependency.
    
    Returns:
        Session: A SQLAlchemy `Session` instance yielded from `request.app.state.session_factory`.
    """
    yield from get_db(request.app.state.session_factory)


@router.post("/items", response_model=CapturedItemRead, status_code=201)
async def create_item(
    payload: CapturedItemCreate,
    request: Request,
    db: Session = Depends(db_dependency),
):
    """
    Create a new CapturedItem with its user content, optional enriched content, relationships, and an audit log entry, then publish a "created" timeline event.
    
    The function persists a CapturedItem, its CapturedItemUserContent, any CapturedItemEnrichedContent provided, one ItemRelationship per entry in `payload.relationships`, and an AuditLog; it commits the transaction and publishes a timeline event via `request.app.state.timeline`.
    
    Parameters:
        payload (CapturedItemCreate): Data used to populate the created item, its content, and relationships.
        request (Request): FastAPI request object; used to access application state for publishing the timeline event.
    
    Returns:
        CapturedItemRead: Representation of the newly created item. `enriched_content` is the most recent enriched entry if present, otherwise `None`. Relationships mirror `payload.relationships`.
    """
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
    """
    Update fields of an existing captured item, record the change in the audit log, publish an "updated" timeline event, and return the item's current representation.
    
    Parameters:
        item_id (int): ID of the item to update.
        payload (CapturedItemUpdate): Fields to apply; only non-None fields are applied. If `enriched_content` is provided, a new enriched content entry is appended.
        request (Request): FastAPI request (used to access application state for timeline publishing).
    
    Returns:
        CapturedItemRead: The updated item representation. `enriched_content` will be the most recent enriched entry if any, otherwise `None`.
    
    Raises:
        HTTPException: 404 if the item with `item_id` does not exist.
    """
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
    """
    Stream timeline events to the connected WebSocket client until the client disconnects.
    
    Subscribes to the application's timeline, reads events from the subscription queue, and sends each event to the client as JSON. Unsubscribes from the timeline when the WebSocket disconnects.
    
    Parameters:
        websocket (WebSocket): The active client WebSocket connection.
    """
    await websocket.accept()
    queue = websocket.app.state.timeline.subscribe()
    try:
        while True:
            event = await queue.get()
            await websocket.send_json(event)
    except WebSocketDisconnect:
        websocket.app.state.timeline.unsubscribe(queue)
