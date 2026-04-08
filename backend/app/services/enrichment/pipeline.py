def enrich_with_context(raw_content: str) -> dict:
    """
    Builds an enriched content payload with provenance metadata.
    
    Parameters:
    	raw_content (str): Input text to include in the enriched content.
    
    Returns:
    	result (dict): Dictionary with keys:
    		- `enriched_content` (str): The input prefixed with "Contextual expansion: ".
    		- `provenance` (dict): Metadata with `provider` set to "internal" and `method` set to "contextual_expansion".
    """
    return {
        "enriched_content": f"Contextual expansion: {raw_content}",
        "provenance": {"provider": "internal", "method": "contextual_expansion"},
    }
