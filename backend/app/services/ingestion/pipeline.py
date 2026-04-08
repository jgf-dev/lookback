from datetime import datetime, timezone


def build_ingest_payload(source_type: str, raw_content: str) -> dict:
    return {
        "source_type": source_type,
        "raw_content": raw_content,
        "timestamp": datetime.now(timezone.utc),
    }


def ingest_speech(text: str) -> dict:
    return build_ingest_payload(source_type="speech", raw_content=text)


def ingest_screenshot(ocr_text: str) -> dict:
    return build_ingest_payload(source_type="screenshot", raw_content=ocr_text)


def ingest_manual_note(note: str) -> dict:
    return build_ingest_payload(source_type="manual_note", raw_content=note)
