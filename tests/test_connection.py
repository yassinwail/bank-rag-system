import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.connection import get_connection

def test_connection():
    # Use a real customer_key that exists in your gold.users_login table
    test_customer_key = 50  # replace with an actual customer_key from your table

    try:
        conn = get_connection(test_customer_key)
        cursor = conn.cursor()

        # 1. Confirm the connection itself works
        cursor.execute("SELECT * from gold.users_login WHERE customer_key = ?", [test_customer_key])
        row = cursor.fetchone()
        print("Connection OK, test query returned:", row.user_id if row else "No rows returned")

        # 2. Confirm session context was actually set correctly
        cursor.execute("SELECT SESSION_CONTEXT(N'customer_key') AS ctx_value")
        row = cursor.fetchone()
        print("Session context customer_key:", row.ctx_value)

        cursor.close()
        conn.close()
        print("Connection closed cleanly.")

    except Exception as e:
        print("Connection failed:", e)

if __name__ == "__main__":
    test_connection()