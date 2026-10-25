import os
from dotenv import load_dotenv

load_dotenv()  # reads .env file into environment variables

class Settings:
    # SQL Server connection
    # DB_SERVER: str = os.getenv("DB_SERVER")
    # DB_NAME: str = os.getenv("DB_NAME")
    # DB_USER: str = os.getenv("DB_USER")
    # DB_PASSWORD: str = os.getenv("DB_PASSWORD")
    connection_string = os.getenv("SQL_CONNECTION_STRING")

    # Groq
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY")

settings = Settings()