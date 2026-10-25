from app.text_to_sql.executor import answer_sql_question, format_as_table

def test_simple_question():
    customer_id = "c0001"
    question = ""

    result = answer_sql_question(customer_id, question)  # admin bypasses access check

    if isinstance(result, str):
        print(result)  # refusal message, if access check triggered
    else:
        print(format_as_table(result))

if __name__ == "__main__":
    test_simple_question()