import json
from groq import Groq
from app.config import settings
from app.db.schema import build_schema_description, CUSTOMER_ALLOWED_TABLES
from app.text_to_sql.generator import generate_sql
from app.db.sql_validator import validate_sql
from app.db.connection import get_connection
from app.graph.state import RAGState
from app.text_to_sql.access_check import check_access, is_global_scope_question
from langchain_core.messages import HumanMessage, AIMessage
from app.graph.history_utils import format_history
from app.graph.chart_utils import detect_chart_request

MAX_ROWS_FOR_LLM = 20
MAX_ROWS_FOR_CHART = 50

CHART_SQL_HINT = (
    "The user wants a chart. Return a small, grouped result with exactly ONE label column "
    "(for example a category, a transaction_type, or for months use gold.dim_date.month_start) "
    "followed by ONE numeric column (a SUM, COUNT or AVG), ordered sensibly (by date for "
    "time series). Do not return raw transaction rows."
)

client = Groq(api_key=settings.GROQ_API_KEY)

router_tools = [
    {
        "type": "function",
        "function": {
            "name": "route_query",
            "description": "Classify the user's banking question",
            "parameters": {
                "type": "object",
                "properties": {
                    "route": {
                        "type": "string",
                        "enum": ["sql", "docs", "both", "chitchat"],
                        "description": (
                            "'sql' = needs the customer's own transaction/loan data. "
                            "'docs' = needs bank policy/terms info. "
                            "'both' = needs personal data AND policy context together. "
                            "'chitchat' = greetings, small talk, or anything unrelated "
                            "to banking data or policy (out of scope)."
                        )
                    }
                },
                "required": ["route"]
            }
        }
    }
]


def access_check_node(state: RAGState) -> dict:
    if state["role"] == "admin":
        return {"access_denied": None}

    if is_global_scope_question(state["question"]):
        return {"access_denied": (
            "I can only answer questions about your own account — "
            "I'm not able to compare or rank data across other customers."
        )}

    refusal = check_access(state["question"], state["customer_id"])
    if refusal:
        return {"access_denied": refusal}
    return {"access_denied": None}



def route_node(state: RAGState) -> dict:
    role_context = (
        "This user is an ADMIN and can ask about any customer's data, aggregates, or rankings."
        if state["role"] == "admin"
        else "This user is a REGULAR CUSTOMER and can only ask about their own account."
    )

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": (
                f"Classify the banking question. {role_context}\n\n"
                "'sql' = the question asks for an actual number, amount, count, date, or "
                "record FROM THE DATABASE — e.g. 'what's the max repayment', 'how much did "
                "I pay', 'how many transactions', 'who has the most loans'. If the question "
                "could be answered by looking at transaction/loan/customer records, it's sql, "
                "even if the wording sounds general (like 'max', 'average', 'total').\n\n"
                "'docs' = the question asks about a RULE, TERM, or POLICY — e.g. 'what's the "
                "policy on late fees', 'is there a limit on repayments', 'what happens if I miss "
                "a payment'. These ask about what the bank's rules SAY, not what actually "
                "happened in someone's account.\n\n"
                "'both' = needs personal data AND policy context together.\n\n"
                "'chitchat' = greetings, small talk, or anything unrelated to banking."
                "Requests for a chart, graph, plot or visualization of the user's data are also 'sql'. "
            )},
            {"role": "user", "content": state["question"]}
        ],
        tools=router_tools,
        tool_choice={"type": "function", "function": {"name": "route_query"}}
    )
    args = json.loads(response.choices[0].message.tool_calls[0].function.arguments)
    return {"route": args["route"]}



def sql_node(state: RAGState) -> dict:
    schema_description = build_schema_description(state["customer_id"])
    history_context = format_history(state.get("messages", []))
    chart_type = detect_chart_request(state["question"])

    question = state["question"]
    if chart_type:
        question = f"{question}\n\n{CHART_SQL_HINT}"
    if history_context:
        question = f"Conversation so far:\n{history_context}\n\nCurrent question: {question}"

    sql = generate_sql(question, schema_description)
    print("Generated SQL:", sql)

    if not validate_sql(sql, CUSTOMER_ALLOWED_TABLES):
        return {"sql_query": sql, "sql_results": []}

    conn = get_connection(state["customer_id"], state["role"])
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    columns = [col[0] for col in cursor.description]
    cursor.close()
    conn.close()

    result_rows = [dict(zip(columns, r)) for r in rows]
    return {
        "sql_query": sql,
        "sql_results": result_rows[:MAX_ROWS_FOR_LLM],
        "sql_row_count": len(result_rows),
        "chart_type": chart_type,
        "chart_rows": result_rows[:MAX_ROWS_FOR_CHART] if chart_type else None,
    }

def docs_node(state: RAGState) -> dict:
    from app.docs_retrieval.retriever import retrieve_chunks_with_sources
    results = retrieve_chunks_with_sources(state["question"])
    return {
        "doc_chunks": [r["text"] for r in results],
        "sources": sorted({f"{r['source']} (p. {r['page']})" for r in results}),
    }


def chitchat_node(state: RAGState) -> dict:
    history_context = format_history(state.get("messages", []))

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": (
                "You are a friendly, casual banking assistant. You can only help with: "
                "the user's own account/transaction/loan data, bank policies, and "
                "normal pleasantries. Use the conversation history to remember things "
                "like a name the user gave you, for tone only — never as real account data. "
                "Politely decline and redirect anything outside banking.\n\n"
                f"Conversation so far:\n{history_context}"
            )},
            {"role": "user", "content": state["question"]}
        ],
        temperature=0.7
    )
    answer = response.choices[0].message.content.strip()
    return {
        "final_answer": answer,
        "messages": [HumanMessage(content=state["question"]), AIMessage(content=answer)],
    }


def generate_answer_node(state: RAGState) -> dict:
    from app.text_to_sql.executor import generate_natural_answer

    if state.get("access_denied"):
        answer = state["access_denied"]
    elif state.get("route") == "chitchat":
        return {}  # chitchat_node already added messages and set final_answer
    else:
        history_context = format_history(state.get("messages", []))
        question_for_answer = state["question"]
        if state.get("chart_type"):
            question_for_answer += (
                "\n\n(A chart of this data is displayed to the user next to your reply. "
                "Don't say you can't make charts; briefly summarise the key takeaway.)"
            )
        answer = generate_natural_answer(
            question_for_answer,
            sql_results=state.get("sql_results"),
            doc_chunks=state.get("doc_chunks"),
            history_context=history_context,
            sql_row_count=state.get("sql_row_count"),
            role=state["role"],
        )

    return {
        "final_answer": answer,
        "messages": [HumanMessage(content=state["question"]), AIMessage(content=answer)],
    }
    
def reset_turn_node(state: RAGState) -> dict:
    return {
        "access_denied": None, "route": None, "sql_query": None,
        "sql_results": None, "sql_row_count": None, "doc_chunks": None,
        "sources": None, "chart_type": None, "chart_rows": None, "final_answer": None,
    }