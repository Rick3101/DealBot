"""Test script to check consumption data and debug the pirate_name issue."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from database import initialize_database, get_database_manager
from core.modern_service_container import get_expedition_service, initialize_services

# Initialize database
initialize_database()

# Initialize services
initialize_services()

# Get service
expedition_service = get_expedition_service()

# Get all expeditions
print("=== Checking Expeditions ===")
expeditions = expedition_service.get_active_expeditions()
print(f"Found {len(expeditions)} active expeditions")

for exp in expeditions[:3]:  # Check first 3
    print(f"\nExpedition ID: {exp.id}, Name: {exp.name}")

    # Get detailed response
    response = expedition_service.get_expedition_response(exp.id)

    if response:
        print(f"  Items: {len(response.items)}")
        print(f"  Consumptions: {len(response.consumptions)}")

        # Check consumptions
        for i, consumption in enumerate(response.consumptions[:5]):  # First 5
            print(f"\n  Consumption {i+1}:")
            print(f"    ID: {consumption.id}")
            print(f"    Consumer Name: {consumption.consumer_name}")
            print(f"    Pirate Name: {consumption.pirate_name}")
            print(f"    Product: {consumption.product_name}")
            print(f"    Quantity: {consumption.quantity}")
            print(f"    Total Price: {consumption.total_price}")
            print(f"    Payment Status: {consumption.payment_status}")

# Check expedition_pirates table directly
print("\n\n=== Checking expedition_pirates table ===")
db_manager = get_database_manager()
with db_manager.get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT ep.id, ep.expedition_id, ep.pirate_name, ep.original_name
            FROM expedition_pirates ep
            ORDER BY ep.id DESC
            LIMIT 10
        """)
        pirates = cur.fetchall()
        print(f"Found {len(pirates)} pirate records (showing last 10)")
        for p in pirates:
            print(f"  ID: {p[0]}, Exp: {p[1]}, Pirate: {p[2]}, Original: {p[3]}")

# Check expedition_assignments table
print("\n\n=== Checking expedition_assignments table ===")
with db_manager.get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT ea.id, ea.expedition_id, ea.pirate_id, ea.consumed_quantity
            FROM expedition_assignments ea
            ORDER BY ea.id DESC
            LIMIT 10
        """)
        assignments = cur.fetchall()
        print(f"Found {len(assignments)} assignment records (showing last 10)")
        for a in assignments:
            print(f"  ID: {a[0]}, Exp: {a[1]}, Pirate ID: {a[2]}, Quantity: {a[3]}")

print("\n=== Done ===")
