from __future__ import annotations

import json
from collections import Counter

from sqlmodel import Session, select

from app.db.models import Entry, Insight


def generate_insights(session: Session) -> list[Insight]:
    entries = session.exec(select(Entry)).all()
    if not entries:
        return []

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
    if not meta:
        return None
    return json.dumps(meta, ensure_ascii=False)
