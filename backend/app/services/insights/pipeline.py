from typing import TypedDict


class InsightItem(TypedDict, total=False):
    id: int
    source_type: str
    raw_content: str
    tags: list[str]


class InsightsResponse(TypedDict):
    patterns: list[str]
    open_loops: list[dict]
    deadlines: list[dict]
    contradictions: list[dict]


def discover_patterns(items: list[InsightItem]) -> InsightsResponse:
    return {
        "patterns": [f"Total items analyzed: {len(items)}"],
        "open_loops": [],
        "deadlines": [],
        "contradictions": [],
    }
