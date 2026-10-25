import uuid
import streamlit as st

from app.auth.service import verify_login
from app.graph.build import build_graph
from app.ui.charts import build_chart, rows_to_dataframe

st.set_page_config(page_title="Bank Assistant", page_icon="🏦", layout="centered")


@st.cache_resource
def get_graph():
    return build_graph()


graph = get_graph()

for key, default in {"user": None, "thread_id": None, "display": []}.items():
    if key not in st.session_state:
        st.session_state[key] = default


def new_chat():
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.display = []


def logout():
    st.session_state.user = None
    st.session_state.thread_id = None
    st.session_state.display = []


def build_assistant_message(result: dict) -> dict:
    msg = {"role": "assistant",
           "content": result.get("final_answer") or "Sorry, I couldn't process that."}

    rows = result.get("sql_results")
    if rows and (len(rows) > 1 or len(rows[0]) > 1):
        msg["rows"] = rows
        total = result.get("sql_row_count")
        if total and total > len(rows):
            msg["row_note"] = f"Showing {len(rows)} of {total} rows."

    if result.get("chart_type") and result.get("chart_rows"):
        fig = build_chart(result["chart_type"], result["chart_rows"])
        if fig is not None:
            msg["fig"] = fig
        else:
            msg["content"] += "\n\n_I couldn't turn this data into a chart, so the table is shown instead._"
            msg["expand_rows"] = True

    msg["sources"] = result.get("sources")
    msg["sql"] = result.get("sql_query")
    return msg


def render_message(msg: dict, is_admin: bool, idx: int):
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg.get("fig") is not None:
            st.plotly_chart(msg["fig"], theme=None, key=f"chart_{idx}")
        if msg.get("rows"):
            with st.expander("View data", expanded=msg.get("expand_rows", False)):
                st.dataframe(rows_to_dataframe(msg["rows"]), hide_index=True)
                if msg.get("row_note"):
                    st.caption(msg["row_note"])
        if msg.get("sources"):
            st.caption("Sources: " + "; ".join(msg["sources"]))
        if is_admin and msg.get("sql"):
            with st.expander("Generated SQL (admin only)"):
                st.code(msg["sql"], language="sql")


# ---------- Login screen ----------
if st.session_state.user is None:
    st.title("🏦 Bank Assistant")
    st.caption("Sign in to ask about your accounts and bank policies.")
    with st.form("login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in")
    if submitted:
        user = verify_login(username.strip(), password)
        if user:
            st.session_state.user = user
            new_chat()
            st.rerun()
        else:
            st.error("Incorrect username or password.")
    st.stop()

# ---------- Chat screen ----------
user = st.session_state.user
is_admin = user["role"] == "admin"

with st.sidebar:
    st.header("Bank Assistant")
    st.markdown("**Admin**" if is_admin else f"**Customer** · {user['customer_id']}")
    st.button("New chat", on_click=new_chat)
    st.button("Log out", on_click=logout)

st.title("🏦 Bank Assistant")

for i, msg in enumerate(st.session_state.display):
    render_message(msg, is_admin, i)

question = st.chat_input("Ask about your account or bank policy...")
if question:
    st.session_state.display.append({"role": "user", "content": question})
    render_message(st.session_state.display[-1], is_admin, len(st.session_state.display) - 1)

    with st.spinner("Thinking..."):
        try:
            result = graph.invoke(
                {
                    "customer_id": user["customer_id"],
                    "role": user["role"],       # always from the login lookup, never from input
                    "question": question,
                },
                config={"configurable": {"thread_id": st.session_state.thread_id}},
            )
            reply = build_assistant_message(result)
        except Exception as e:
            print("Graph error:", repr(e))    # full detail stays in the terminal
            reply = {"role": "assistant",
                     "content": "Sorry, something went wrong while processing that. Please try again."}

    st.session_state.display.append(reply)
    render_message(reply, is_admin, len(st.session_state.display) - 1)