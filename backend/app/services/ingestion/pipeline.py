from datetime import datetime, timezone


def ingest_speech(text: str) -> dict:
    """
    Create an ingestion record for spoken input.
    
    Parameters:
        text (str): Transcribed speech content.
    
    Returns:
        dict: A record with keys:
            - `source_type` (str): The literal value "speech".
            - `raw_content` (str): The provided `text`.
            - `timestamp` (datetime): UTC timestamp when the record was created.
    """
    return {"source_type": "speech", "raw_content": text, "timestamp": datetime.now(timezone.utc)}


def ingest_screenshot(ocr_text: str) -> dict:
    """
    Create an ingestion record for text extracted from a screenshot.
    
    Parameters:
        ocr_text (str): Text produced by OCR from a screenshot image.
    
    Returns:
        dict: An ingestion dictionary with keys:
            - `source_type` (str): Always "screenshot".
            - `raw_content` (str): The provided `ocr_text`.
            - `timestamp` (datetime): UTC timestamp when the record was created.
    """
    return {
        "source_type": "screenshot",
        "raw_content": ocr_text,
        "timestamp": datetime.now(timezone.utc),
    }


def ingest_manual_note(note: str) -> dict:
    """
    Create an ingestion record for a manually entered note.
    
    Parameters:
        note (str): The text content of the manual note.
    
    Returns:
        dict: A dictionary with keys:
            - "source_type": the literal string "manual_note".
            - "raw_content": the provided note text.
            - "timestamp": a timezone-aware UTC datetime representing when the record was created.
    """
    return {
        "source_type": "manual_note",
        "raw_content": note,
        "timestamp": datetime.now(timezone.utc),
    }
