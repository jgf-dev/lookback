def orchestrate_end_of_day_review(items: list[dict]) -> dict:
    """
    Builds an end-of-day review payload for the provided items.
    
    Parameters:
        items (list[dict]): List of captured item records to summarize.
    
    Returns:
        dict: A review payload containing:
            - "voice_review_script": A string summarizing the count, e.g. "You captured {N} items today."
            - "next_actions": A list of two action strings: ["Confirm inferred tasks", "Close open loops"].
    """
    return {
        "voice_review_script": f"You captured {len(items)} items today.",
        "next_actions": ["Confirm inferred tasks", "Close open loops"],
    }
