import requests
import json
import time

def test_apis():
    # Inside docker network, use service name 'web'
    try:
        requests.get("http://web:8000")
        base_url = "http://web:8000"
    except:
        base_url = "http://localhost:8000"
    
    print(f"Using Base URL: {base_url}")
    
    # 1. Register
    print("\nTesting /register...")
    payload = {
        "first_name": "Test",
        "last_name": "User",
        "age": 25,
        "monthly_income": 30000,
        "phone_number": 8888888888
    }
    try:
        r = requests.post(f"{base_url}/register", json=payload)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.json()}")
        new_customer_id = r.json().get('customer_id')
    except Exception as e:
        print(f"Error: {e}")
        new_customer_id = None

    # 2. Check Eligibility (for ingested customer 1)
    # John Doe (id 1) has 1 loan fully paid on time. Credit score should be high.
    print("\nTesting /check-eligibility for Customer 1...")
    payload = {
        "customer_id": 1,
        "loan_amount": 50000,
        "interest_rate": 10.0,
        "tenure": 12
    }
    r = requests.post(f"{base_url}/check-eligibility", json=payload)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.json()}")

    # 3. Create Loan
    print("\nTesting /create-loan for Customer 1...")
    r = requests.post(f"{base_url}/create-loan", json=payload)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.json()}")
    loan_id = r.json().get('loan_id')

    # 4. View Loan
    if loan_id:
        print(f"\nTesting /view-loan/{loan_id}...")
        r = requests.get(f"{base_url}/view-loan/{loan_id}")
        print(f"Status: {r.status_code}")
        print(f"Response: {r.json()}")

    # 5. View Customer Loans
    print("\nTesting /view-loans/1...")
    r = requests.get(f"{base_url}/view-loans/1")
    print(f"Status: {r.status_code}")
    print(f"Response: {r.json()}")

if __name__ == "__main__":
    test_apis()
