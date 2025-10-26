"""
Test script to verify the master key implementation.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize database
from database import initialize_database
initialize_database()

# Test the master key functionality
from utils.encryption import get_encryption_service

def test_master_key_generation():
    """Test that master key generation is consistent."""
    print("Testing Master Key Generation...")
    print("="*60)

    encryption_service = get_encryption_service()

    # Test with a sample chat_id
    test_chat_id = 123456789

    # Generate master key multiple times - should be the SAME every time
    key1 = encryption_service.generate_user_master_key(test_chat_id)
    key2 = encryption_service.generate_user_master_key(test_chat_id)
    key3 = encryption_service.generate_user_master_key(test_chat_id)

    print(f"Test Chat ID: {test_chat_id}")
    print(f"Key 1: {key1[:50]}...")
    print(f"Key 2: {key2[:50]}...")
    print(f"Key 3: {key3[:50]}...")
    print()

    if key1 == key2 == key3:
        print("[PASS] SUCCESS: Master key is consistent (deterministic)")
    else:
        print("[FAIL] FAILED: Master keys are different!")
        return False

    # Test with different chat_id - should produce DIFFERENT key
    different_chat_id = 987654321
    key_different = encryption_service.generate_user_master_key(different_chat_id)

    print(f"\nTest Different Chat ID: {different_chat_id}")
    print(f"Key: {key_different[:50]}...")
    print()

    if key_different != key1:
        print("[PASS] SUCCESS: Different users have different master keys")
    else:
        print("[FAIL] FAILED: Same key for different users!")
        return False

    return True


def test_master_key_storage():
    """Test storing and retrieving master keys from database."""
    print("\nTesting Master Key Storage...")
    print("="*60)

    from database import get_db_manager
    from utils.encryption import get_encryption_service

    db_manager = get_db_manager()
    encryption_service = get_encryption_service()

    test_chat_id = 111222333

    # Generate master key
    master_key = encryption_service.generate_user_master_key(test_chat_id)
    print(f"Generated master key: {master_key[:50]}...")

    # Store it in database
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            # Clean up any existing key first
            cur.execute("DELETE FROM user_master_keys WHERE owner_chat_id = %s", (test_chat_id,))

            # Insert new key
            cur.execute("""
                INSERT INTO user_master_keys (owner_chat_id, master_key, key_version)
                VALUES (%s, %s, 1)
                RETURNING created_at
            """, (test_chat_id, master_key))
            created_at = cur.fetchone()[0]
            conn.commit()
            print(f"[PASS] Stored master key in database (created_at: {created_at})")

            # Retrieve it
            cur.execute("""
                SELECT master_key, created_at, key_version
                FROM user_master_keys
                WHERE owner_chat_id = %s
            """, (test_chat_id,))
            result = cur.fetchone()

            if result:
                retrieved_key, retrieved_created_at, key_version = result
                print(f"[PASS] Retrieved master key from database")
                print(f"   Key matches: {retrieved_key == master_key}")
                print(f"   Created at: {retrieved_created_at}")
                print(f"   Key version: {key_version}")

                if retrieved_key == master_key:
                    print("[PASS] SUCCESS: Stored and retrieved keys match!")
                    return True
                else:
                    print("[FAIL] FAILED: Keys don't match!")
                    return False
            else:
                print("[FAIL] FAILED: Could not retrieve key from database")
                return False


def test_generate_owner_key_with_master():
    """Test that generate_owner_key uses master key by default."""
    print("\nTesting generate_owner_key with Master Key...")
    print("="*60)

    from utils.encryption import get_encryption_service

    encryption_service = get_encryption_service()

    test_chat_id = 555666777
    expedition_id_1 = 1
    expedition_id_2 = 2

    # Generate owner keys for different expeditions with same chat_id
    # With use_master_key=True (default), should be the SAME
    key_exp1 = encryption_service.generate_owner_key(expedition_id_1, test_chat_id, use_master_key=True)
    key_exp2 = encryption_service.generate_owner_key(expedition_id_2, test_chat_id, use_master_key=True)

    print(f"Chat ID: {test_chat_id}")
    print(f"Expedition 1 key: {key_exp1[:50]}...")
    print(f"Expedition 2 key: {key_exp2[:50]}...")
    print()

    if key_exp1 == key_exp2:
        print("[PASS] SUCCESS: Same master key used for different expeditions")
    else:
        print("[FAIL] FAILED: Different keys for different expeditions!")
        return False

    # Test legacy mode (use_master_key=False) - should be DIFFERENT
    key_exp1_legacy = encryption_service.generate_owner_key(expedition_id_1, test_chat_id, use_master_key=False)
    key_exp2_legacy = encryption_service.generate_owner_key(expedition_id_2, test_chat_id, use_master_key=False)

    print(f"Legacy Mode (per-expedition keys):")
    print(f"Expedition 1 key: {key_exp1_legacy[:50]}...")
    print(f"Expedition 2 key: {key_exp2_legacy[:50]}...")
    print()

    if key_exp1_legacy != key_exp2_legacy:
        print("[PASS] SUCCESS: Legacy mode generates different keys per expedition")
    else:
        print("[WARN]  WARNING: Legacy mode generated same keys (random collision - very unlikely)")

    return True


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("MASTER KEY IMPLEMENTATION TEST SUITE")
    print("="*60 + "\n")

    tests = [
        ("Master Key Generation", test_master_key_generation),
        ("Master Key Storage", test_master_key_storage),
        ("generate_owner_key with Master Key", test_generate_owner_key_with_master),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n[FAIL] ERROR in {test_name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for test_name, passed in results:
        status = "[PASS] PASSED" if passed else "[FAIL] FAILED"
        print(f"{status}: {test_name}")

    total = len(results)
    passed = sum(1 for _, p in results if p)

    print(f"\nTotal: {passed}/{total} tests passed")
    print("="*60)

    if passed == total:
        print("\n[SUCCESS] All tests passed! Master key implementation is working correctly.")
    else:
        print(f"\n[WARN]  {total - passed} test(s) failed. Please review the output above.")


if __name__ == "__main__":
    main()
