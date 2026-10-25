# tests/test_auth.py
from app.auth.service import verify_login

def test_valid_login():
    result = verify_login("C0001", "C0001")  # use a real customer_id from your table
    assert result is not None
    print("Login success:", result)

def test_invalid_login():
    result = verify_login("C0001", "wrong_password")
    assert result is None
    print("Correctly rejected invalid login")

if __name__ == "__main__":
    test_valid_login()
    test_invalid_login()
    print("All auth tests passed.")