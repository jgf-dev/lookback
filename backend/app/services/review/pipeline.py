def orchestrate_end_of_day_review(items: list[dict]) -> dict:
    return {
        "voice_review_script": f"You captured {len(items)} items today.",
        "next_actions": ["Confirm inferred tasks", "Close open loops"],
    }
