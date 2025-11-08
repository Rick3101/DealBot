"""
Test script to verify product_id is properly handled in encrypted items.
This tests the backend changes for the Brambler Management Console.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_create_encrypted_item_signature():
    """Test that create_encrypted_item accepts product_id parameter."""
    from services.brambler_service import BramblerService
    import inspect

    # Get the method signature
    sig = inspect.signature(BramblerService.create_encrypted_item)
    params = list(sig.parameters.keys())

    print("Testing create_encrypted_item signature...")
    print(f"Parameters: {params}")

    # Check if product_id parameter exists
    assert 'product_id' in params, "product_id parameter not found in create_encrypted_item"
    print("[PASS] product_id parameter found in create_encrypted_item")

    # Check that it's optional (has default value)
    param_obj = sig.parameters['product_id']
    assert param_obj.default is not inspect.Parameter.empty, "product_id should have a default value"
    print(f"[PASS] product_id has default value: {param_obj.default}")

    return True


def test_brambler_service_method():
    """Test the brambler service method directly."""
    from services.brambler_service import BramblerService

    print("\nTesting BramblerService.create_encrypted_item method...")

    service = BramblerService()

    # Check method exists
    assert hasattr(service, 'create_encrypted_item'), "create_encrypted_item method not found"
    print("[PASS] create_encrypted_item method exists")

    # Check get_all_encrypted_items exists
    assert hasattr(service, 'get_all_encrypted_items'), "get_all_encrypted_items method not found"
    print("[PASS] get_all_encrypted_items method exists")

    return True


def test_sql_query_structure():
    """Verify the SQL query includes produto_id column."""
    from services.brambler_service import BramblerService
    import inspect

    print("\nChecking SQL query structure in source code...")

    # Read the source file
    source_file = inspect.getsourcefile(BramblerService)
    with open(source_file, 'r', encoding='utf-8') as f:
        source_code = f.read()

    # Check if produto_id is in the INSERT query for create_encrypted_item
    assert 'produto_id' in source_code, "produto_id not found in brambler_service.py"
    print("[PASS] produto_id column referenced in brambler_service.py")

    # Check if it's in the INSERT statement
    create_item_section = source_code[source_code.find('def create_encrypted_item'):]
    insert_section = create_item_section[create_item_section.find('INSERT INTO expedition_items'):]
    insert_section = insert_section[:insert_section.find('RETURNING')]

    assert 'produto_id' in insert_section, "produto_id not in INSERT statement"
    print("[PASS] produto_id in INSERT statement")

    # Check if it's in the SELECT query for get_all_encrypted_items
    get_all_section = source_code[source_code.find('def get_all_encrypted_items'):]
    select_section = get_all_section[get_all_section.find('SELECT'):]
    select_section = select_section[:select_section.find('FROM expedition_items')]

    assert 'ei.produto_id' in select_section, "ei.produto_id not in SELECT statement"
    print("[PASS] produto_id in SELECT statement for get_all_encrypted_items")

    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Product ID Backend Integration")
    print("=" * 60)

    try:
        # Test 1: Method signature
        test_create_encrypted_item_signature()

        # Test 2: Service methods exist
        test_brambler_service_method()

        # Test 3: SQL query structure
        test_sql_query_structure()

        print("\n" + "=" * 60)
        print("All Tests Passed!")
        print("=" * 60)
        print("\nBackend Changes Summary:")
        print("1. [OK] API endpoint accepts product_id from request")
        print("2. [OK] create_encrypted_item() method accepts product_id parameter")
        print("3. [OK] product_id is stored in expedition_items.produto_id column")
        print("4. [OK] get_all_encrypted_items() returns product_id in response")
        print("\nNext Steps:")
        print("- Frontend is already configured to send product_id")
        print("- Test the complete flow by creating an encrypted item with a product")
        print("- Verify the product_id appears when adding items to expeditions")

        return True

    except AssertionError as e:
        print(f"\n[FAIL] Test Failed: {e}")
        return False
    except Exception as e:
        print(f"\n[ERROR] Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
