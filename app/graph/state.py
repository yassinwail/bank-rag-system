from typing import TypedDict, Optional, Literal, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class RAGState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    customer_id: str
    role: str
    question: str
    access_denied: Optional[str]
    route: Optional[Literal["sql", "docs", "both", "chitchat"]]
    sql_query: Optional[str]
    sql_results: Optional[list[dict]]
    doc_chunks: Optional[list[str]]
    final_answer: Optional[str]
    sql_row_count: Optional[int]
    chart_type: Optional[str]          # "bar" | "line" | "pie" | None
    chart_rows: Optional[list[dict]]   # larger slice of results, used only for drawing
    sources: Optional[list[str]]       # policy document names and pages