"""Test the actual API response to see what's being sent to the frontend."""

import requests
import json

# Test expedition ID (using one from our test)
expedition_id = 11

# Make request (you'll need to add auth headers if required)
url = f"http://127.0.0.1:5000/api/expeditions/{expedition_id}"

# Use the owner chat_id
headers = {
    'X-Chat-ID': '5094426438',  # Owner user
    'Content-Type': 'application/json'
}

try:
    response = requests.get(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    print("\nResponse Headers:")
    print(json.dumps(dict(response.headers), indent=2))

    if response.status_code == 200:
        data = response.json()
        print("\n=== EXPEDITION DATA ===")
        print(f"ID: {data.get('id')}")
        print(f"Name: {data.get('name')}")
        print(f"\nItems: {len(data.get('items', []))}")
        print(f"Consumptions: {len(data.get('consumptions', []))}")

        print("\n=== CONSUMPTIONS ===")
        for i, consumption in enumerate(data.get('consumptions', [])[:3]):
            print(f"\nConsumption {i+1}:")
            print(json.dumps(consumption, indent=2))

    else:
        print(f"\nError Response:")
        print(response.text)

except Exception as e:
    print(f"Error: {e}")
