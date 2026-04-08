"""Tests for the AGENTS.md implementation spec document.

Validates that the spec is complete, well-formed, and contains all required
sections, contracts, endpoints, and acceptance criteria described in the PR.
"""

import json
import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AGENTS_MD = PROJECT_ROOT / "AGENTS.md"


@pytest.fixture(scope="module")
def spec_text() -> str:
    try:
        return AGENTS_MD.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError) as e:
        message = f"AGENTS.md not available: {e}"
        pytest.skip(message)
        raise pytest.skip.Exception(message)


# ---------------------------------------------------------------------------
# File existence and basic sanity
# ---------------------------------------------------------------------------


def test_agents_md_exists() -> None:
    assert AGENTS_MD.exists(), "AGENTS.md must exist at the project root"


def test_agents_md_is_non_empty(spec_text: str) -> None:
    assert len(spec_text.strip()) > 0, "AGENTS.md must not be empty"


def test_agents_md_minimum_length(spec_text: str) -> None:
    lines = spec_text.splitlines()
    assert len(lines) >= 400, f"Expected at least 400 lines, got {len(lines)}"


# ---------------------------------------------------------------------------
# Required top-level sections (## 1. … ## 12.)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "section_heading",
    [
        "## 1. System Overview",
        "## 2. Tech Stack",
        "## 3. High-Level Architecture",
        "## 4. Core Services",
        "## 5. Data Model",
        "## 6. Realtime Layer",
        "## 7. Frontend (Next.js)",
        "## 8. Pipelines",
        "## 9. Security & Privacy",
        "## 10. Folder Structure",
        "## 11. Acceptance Criteria",
        "## 12. Stretch Goals",
    ],
)
def test_required_section_present(spec_text: str, section_heading: str) -> None:
    assert section_heading in spec_text, f"Missing section: {section_heading!r}"


# ---------------------------------------------------------------------------
# Tech stack
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "technology",
    ["FastAPI", "PostgreSQL", "Redis", "Next.js", "TypeScript", "OpenAI", "Gemini"],
)
def test_tech_stack_mentions(spec_text: str, technology: str) -> None:
    assert technology in spec_text, f"Tech stack missing: {technology!r}"


# ---------------------------------------------------------------------------
# HTTP endpoints
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "endpoint",
    [
        "POST /ingest/audio",
        "POST /ingest/screenshot",
        "POST /ingest/text",
        "POST /review/start",
    ],
)
def test_http_endpoint_defined(spec_text: str, endpoint: str) -> None:
    assert endpoint in spec_text, f"HTTP endpoint not specified: {endpoint!r}"


def test_websocket_endpoint_defined(spec_text: str) -> None:
    assert "/ws/timeline" in spec_text, "WebSocket endpoint /ws/timeline not specified"


# ---------------------------------------------------------------------------
# WebSocket event names
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "event",
    ["entry_created", "entry_updated", "insight_created"],
)
def test_websocket_event_defined(spec_text: str, event: str) -> None:
    assert event in spec_text, f"WebSocket event not mentioned: {event!r}"


# ---------------------------------------------------------------------------
# JSON contract examples
# ---------------------------------------------------------------------------


def _extract_json_blocks(text: str) -> list[str]:
    """Return all fenced ```json … ``` blocks from *text*."""
    return re.findall(r"```json\s*([\s\S]*?)```", text)


def test_json_blocks_present(spec_text: str) -> None:
    blocks = _extract_json_blocks(spec_text)
    assert len(blocks) >= 2, "Expected at least 2 JSON code blocks in the spec"


def test_enrichment_output_is_valid_json(spec_text: str) -> None:
    blocks = _extract_json_blocks(spec_text)
    enrichment_block = next(
        (b for b in blocks if '"summary"' in b and '"tags"' in b), None
    )
    assert enrichment_block is not None, "Enrichment output JSON block not found"
    parsed = json.loads(enrichment_block)
    assert isinstance(parsed, dict)


def test_enrichment_output_has_required_fields(spec_text: str) -> None:
    blocks = _extract_json_blocks(spec_text)
    enrichment_block = next(
        (b for b in blocks if '"summary"' in b and '"tags"' in b), None
    )
    assert enrichment_block is not None
    parsed = json.loads(enrichment_block)
    for field in ("summary", "tags", "related_entries", "external_context", "confidence"):
        assert field in parsed, f"Enrichment output missing field: {field!r}"


def test_enrichment_confidence_is_numeric(spec_text: str) -> None:
    blocks = _extract_json_blocks(spec_text)
    enrichment_block = next(
        (b for b in blocks if '"summary"' in b and '"tags"' in b), None
    )
    assert enrichment_block is not None
    parsed = json.loads(enrichment_block)
    assert isinstance(parsed["confidence"], float), "confidence must be a float"
    assert 0.0 <= parsed["confidence"] <= 1.0, "confidence must be in [0, 1]"


def test_enrichment_tags_is_list(spec_text: str) -> None:
    blocks = _extract_json_blocks(spec_text)
    enrichment_block = next(
        (b for b in blocks if '"summary"' in b and '"tags"' in b), None
    )
    assert enrichment_block is not None
    parsed = json.loads(enrichment_block)
    assert isinstance(parsed["tags"], list), "tags must be a list"


def test_visualization_output_is_valid_json(spec_text: str) -> None:
    blocks = _extract_json_blocks(spec_text)
    viz_block = next(
        (b for b in blocks if '"nodes"' in b and '"edges"' in b), None
    )
    assert viz_block is not None, "Visualization output JSON block not found"
    parsed = json.loads(viz_block)
    assert isinstance(parsed, dict)


def test_visualization_output_has_nodes_and_edges(spec_text: str) -> None:
    blocks = _extract_json_blocks(spec_text)
    viz_block = next(
        (b for b in blocks if '"nodes"' in b and '"edges"' in b), None
    )
    assert viz_block is not None
    parsed = json.loads(viz_block)
    assert "nodes" in parsed, "Visualization output must have 'nodes'"
    assert "edges" in parsed, "Visualization output must have 'edges'"


# ---------------------------------------------------------------------------
# Insight object contract (uses range notation — not strict JSON, tested textually)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field",
    ["type", "title", "description", "related_entries", "priority", "confidence"],
)
def test_insight_object_field_mentioned(spec_text: str, field: str) -> None:
    insight_section_match = re.search(
        r"#### Insight Object([\s\S]*?)(?=\n---|\Z)", spec_text
    )
    assert insight_section_match is not None, "Insight Object section not found"
    insight_section = insight_section_match.group(1)
    assert f'"{field}"' in insight_section, f"Insight object missing field: {field!r}"


def test_insight_type_values_defined(spec_text: str) -> None:
    """The insight type field should enumerate its allowed values."""
    assert "trend" in spec_text
    assert "reminder" in spec_text
    assert "contradiction" in spec_text
    assert "opportunity" in spec_text


# ---------------------------------------------------------------------------
# Data model tables
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("table", ["entries", "insights", "screenshots"])
def test_data_model_table_defined(spec_text: str, table: str) -> None:
    assert table in spec_text, f"Data model table not defined: {table!r}"


@pytest.mark.parametrize(
    "column",
    ["UUID PRIMARY KEY", "TIMESTAMP", "JSONB", "TEXT[]"],
)
def test_entries_table_sql_types_present(spec_text: str, column: str) -> None:
    assert column in spec_text, f"Expected SQL type/keyword missing: {column!r}"


# ---------------------------------------------------------------------------
# Security & Privacy
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "security_term",
    ["JWT", "consent", "encryption", "Audit log"],
)
def test_security_requirement_present(spec_text: str, security_term: str) -> None:
    assert security_term in spec_text, f"Security requirement missing: {security_term!r}"


# ---------------------------------------------------------------------------
# Acceptance criteria
# ---------------------------------------------------------------------------


def test_acceptance_criteria_has_unchecked_items(spec_text: str) -> None:
    """All acceptance criteria items should be unchecked (awaiting implementation)."""
    checked_count = (
        spec_text.count("- [x]") + spec_text.count("- [X]")
        + spec_text.count("* [x]") + spec_text.count("* [X]")
    )
    unchecked_count = spec_text.count("- [ ]") + spec_text.count("* [ ]")
    assert unchecked_count >= 10, (
        f"Expected at least 10 unchecked acceptance criteria, found {unchecked_count}"
    )
    assert checked_count == 0, (
        f"Expected no pre-checked criteria (spec is a forward-looking plan), "
        f"but found {checked_count}"
    )


@pytest.mark.parametrize(
    "category",
    ["Core Functionality", "UX", "Intelligence", "Reliability"],
)
def test_acceptance_criteria_category_present(spec_text: str, category: str) -> None:
    assert category in spec_text, f"Acceptance criteria category missing: {category!r}"


def test_acceptance_criteria_audio_latency(spec_text: str) -> None:
    """Audio transcription latency target must be stated."""
    assert "<2s" in spec_text or "2s delay" in spec_text, (
        "Audio latency requirement (<2s) not found in spec"
    )


def test_acceptance_criteria_has_intelligence_subsection() -> None:
    content = read_agents_md()
    assert "### Intelligence" in content


# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("page", ["/timeline", "/review", "/insights", "/settings"])
def test_frontend_page_defined(spec_text: str, page: str) -> None:
    assert page in spec_text, f"Frontend page not defined: {page!r}"


@pytest.mark.parametrize(
    "component",
    ["TimelineCanvas", "EntryCard", "InsightPanel", "VoiceReviewPanel", "ScreenshotViewer"],
)
def test_frontend_component_defined(spec_text: str, component: str) -> None:
    assert component in spec_text, f"Frontend component not defined: {component!r}"


# ---------------------------------------------------------------------------
# Pipelines
# ---------------------------------------------------------------------------


def test_audio_pipeline_defined(spec_text: str) -> None:
    assert "Audio Pipeline" in spec_text or "8.1 Audio Pipeline" in spec_text


def test_screenshot_pipeline_defined(spec_text: str) -> None:
    assert "Screenshot Pipeline" in spec_text or "8.2 Screenshot Pipeline" in spec_text


# ---------------------------------------------------------------------------
# Negative / boundary checks
# ---------------------------------------------------------------------------


def test_no_hardcoded_api_keys(spec_text: str) -> None:
    """Spec must not contain inline API keys or secrets."""
    suspicious_patterns = [
        r"sk-[A-Za-z0-9]{20,}",   # OpenAI key pattern
        r"AIza[A-Za-z0-9_\-]{35}",  # Google API key pattern
        r"password\s*=\s*['\"][^'\"]{4,}",
    ]
    for pattern in suspicious_patterns:
        match = re.search(pattern, spec_text)
        assert match is None, f"Possible hardcoded credential found matching {pattern!r}"


def test_spec_does_not_mark_todo_as_done(spec_text: str) -> None:
    """AGENTS.md is a forward-looking spec; no items should be marked done."""
    checked = (
        spec_text.count("- [x]") + spec_text.count("- [X]")
        + spec_text.count("* [x]") + spec_text.count("* [X]")
    )
    assert checked == 0, "No acceptance criteria should be marked complete in the spec"


def test_stretch_goals_section_non_empty(spec_text: str) -> None:
    """Stretch goals section must contain at least one goal."""
    match = re.search(r"## 12\. Stretch Goals([\s\S]*?)(?=\n---|\Z)", spec_text)
    assert match is not None, "Stretch Goals section not found"
    content = match.group(1).strip()
    assert len(content) > 0, "Stretch Goals section is empty"
    bullet_count = sum(1 for line in content.splitlines() if re.match(r'^\s*[-*]\s+', line))
    assert bullet_count >= 3, f"Expected at least 3 stretch goals, found section: {content!r}"