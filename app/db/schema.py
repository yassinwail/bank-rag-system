from app.db.connection import get_connection

CUSTOMER_ALLOWED_TABLES = {
    "gold.fact_transactions",
    "gold.dim_loan",
    "gold.dim_customer",
    "gold.dim_branch",
    "gold.dim_channel",
    "gold.dim_date",
}

def get_schema(customer_id: str):
    conn = get_connection(customer_id)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, DATA_TYPE,
               CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        ORDER BY TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    schema = {}
    for row in rows:
        table_key = f"{row.TABLE_SCHEMA}.{row.TABLE_NAME}"
        schema.setdefault(table_key, []).append(
            f"{row.COLUMN_NAME} {row.DATA_TYPE}" +
            (f"({row.CHARACTER_MAXIMUM_LENGTH})" if row.CHARACTER_MAXIMUM_LENGTH else "") +
            (" NULL" if row.IS_NULLABLE == "YES" else " NOT NULL")
        )
    return schema


def build_schema_description(customer_id: str) -> str:
    schema = get_schema(customer_id)
    distinct_values = get_distinct_values(customer_id)

    lines = ["You can query the following tables (read-only):\n"]

    for table, columns in schema.items():
        if table not in CUSTOMER_ALLOWED_TABLES:
            continue
        lines.append(f"{table} ({', '.join(columns)})")

    lines.append("\nActual values stored in categorical columns (use these exact values in WHERE clauses, not paraphrases):")
    for col_key, values in distinct_values.items():
        lines.append(f"  {col_key}: {values}")

    lines.append(
        "\nJoin keys: fact_transactions.customer_key -> dim_customer.customer_key, "
        "fact_transactions.transaction_date_key -> dim_date.date_key, "
        "fact_transactions.loan_key -> dim_loan.loan_key, "
        "fact_transactions.branch_key -> dim_branch.branch_key, "
        "fact_transactions.channel_key -> dim_channel.channel_key, "
        "dim_loan.customer_id -> dim_customer.customer_id."
    )
    lines.append(
        "\nDo not include customer_key filters yourself — that is handled automatically by the system."
        "\nOnly generate SELECT statements against the tables listed above. "
        "Never generate INSERT, UPDATE, DELETE, DROP, or EXEC statements."
    )
    return "\n".join(lines)

CATEGORICAL_COLUMNS = {
    "gold.fact_transactions": ["transaction_type", "transaction_status"],
    "gold.dim_loan": ["loan_product", "currency_code"],
}

def get_distinct_values(customer_id: str, role: str = "admin") -> dict:
    """
    Fetches actual distinct values for known categorical columns,
    so the LLM knows the real stored values (e.g. 'POSTED' not 'Paid').
    Uses admin role internally since this is metadata, not customer data.
    """
    conn = get_connection(customer_id, role)
    cursor = conn.cursor()

    values = {}
    for table, columns in CATEGORICAL_COLUMNS.items():
        for column in columns:
            cursor.execute(f"SELECT DISTINCT {column} FROM {table}")
            rows = cursor.fetchall()
            values[f"{table}.{column}"] = [row[0] for row in rows]

    cursor.close()
    conn.close()
    return values