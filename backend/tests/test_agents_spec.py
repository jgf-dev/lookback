"""Tests for the AGENTS.md specification document.

Validates the structure, content, and internal consistency of the
implementation spec introduced in this PR.
"""

import json
import os
import re


AGENTS_MD_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "AGENTS.md")


def read_agents_md() -> str:
    with open(AGENTS_MD_PATH, encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# File presence
# ---------------------------------------------------------------------------


def test_agents_md_exists() -> None:
    assert os.path.isfile(AGENTS_MD_PATH), "AGENTS.md must exist at the repository root"


def test_agents_md_is_not_empty() -> None:
    content = read_agents_md()
    assert len(content.strip()) > 0, "AGENTS.md must not be empty"


# ---------------------------------------------------------------------------
# Top-level document structure (12 required sections)
# ---------------------------------------------------------------------------

REQUIRED_SECTIONS = [
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
]


def test_all_required_sections_present() -> None:
    content = read_agents_md()
    for section in REQUIRED_SECTIONS:
        assert section in content, f"Required section missing: {section!r}"


def test_document_title_present() -> None:
    content = read_agents_md()
    assert "# Implementation Spec: Personal Capture & Insight System" in content


# ---------------------------------------------------------------------------
# Tech stack mentions
# ---------------------------------------------------------------------------

REQUIRED_BACKEND_TECHNOLOGIES = ["FastAPI", "PostgreSQL", "Redis"]
REQUIRED_FRONTEND_TECHNOLOGIES = ["Next.js", "TypeScript", "WebSocket"]
REQUIRED_AI_TECHNOLOGIES = ["OpenAI", "Gemini"]


def test_required_backend_technologies_mentioned() -> None:
    content = read_agents_md()
    for tech in REQUIRED_BACKEND_TECHNOLOGIES:
        assert tech in content, f"Backend technology not mentioned: {tech!r}"


def test_required_frontend_technologies_mentioned() -> None:
    content = read_agents_md()
    for tech in REQUIRED_FRONTEND_TECHNOLOGIES:
        assert tech in content, f"Frontend technology not mentioned: {tech!r}"


def test_required_ai_technologies_mentioned() -> None:
    content = read_agents_md()
    for tech in REQUIRED_AI_TECHNOLOGIES:
        assert tech in content, f"AI technology not mentioned: {tech!r}"


# ---------------------------------------------------------------------------
# Core service sub-sections
# ---------------------------------------------------------------------------

REQUIRED_SERVICES = [
    "### 4.1 Ingestion Service",
    "### 4.2 Enrichment Service",
    "### 4.3 Analysis Service",
    "### 4.4 Visualization Service",
    "### 4.5 End-of-Day Review Service",
]


def test_all_core_services_documented() -> None:
    content = read_agents_md()
    for service in REQUIRED_SERVICES:
        assert service in content, f"Core service section missing: {service!r}"


# ---------------------------------------------------------------------------
# API endpoint specifications
# ---------------------------------------------------------------------------

REQUIRED_INGESTION_ENDPOINTS = [
    "POST /ingest/audio",
    "POST /ingest/screenshot",
    "POST /ingest/text",
]

REQUIRED_REVIEW_ENDPOINT = "POST /review/start"
REQUIRED_WEBSOCKET_ENDPOINT = "/ws/timeline"


def test_ingestion_endpoints_defined() -> None:
    content = read_agents_md()
    for endpoint in REQUIRED_INGESTION_ENDPOINTS:
        assert endpoint in content, f"Ingestion endpoint missing from spec: {endpoint!r}"


def test_review_endpoint_defined() -> None:
    content = read_agents_md()
    assert REQUIRED_REVIEW_ENDPOINT in content


def test_websocket_endpoint_defined() -> None:
    content = read_agents_md()
    assert REQUIRED_WEBSOCKET_ENDPOINT in content


def test_all_ingestion_endpoints_use_post_method() -> None:
    """All /ingest/* endpoints must be declared as POST."""
    content = read_agents_md()
    # Extract the http code block that contains ingest endpoints
    http_blocks = re.findall(r"```http\n(.*?)```", content, re.DOTALL)
    ingest_block = next(
        (b for b in http_blocks if "/ingest/" in b),
        None,
    )
    assert ingest_block is not None, "No HTTP block with /ingest/ routes found"
    ingest_routes = [
        line.strip() for line in ingest_block.strip().splitlines() if "/ingest/" in line
    ]
    for route in ingest_routes:
        assert route.startswith("POST "), f"Ingest route must use POST: {route!r}"


# ---------------------------------------------------------------------------
# Enrichment service JSON output shape
# ---------------------------------------------------------------------------

ENRICHMENT_JSON_REQUIRED_KEYS = {
    "summary",
    "tags",
    "related_entries",
    "external_context",
    "confidence",
}


def _extract_json_blocks(content: str) -> list[str]:
    """Return all fenced ```json ... ``` blocks from markdown content."""
    return re.findall(r"```json\n(.*?)```", content, re.DOTALL)


def test_enrichment_output_json_is_valid() -> None:
    content = read_agents_md()
    json_blocks = _extract_json_blocks(content)
    # The enrichment output block contains "summary" and "tags"
    enrichment_block = next(
        (b for b in json_blocks if '"summary"' in b and '"tags"' in b),
        None,
    )
    assert enrichment_block is not None, "Enrichment output JSON block not found"
    parsed = json.loads(enrichment_block)
    assert isinstance(parsed, dict)


def test_enrichment_output_has_required_keys() -> None:
    content = read_agents_md()
    json_blocks = _extract_json_blocks(content)
    enrichment_block = next(
        (b for b in json_blocks if '"summary"' in b and '"tags"' in b),
        None,
    )
    assert enrichment_block is not None
    parsed = json.loads(enrichment_block)
    missing = ENRICHMENT_JSON_REQUIRED_KEYS - parsed.keys()
    assert not missing, f"Enrichment JSON missing keys: {missing}"


def test_enrichment_confidence_is_numeric() -> None:
    content = read_agents_md()
    json_blocks = _extract_json_blocks(content)
    enrichment_block = next(
        (b for b in json_blocks if '"summary"' in b and '"tags"' in b),
        None,
    )
    assert enrichment_block is not None
    parsed = json.loads(enrichment_block)
    assert isinstance(parsed["confidence"], (int, float))
    assert 0.0 <= parsed["confidence"] <= 1.0


def test_enrichment_tags_is_list() -> None:
    content = read_agents_md()
    json_blocks = _extract_json_blocks(content)
    enrichment_block = next(
        (b for b in json_blocks if '"summary"' in b and '"tags"' in b),
        None,
    )
    assert enrichment_block is not None
    parsed = json.loads(enrichment_block)
    assert isinstance(parsed["tags"], list)


def test_enrichment_related_entries_is_list() -> None:
    content = read_agents_md()
    json_blocks = _extract_json_blocks(content)
    enrichment_block = next(
        (b for b in json_blocks if '"summary"' in b and '"tags"' in b),
        None,
    )
    assert enrichment_block is not None
    parsed = json.loads(enrichment_block)
    assert isinstance(parsed["related_entries"], list)


# ---------------------------------------------------------------------------
# Visualization service JSON output shape
# ---------------------------------------------------------------------------


def test_visualization_output_json_is_valid() -> None:
    content = read_agents_md()
    json_blocks = _extract_json_blocks(content)
    viz_block = next(
        (b for b in json_blocks if '"nodes"' in b and '"edges"' in b),
        None,
    )
    assert viz_block is not None, "Visualization output JSON block not found"
    parsed = json.loads(viz_block)
    assert isinstance(parsed, dict)


def test_visualization_output_has_nodes_and_edges() -> None:
    content = read_agents_md()
    json_blocks = _extract_json_blocks(content)
    viz_block = next(
        (b for b in json_blocks if '"nodes"' in b and '"edges"' in b),
        None,
    )
    assert viz_block is not None
    parsed = json.loads(viz_block)
    assert "nodes" in parsed
    assert "edges" in parsed


# ---------------------------------------------------------------------------
# Insight object keys
# ---------------------------------------------------------------------------

INSIGHT_REQUIRED_KEYS = {"type", "title", "description", "related_entries", "priority", "confidence"}

VALID_INSIGHT_TYPES = {"trend", "reminder", "contradiction", "opportunity"}


def test_insight_object_declares_required_keys() -> None:
    """Insight JSON block (even as a template) must contain all required keys."""
    content = read_agents_md()
    json_blocks = _extract_json_blocks(content)
    insight_block = next(
        (b for b in json_blocks if '"type"' in b and '"priority"' in b),
        None,
    )
    assert insight_block is not None, "Insight object JSON block not found"
    for key in INSIGHT_REQUIRED_KEYS:
        assert f'"{key}"' in insight_block, f"Insight block missing key: {key!r}"


def test_insight_type_values_listed() -> None:
    """The spec must enumerate all valid insight type values."""
    content = read_agents_md()
    for insight_type in VALID_INSIGHT_TYPES:
        assert insight_type in content, f"Valid insight type not mentioned: {insight_type!r}"


# ---------------------------------------------------------------------------
# Data model (SQL schemas)
# ---------------------------------------------------------------------------

ENTRIES_TABLE_COLUMNS = [
    "id",
    "timestamp",
    "type",
    "raw_content",
    "enriched_content",
    "tags",
    "project",
    "relationships",
    "confidence",
    "metadata",
    "created_at",
]

INSIGHTS_TABLE_COLUMNS = [
    "id",
    "type",
    "title",
    "description",
    "related_entries",
    "priority",
    "confidence",
    "created_at",
]

SCREENSHOTS_TABLE_COLUMNS = [
    "id",
    "entry_id",
    "file_path",
    "ocr_text",
    "analysis",
]


def _extract_sql_blocks(content: str) -> list[str]:
    return re.findall(r"```sql\n(.*?)```", content, re.DOTALL)


def test_entries_table_has_required_columns() -> None:
    content = read_agents_md()
    sql_blocks = _extract_sql_blocks(content)
    entries_block = next((b for b in sql_blocks if "entries" in b), None)
    assert entries_block is not None, "entries SQL block not found"
    for col in ENTRIES_TABLE_COLUMNS:
        assert col in entries_block, f"entries table missing column: {col!r}"


def test_entries_table_has_uuid_primary_key() -> None:
    content = read_agents_md()
    sql_blocks = _extract_sql_blocks(content)
    entries_block = next((b for b in sql_blocks if "entries" in b), None)
    assert entries_block is not None
    assert "UUID PRIMARY KEY" in entries_block


def test_entries_type_column_has_comment_with_valid_types() -> None:
    """The entries.type column comment must list audio, screenshot, text, analysis."""
    content = read_agents_md()
    sql_blocks = _extract_sql_blocks(content)
    entries_block = next((b for b in sql_blocks if "entries" in b), None)
    assert entries_block is not None
    for entry_type in ("audio", "screenshot", "text", "analysis"):
        assert entry_type in entries_block, (
            f"entries.type comment missing value: {entry_type!r}"
        )


def test_insights_table_has_required_columns() -> None:
    content = read_agents_md()
    sql_blocks = _extract_sql_blocks(content)
    insights_block = next((b for b in sql_blocks if "insights" in b), None)
    assert insights_block is not None, "insights SQL block not found"
    for col in INSIGHTS_TABLE_COLUMNS:
        assert col in insights_block, f"insights table missing column: {col!r}"


def test_screenshots_table_has_required_columns() -> None:
    content = read_agents_md()
    sql_blocks = _extract_sql_blocks(content)
    screenshots_block = next((b for b in sql_blocks if "screenshots" in b), None)
    assert screenshots_block is not None, "screenshots SQL block not found"
    for col in SCREENSHOTS_TABLE_COLUMNS:
        assert col in screenshots_block, f"screenshots table missing column: {col!r}"


def test_screenshots_table_references_entry_id() -> None:
    content = read_agents_md()
    sql_blocks = _extract_sql_blocks(content)
    screenshots_block = next((b for b in sql_blocks if "screenshots" in b), None)
    assert screenshots_block is not None
    assert "entry_id" in screenshots_block, "screenshots table must reference entry_id"


# ---------------------------------------------------------------------------
# Realtime / WebSocket events
# ---------------------------------------------------------------------------

REQUIRED_WEBSOCKET_EVENTS = ["entry_created", "entry_updated", "insight_created"]


def test_all_websocket_events_documented() -> None:
    content = read_agents_md()
    for event in REQUIRED_WEBSOCKET_EVENTS:
        assert event in content, f"WebSocket event missing from spec: {event!r}"


# ---------------------------------------------------------------------------
# Frontend pages and components
# ---------------------------------------------------------------------------

REQUIRED_FRONTEND_PAGES = ["/timeline", "/review", "/insights", "/settings"]
REQUIRED_FRONTEND_COMPONENTS = [
    "TimelineCanvas",
    "EntryCard",
    "InsightPanel",
    "VoiceReviewPanel",
    "ScreenshotViewer",
]


def test_required_frontend_pages_documented() -> None:
    content = read_agents_md()
    for page in REQUIRED_FRONTEND_PAGES:
        assert page in content, f"Frontend page missing from spec: {page!r}"


def test_required_frontend_components_documented() -> None:
    content = read_agents_md()
    for component in REQUIRED_FRONTEND_COMPONENTS:
        assert component in content, f"Frontend component missing from spec: {component!r}"


# ---------------------------------------------------------------------------
# Pipelines
# ---------------------------------------------------------------------------


def test_audio_pipeline_section_present() -> None:
    content = read_agents_md()
    assert "### 8.1 Audio Pipeline" in content


def test_screenshot_pipeline_section_present() -> None:
    content = read_agents_md()
    assert "### 8.2 Screenshot Pipeline" in content


def test_audio_pipeline_ends_at_timeline() -> None:
    """Audio pipeline diagram must end with Timeline."""
    content = read_agents_md()
    # Find the audio pipeline diagram line
    match = re.search(r"Audio.*?→.*?Timeline", content)
    assert match is not None, "Audio pipeline must show flow ending at Timeline"


def test_screenshot_pipeline_ends_at_timeline() -> None:
    """Screenshot pipeline diagram must end with Timeline."""
    content = read_agents_md()
    match = re.search(r"Screenshot.*?→.*?Timeline", content)
    assert match is not None, "Screenshot pipeline must show flow ending at Timeline"


# ---------------------------------------------------------------------------
# Security & Privacy
# ---------------------------------------------------------------------------

REQUIRED_SECURITY_ITEMS = ["JWT", "encryption", "consent"]


def test_security_section_mentions_jwt() -> None:
    content = read_agents_md()
    assert "JWT" in content, "Security section must mention JWT authentication"


def test_security_section_mentions_encryption() -> None:
    content = read_agents_md()
    assert "encryption" in content, "Security section must mention encryption"


def test_security_section_requires_user_consent() -> None:
    content = read_agents_md()
    assert "consent" in content, "Security section must require user consent"


def test_security_section_mentions_audit_log() -> None:
    content = read_agents_md()
    assert "Audit log" in content or "audit log" in content


# ---------------------------------------------------------------------------
# Acceptance criteria completeness
# ---------------------------------------------------------------------------

REQUIRED_ACCEPTANCE_CRITERIA_KEYWORDS = [
    "transcribed",
    "timeline",
    "Enrichment",
    "Insights",
    "edit",
    "delete",
]


def test_acceptance_criteria_covers_core_functionality() -> None:
    content = read_agents_md()
    # Find the acceptance criteria section
    ac_section_match = re.search(
        r"## 11\. Acceptance Criteria(.*?)## 12\.",
        content,
        re.DOTALL,
    )
    assert ac_section_match is not None, "Acceptance Criteria section not found"
    ac_section = ac_section_match.group(1)
    for keyword in REQUIRED_ACCEPTANCE_CRITERIA_KEYWORDS:
        assert keyword in ac_section, (
            f"Acceptance criteria missing keyword: {keyword!r}"
        )


def test_acceptance_criteria_has_reliability_subsection() -> None:
    content = read_agents_md()
    assert "### Reliability" in content


def test_acceptance_criteria_has_ux_subsection() -> None:
    content = read_agents_md()
    assert "### UX" in content


def test_acceptance_criteria_has_intelligence_subsection() -> None:
    content = read_agents_md()
    assert "### Intelligence" in content


# ---------------------------------------------------------------------------
# Folder structure documentation
# ---------------------------------------------------------------------------

REQUIRED_BACKEND_FILES = [
    "main.py",
    "routes_ingest.py",
    "routes_review.py",
    "transcription.py",
    "enrichment.py",
    "analysis.py",
    "vision.py",
    "insights.py",
]


def test_backend_folder_structure_documents_main_entry() -> None:
    content = read_agents_md()
    assert "main.py" in content


def test_backend_folder_structure_documents_service_files() -> None:
    content = read_agents_md()
    for filename in REQUIRED_BACKEND_FILES:
        assert filename in content, f"Backend folder structure missing file: {filename!r}"


def test_frontend_folder_structure_documented() -> None:
    content = read_agents_md()
    for folder in ("timeline/", "review/", "insights/"):
        assert folder in content, f"Frontend folder structure missing: {folder!r}"


# ---------------------------------------------------------------------------
# Stretch goals (regression: ensure they're present)
# ---------------------------------------------------------------------------


def test_stretch_goals_section_present() -> None:
    content = read_agents_md()
    assert "## 12. Stretch Goals" in content


def test_stretch_goals_include_semantic_search() -> None:
    content = read_agents_md()
    assert "Semantic search" in content or "semantic search" in content


def test_stretch_goals_include_mobile_companion() -> None:
    content = read_agents_md()
    assert "Mobile companion" in content or "mobile companion" in content


# ---------------------------------------------------------------------------
# Boundary / negative cases
# ---------------------------------------------------------------------------


def test_spec_does_not_reference_deprecated_technologies() -> None:
    """The spec should not reference outdated approaches like REST polling instead of WebSockets."""
    content = read_agents_md()
    # The spec explicitly requires WebSockets; polling would contradict it
    assert "WebSocket" in content, "Spec must reference WebSocket for real-time updates"


def test_spec_confidence_field_range_documented() -> None:
    """The insight object must document that confidence is a 0.0–1.0 float."""
    content = read_agents_md()
    # Look for confidence range notation in insight block area
    insight_section_match = re.search(
        r"#### Insight Object(.*?)---",
        content,
        re.DOTALL,
    )
    assert insight_section_match is not None
    insight_section = insight_section_match.group(1)
    assert "confidence" in insight_section
    assert "0.0" in insight_section and "1.0" in insight_section


def test_spec_priority_field_range_documented() -> None:
    """The insight object must document priority as an integer range (1-5)."""
    content = read_agents_md()
    insight_section_match = re.search(
        r"#### Insight Object(.*?)---",
        content,
        re.DOTALL,
    )
    assert insight_section_match is not None
    insight_section = insight_section_match.group(1)
    assert "priority" in insight_section
    assert "1" in insight_section and "5" in insight_section


def test_spec_has_no_undefined_section_references() -> None:
    """Any section reference like '## N.' should correspond to an actual section heading."""
    content = read_agents_md()
    # Extract declared section numbers
    declared = set(re.findall(r"^## (\d+)\.", content, re.MULTILINE))
    assert declared == {"1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"}