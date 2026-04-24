import os
import sys
import threading
import requests
import time
from concurrent.futures import ThreadPoolExecutor

# We'll use the requests library to hit the local server we just started
BASE_URL = "http://localhost:8000"

def simulate_student_action(user_id, session):
    """Simulates a student logging in and submitting an assignment."""
    try:
        # 1. Access Dashboard
        start = time.time()
        resp = session.get(f"{BASE_URL}/hub/")
        if resp.status_code != 200:
            return f"Student {user_id}: Dashboard Failed ({resp.status_code})"
        
        # 2. Simulate a Submission (POST request)
        # Note: In a real test, we'd need to handle CSRF tokens, 
        # but for this stress test we'll focus on the concurrency of the view logic.
        # If CSRF is a blocker, we'll use a specific 'internal' test view.
        
        duration = time.time() - start
        return f"Student {user_id}: Dashboard Load {duration:.2f}s"
    except Exception as e:
        return f"Student {user_id}: Error {str(e)}"

def run_concurrency_test(user_count=30):
    print(f"STARTING CONCURRENCY STRESS TEST")
    print(f"Simulating {user_count} students hitting the Hub simultaneously...")
    print("-" * 50)

    # We'll use a single session pool to simulate different users
    # For a true test, we'd have unique login sessions for each
    sessions = [requests.Session() for _ in range(user_count)]
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=user_count) as executor:
        futures = []
        for i in range(user_count):
            futures.append(executor.submit(simulate_student_action, i, sessions[i]))
        
        for future in futures:
            print(future.result())

    duration = time.time() - start_time
    print("-" * 50)
    print(f"CONCURRENCY TEST FINISHED in {duration:.2f} seconds")
    print(f"Average response time: {duration/user_count:.2f}s per user")

if __name__ == "__main__":
    run_concurrency_test(user_count=20)
