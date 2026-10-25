from app.graph.build import build_graph

app = build_graph()

test_questions = [
    "how many transactions do I have?",
    # "what's your policy on early loan repayment?",
    # "why was I charged a fee that seems to contradict the repayment policy?",
    "hey, how's it going?",
]

for q in test_questions:
    result = app.invoke({
        "customer_id": "C0000061",   # use a real customer_id from your data
        "role": "user",
        "question": q,
    })
    print(f"\nQ: {q}")
    print(f"Route: {result.get('route')}")
    print(f"A: {result.get('final_answer')}")