from app.auth.service import verify_login
from app.graph.build import build_graph

graph = build_graph()

def main():
    username = input("Username: ")
    password = input("Password: ")

    user = verify_login(username, password)
    if not user:
        print("Invalid credentials.")
        return

    customer_id = user["customer_id"]
    role = user["role"]
    print(f"\nLogged in as {customer_id} ({role})")

    config = {"configurable": {"thread_id": f"{username}_session"}}

    while True:
        question = input("\nYou: ")
        if question.lower() in ("quit", "exit"):
            break

        result = graph.invoke({
            "customer_id": customer_id,
            "role": role,
            "question": question,
        }, config=config)

        answer = result.get("final_answer", "Sorry, I couldn't process that.")
        print(f"Assistant: {answer}")

if __name__ == "__main__":
    main()