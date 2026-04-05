def generate_day_review(date: str) -> dict[str, object]:
    """Return a simple day-review payload."""
    return {
        "date": date,
        "highlights": ["No highlights generated yet"],
        "open_questions": [],
    }
