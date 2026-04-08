def discover_patterns(items: list[dict]) -> dict:
    """
    Create a summary dictionary of simple pattern metrics for the given items.
    
    Parameters:
        items (list[dict]): A list of items to analyze; each item is a dictionary (contents are not inspected).
    
    Returns:
        dict: A dictionary with keys:
            - "patterns": a single-element list containing the string "Total items analyzed: N", where N is the number of items.
            - "open_loops": an empty list.
            - "deadlines": an empty list.
            - "contradictions": an empty list.
    """
    return {
        "patterns": [f"Total items analyzed: {len(items)}"],
        "open_loops": [],
        "deadlines": [],
        "contradictions": [],
    }
