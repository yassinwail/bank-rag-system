from groq import Groq
from app.config import settings

client = Groq(api_key=settings.GROQ_API_KEY)

def generate_sql(user_question: str, schema_description: str) -> str:
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": (
                "You are a SQL Server query generator. "
                "Given a user's question, output ONLY a single valid T-SQL SELECT statement. "
                "No explanation, no markdown, no code fences — just the raw SQL.\n\n"
                f"{schema_description}"
            )},
            {"role": "user", "content": user_question}
        ],
        temperature=0
    )
    return response.choices[0].message.content.strip()