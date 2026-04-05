def augment_search_context(query: str) -> list[str]:
    """Return placeholder snippets for future retrieval integration."""
    return [f"Context snippet for: {query}"]
