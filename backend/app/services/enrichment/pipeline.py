def enrich_with_context(raw_content: str) -> dict:
    return {
        "enriched_content": f"Contextual expansion: {raw_content}",
        "provenance": {"provider": "internal", "method": "contextual_expansion"},
    }
