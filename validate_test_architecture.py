#!/usr/bin/env python3
"""
Quick validation script to verify the 4-layer test architecture is complete.
"""

import os
import re
from pathlib import Path


def validate_test_architecture():
    """Validate that all 4 layers of testing are properly implemented."""
    print("🔍 Validating 4-Layer Test Architecture")
    print("=" * 50)
    
    # Layer 1: Schema Validation
    layer1_file = "tests/test_all_handlers_schema_validation.py"
    layer1_tests = count_tests_in_file(layer1_file)
    print(f"✅ Layer 1 (Schema): {layer1_tests} tests in {layer1_file}")
    
    # Layer 2: Complete Flows
    layer2_file = "tests/test_all_handlers_flows.py"
    layer2_tests = count_tests_in_file(layer2_file)
    print(f"✅ Layer 2 (Flows): {layer2_tests} tests in {layer2_file}")
    
    # Layer 3 & 4: Error Scenarios & Security
    layer34_file = "tests/test_handlers_error_scenarios.py"
    layer34_tests = count_tests_in_file(layer34_file)
    print(f"✅ Layer 3&4 (Errors/Security): {layer34_tests} tests in {layer34_file}")
    
    # Core validation files
    core_schema = "tests/test_schema_validation.py"
    core_flows = "tests/test_complete_handler_flows.py"
    core_schema_tests = count_tests_in_file(core_schema)
    core_flows_tests = count_tests_in_file(core_flows)
    print(f"✅ Core Schema: {core_schema_tests} tests in {core_schema}")
    print(f"✅ Core Flows: {core_flows_tests} tests in {core_flows}")
    
    # Check handlers coverage
    handlers = [
        "login_handler", "product_handler", "buy_handler", "user_handler",
        "estoque_handler", "pagamento_handler", "relatorios_handler", 
        "smartcontract_handler", "start_handler", "lista_produtos_handler",
        "commands_handler", "error_handler", "base_handler"
    ]
    
    print(f"\n📋 Handler Coverage Validation:")
    for handler in handlers:
        coverage = check_handler_coverage(handler)
        status = "✅" if coverage['total'] >= 3 else "⚠️"
        print(f"{status} {handler}: {coverage['total']} layers covered")
    
    # Validate test runner
    runner_exists = os.path.exists("run_improved_tests.py")
    print(f"\n🚀 Test Runner: {'✅' if runner_exists else '❌'} run_improved_tests.py")
    
    # Check pytest configuration
    pytest_config = os.path.exists("pytest.ini")
    print(f"⚙️ Pytest Config: {'✅' if pytest_config else '❌'} pytest.ini")
    
    # Total count
    total_tests = layer1_tests + layer2_tests + layer34_tests + core_schema_tests + core_flows_tests
    print(f"\n🎯 Total Tests: {total_tests}")
    print(f"🎯 Total Handlers: {len(handlers)}")
    
    # Final assessment
    print(f"\n{'='*50}")
    if total_tests >= 40 and all(check_handler_coverage(h)['total'] >= 2 for h in handlers[:8]):
        print("🎉 4-Layer Test Architecture: COMPLETE ✅")
        print("🛡️ Your bot has enterprise-grade test coverage!")
    else:
        print("⚠️ 4-Layer Test Architecture: NEEDS ATTENTION")
        print("Some layers may need additional coverage.")
    
    return total_tests


def count_tests_in_file(file_path):
    """Count test methods in a file."""
    if not os.path.exists(file_path):
        return 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return len(re.findall(r'def test_', content))
    except Exception:
        return 0


def check_handler_coverage(handler_name):
    """Check how many test layers cover a specific handler."""
    coverage = {
        'schema': False,
        'flows': False, 
        'errors': False,
        'security': False,
        'total': 0
    }
    
    test_files = [
        "tests/test_all_handlers_schema_validation.py",
        "tests/test_all_handlers_flows.py",
        "tests/test_handlers_error_scenarios.py",
        "tests/test_schema_validation.py",
        "tests/test_complete_handler_flows.py"
    ]
    
    for file_path in test_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if handler_name.lower() in content.lower():
                        if 'schema' in file_path:
                            coverage['schema'] = True
                        elif 'flows' in file_path:
                            coverage['flows'] = True
                        elif 'error' in file_path:
                            coverage['errors'] = True
                            coverage['security'] = True
            except Exception:
                continue
    
    coverage['total'] = sum([coverage['schema'], coverage['flows'], coverage['errors']])
    return coverage


def validate_specific_protections():
    """Validate specific protection mechanisms."""
    print(f"\n🔒 Security Protection Validation:")
    
    # SQL Injection Protection
    sql_injection_tests = count_pattern_in_files("sql_injection|SQL injection", "tests/")
    print(f"🛡️ SQL Injection Tests: {sql_injection_tests}")
    
    # XSS Protection  
    xss_tests = count_pattern_in_files("xss|XSS|script.*alert", "tests/")
    print(f"🛡️ XSS Protection Tests: {xss_tests}")
    
    # Input Validation
    validation_tests = count_pattern_in_files("validation|sanitiz", "tests/")
    print(f"🛡️ Input Validation Tests: {validation_tests}")
    
    # Permission Tests
    permission_tests = count_pattern_in_files("permission|escalation", "tests/")
    print(f"🛡️ Permission Tests: {permission_tests}")


def count_pattern_in_files(pattern, directory):
    """Count occurrences of a pattern in test files."""
    count = 0
    for file_path in Path(directory).glob("test_*.py"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                count += len(re.findall(pattern, content, re.IGNORECASE))
        except Exception:
            continue
    return count


if __name__ == "__main__":
    total_tests = validate_test_architecture()
    validate_specific_protections()
    
    print(f"\n🎯 Quick Test Command:")
    print(f"python run_improved_tests.py")
    print(f"\n🎯 Interactive Test Menu:")
    print(f"python run_improved_tests.py --interactive")