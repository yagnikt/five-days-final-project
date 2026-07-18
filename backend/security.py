import re
from typing import Tuple

def sanitize_and_validate_input(query: str, max_length: int = 500) -> Tuple[bool, str]:
    """
    Sanitizes and validates user-provided query strings to protect against prompt injection,
    malicious scripts, and system overloads.
    
    Args:
        query: Raw input query from the client.
        max_length: Maximum allowed character length for the query.
        
    Returns:
        A tuple of (is_safe: bool, sanitized_query: str).
    """
    if not query:
        return False, "Query cannot be empty."
        
    # 1. Length constraint check
    if len(query) > max_length:
        return False, f"Query exceeds maximum allowed length of {max_length} characters."
        
    # 2. Strip basic HTML tags / script injection
    sanitized = re.sub(r"<[^>]*>", "", query)
    
    # 3. Detect and block common jailbreak / prompt injection phrases
    jailbreak_patterns = [
        r"ignore\s+(?:all\s+)?previous\s+instructions",
        r"system\s+override",
        r"you\s+are\s+now\s+a\s+",
        r"developer\s+mode",
        r"disregard\s+(?:all\s+)?prior",
        r"bypass\s+safety",
        r"acting\s+as\s+a\s+"
    ]
    
    for pattern in jailbreak_patterns:
        if re.search(pattern, sanitized, re.IGNORECASE):
            return False, "Input triggered a prompt safety filter check. Please rephrase your request."
            
    # Clean up excess whitespace
    sanitized = " ".join(sanitized.split())
    
    return True, sanitized
