import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.schema import get_schema

if __name__ == "__main__":
    schema = get_schema(customer_id="c0001")  # any valid customer_id, just to open the connection
    for table, columns in schema.items():
        print(f"\n{table}")
        for col in columns:
            print(f"  {col}")