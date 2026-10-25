import re

def extract_referenced_customer(question: str) -> str | None:
    """
    Looks for an explicit customer identifier mentioned in the question,
    either as natural phrasing ('customer 55', 'customer id 55')
    or as a raw ID matching the stored format (e.g. 'c0006', 'C0001').
    Returns the digits found as a string, else None.
    """
    # Pattern 1: natural phrasing — "customer 55", "customer_id 55"
    phrase_pattern = r'customer[_\s]?(?:key|id)?\s*(\d+)'
    match = re.search(phrase_pattern, question, re.IGNORECASE)
    if match:
        return match.group(1)

    # Pattern 2: raw ID format — "c0006", "C0001", etc.
    id_pattern = r'\bc0*(\d+)\b'
    match = re.search(id_pattern, question, re.IGNORECASE)
    if match:
        return match.group(1)

    return None

def check_access(question: str, session_customer_id: str | None) -> str | None:
    """
    Returns a refusal message if the question references a different
    customer than the logged-in session. Compares by digits only,
    since customer_id may have a non-numeric prefix (e.g. 'C0000061').
    Returns None (no restriction) if session_customer_id is None (e.g. admin).
    """
    if session_customer_id is None:
        return None  # no customer context to compare against — nothing to restrict

    referenced_digits = extract_referenced_customer(question)
    if referenced_digits is None:
        return None

    # Extract digits from the session's real customer_id for comparison
    session_digits = re.sub(r'\D', '', session_customer_id).lstrip('0')
    referenced_digits_clean = referenced_digits.lstrip('0')

    if referenced_digits_clean != session_digits:
        return (
            "You don't have permission to view another customer's data. "
            "I can only answer questions about your own account."
        )
    return None

GLOBAL_SCOPE_PATTERNS = [
    r'\bwhich customer\b',
    r'\bwho has the (most|least|highest|lowest)\b',
    r'\back?ross all customers\b',
    r'\ball customers\b',
    r'\bevery customer\b',
    r'\btop customer\b',
]

def is_global_scope_question(question: str) -> bool:
    return any(re.search(p, question, re.IGNORECASE) for p in GLOBAL_SCOPE_PATTERNS)