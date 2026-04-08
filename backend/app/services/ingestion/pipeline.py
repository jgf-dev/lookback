from datetime import datetime, timezone


def ingest_speech(text: str) -> dict:
    return {"source_type": "speech", "raw_content": text, "timestamp": datetime.now(timezone.utc)}


def ingest_screenshot(ocr_text: str) -> dict:
    return {
        "source_type": "screenshot",
        "raw_content": ocr_text,
        "timestamp": datetime.now(timezone.utc),
    }


def ingest_manual_note(note: str) -> dict:
    return {
        "source_type": "manual_note",
        "raw_content": note,
        "timestamp": datetime.now(timezone.utc),
    }
