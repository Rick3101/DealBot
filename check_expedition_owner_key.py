"""
Check if expedition 7 has an owner_key
"""

from services.expedition_service import ExpeditionService

def check_key():
    service = ExpeditionService()

    # Direct SQL query
    query = "SELECT id, name, owner_chat_id, owner_key FROM Expeditions WHERE id = %s"
    row = service._execute_query(query, (7,), fetch_one=True)

    if row:
        exp_id, name, owner_chat_id, owner_key = row
        print(f"Expedition ID: {exp_id}")
        print(f"Name: {name}")
        print(f"Owner Chat ID: {owner_chat_id}")
        print(f"Owner Key: {owner_key}")
        print(f"Has owner_key: {owner_key is not None and owner_key != ''}")

        if owner_key:
            print(f"Owner Key Length: {len(owner_key)}")
            print(f"Owner Key (first 30 chars): {owner_key[:30]}...")
        else:
            print("\n!!! PROBLEM: No owner_key found!")
            print("This expedition needs an owner_key to decrypt pirate names.")
            print("\nSolution: Run the owner key backfill migration or generate a new key.")
    else:
        print("Expedition 7 not found!")

if __name__ == "__main__":
    check_key()
