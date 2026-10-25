import re

FORBIDDEN_KEYWORDS = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "EXEC", "TRUNCATE", "MERGE", "CREATE"]

def extract_table_names(sql: str) -> set[str]:
    pattern = r'(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*)'
    return set(re.findall(pattern, sql, re.IGNORECASE))

def validate_sql(sql: str, allowed_tables: set[str]) -> bool:
    upper_sql = sql.upper()

    if not upper_sql.strip().startswith("SELECT"):
        return False
    if any(kw in upper_sql for kw in FORBIDDEN_KEYWORDS):
        return False
    if ";" in sql.strip().rstrip(";"):
        return False

    referenced = extract_table_names(sql)
    if not referenced.issubset(allowed_tables):
        return False

    return True