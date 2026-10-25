from mssql_python import connect
from app.config import settings


def get_connection(customer_id: str, role: str = "user"):
    conn = connect(settings.connection_string)
    cursor = conn.cursor()
    cursor.execute(
        "EXEC sp_set_session_context @key=N'customer_id', @value=?, @read_only=1",
        [customer_id]
    )
    cursor.execute(
        "EXEC sp_set_session_context @key=N'role', @value=?, @read_only=1",
        [role]
    )
    conn.commit()
    cursor.close()
    return conn