from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

def format_history(messages: list[BaseMessage], limit: int = 10) -> str:
    if not messages:
        return ""
    recent = messages[-limit:]
    lines = []
    for m in recent:
        role = "User" if isinstance(m, HumanMessage) else "Assistant"
        lines.append(f"{role}: {m.content}")
    return "\n".join(lines)