"""Test script to verify endpoint performance improvements"""
import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()

# Get an admin chat_id from the database
from database import initialize_database, get_db_manager

initialize_database(os.getenv('DATABASE_URL'))
db_manager = get_db_manager()
with db_manager.get_connection() as conn:
    with conn.cursor() as cursor:
        cursor.execute("SELECT chat_id FROM usuarios WHERE nivel IN ('admin', 'owner') LIMIT 1")
        result = cursor.fetchone()

if not result:
    print("No admin user found in database!")
    exit(1)

admin_chat_id = result[0]
print(f"Using admin chat_id: {admin_chat_id}")

base_url = "http://127.0.0.1:5000"
headers = {"X-Chat-ID": str(admin_chat_id)}

endpoints = [
    "/api/dashboard/timeline",
    "/api/dashboard/analytics",
]

print("\n" + "="*60)
print("Testing Optimized Endpoint Performance")
print("="*60 + "\n")

for endpoint in endpoints:
    print(f"Testing: {endpoint}")
    start = time.time()

    try:
        response = requests.get(f"{base_url}{endpoint}", headers=headers, timeout=15)
        elapsed = time.time() - start

        if response.status_code == 200:
            data = response.json()
            print(f"  Status: SUCCESS")
            print(f"  Time: {elapsed:.3f}s")

            # Show some stats
            if endpoint == "/api/dashboard/timeline":
                stats = data.get("stats", {})
                print(f"  Total expeditions: {stats.get('total_expeditions', 0)}")
            elif endpoint == "/api/dashboard/analytics":
                overview = data.get("overview", {})
                print(f"  Total expeditions: {overview.get('total_expeditions', 0)}")
        else:
            elapsed = time.time() - start
            print(f"  Status: ERROR {response.status_code}")
            print(f"  Time: {elapsed:.3f}s")
            print(f"  Response: {response.text[:200]}")

    except requests.exceptions.Timeout:
        elapsed = time.time() - start
        print(f"  Status: TIMEOUT (>{elapsed:.3f}s)")
    except Exception as e:
        elapsed = time.time() - start
        print(f"  Status: ERROR - {str(e)}")
        print(f"  Time: {elapsed:.3f}s")

    print()

print("="*60)
print("Performance Test Complete")
print("="*60)
