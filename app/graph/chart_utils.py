import re

CHART_WORDS = r"\b(chart|graph|plot|visuali[sz]e|visuali[sz]ation|visual|diagram|pie|histogram)\b"

def detect_chart_request(question: str) -> str | None:
    """Returns 'bar', 'line' or 'pie' if the user wants a visual, else None."""
    q = question.lower()
    if not re.search(CHART_WORDS, q):
        return None
    if re.search(r"\bpie\b", q):
        return "pie"
    if re.search(r"\bline (chart|graph)\b", q):
        return "line"
    if re.search(r"\bbar (chart|graph)\b", q):
        return "bar"
    if re.search(r"\b(share|proportion|percentage|breakdown|split|distribution)\b", q):
        return "pie"
    if re.search(r"\b(trend|over time|monthly|per month|by month|each month|daily|per day|weekly|yearly|per year|history|timeline|growth)\b", q):
        return "line"
    return "bar"