from os import getenv
from dotenv import load_dotenv
from mssql_python import connect

# Load the connection string from the .env file
load_dotenv()
connection_string = getenv("SQL_CONNECTION_STRING")

# try:
#     # Establish the connection
#     print("Connecting to SQL Server...")
#     with connect(connection_string) as conn:
#         with conn.cursor() as cursor:
#             # Execute a test query
#             cursor.execute("SELECT @@VERSION;")
#             row = cursor.fetchone()
            
#             print("\nSuccessfully connected!")
#             print(f"SQL Server Version: {row[0]}")

# except Exception as e:
#     print(f"Error connecting to the database: {e}")

# with connect(connection_string) as conn:
    # with conn.cursor() as cursor:
    #     cursor.execute("SELECT * FROM gold.dim_customer;")
    #     rows = cursor.fetchall()
        
    #     for row in rows:
    #         print(f"ID: {row[0]}, Name: {row[1]}, Email: {row[2]}, city: {row[3]}")

