from mssql_python import connect

from app.config import settings


def verify_login(username: str, password: str) -> dict | None:
    """
    Looks the user up in gold.users_login and returns their identity
    (user_id, customer_key, role) on success, or None on failure.

    This runs before the customer_key is known, so it cannot go through
    app.db.connection.get_connection() -- that helper needs the customer_key
    to set the RLS session context.
    """
    conn = connect(settings.connection_string)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, customer_id, role FROM gold.users_login WHERE username = ? AND password = ?",
        [username, password]
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        return None
    return {"user_id": row.user_id, "customer_id": row.customer_id, "role": row.role}
