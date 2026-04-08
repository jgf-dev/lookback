def enrich_with_context(raw_content: str) -> dict:
    return {
        "enriched_content": f"Contextual expansion: {raw_content}",
        "enriched_provenance": {"provider": "internal", "method": "contextual_expansion"},
    }
