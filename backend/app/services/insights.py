from __future__ import annotations

import json
from collections import Counter
from datetime import datetime

from sqlmodel import Session, select

from app.db.models import Entry, Insight


def generate_insights(session: Session) -> list[Insight]:
    """
    Create and persist Insight records summarizing the top project and top capture source derived from Entry rows.

    Parameters:
        session (Session): Active database session used to query Entry rows and persist created Insight instances.

    Returns:
        list[Insight]: Created Insight objects persisted to the database; returns an empty list if no Entry rows exist.
    """
    now = datetime.utcnow()
    today = now.date()
    today_start = datetime(today.year, today.month, today.day, 0, 0, 0)
    today_end = datetime(today.year, today.month, today.day, 23, 59, 59, 999999)

    entries = session.exec(
        select(Entry)
        .where(Entry.created_at >= today_start, Entry.created_at <= today_end)
    ).all()
    if not entries:
        return []

    # Delete existing insights for today to make this operation idempotent
    existing_insights = session.exec(
        select(Insight)
        .where(Insight.created_at >= today_start, Insight.created_at <= today_end)
    ).all()
    for existing in existing_insights:
        session.delete(existing)
    session.commit()

    project_counter = Counter((e.project or 'General') for e in entries)
    source_counter = Counter(e.source for e in entries)

    insights: list[Insight] = []
    top_project, project_count = project_counter.most_common(1)[0]
    insights.append(
        Insight(
            title='Primary focus area',
            description=f'Most of your notes today are in project "{top_project}" ({project_count} entries).',
            action='Consider blocking dedicated deep-work time around this project.',
            confidence=0.8,
        )
    )

    top_source, source_count = source_counter.most_common(1)[0]
    insights.append(
        Insight(
            title='Capture channel trend',
            description=f'Highest capture volume came from {top_source} ({source_count} events).',
            action='Improve capture quality by adding richer context fields on this channel.',
            confidence=0.72,
        )
    )

    for insight in insights:
        session.add(insight)
    session.commit()
    for insight in insights:
        session.refresh(insight)
    return insights


def safe_metadata(meta: dict | None) -> str | None:
    """
    Serialize a metadata dictionary to a JSON string when metadata is provided.
    
    Parameters:
    	meta (dict | None): Metadata to serialize; if `None` or empty, no serialization is performed.
    
    Returns:
    	A JSON-formatted string of `meta`, or `None` if `meta` is `None` or empty.
    """
    if not meta:
        return None
    return json.dumps(meta, ensure_ascii=False)