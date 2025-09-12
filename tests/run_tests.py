"""
Test runner script for the Telegram bot handler tests.
Provides easy execution and reporting of test suites.
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path


def run_command(command, description=""):
    """Run a command and return the result"""
    print(f"\n{'='*60}")
    if description:
        print(f"Running: {description}")
    print(f"Command: {command}")
    print('='*60)
    
    try:
        # Use direct command execution without shell on Windows to avoid path issues
        if isinstance(command, str):
            cmd_parts = command.split()
        else:
            cmd_parts = command
            
        result = subprocess.run(cmd_parts, capture_output=True, text=True, cwd=os.getcwd())
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        print(f"Return code: {result.returncode}")
        return result.returncode == 0
    except Exception as e:
        print(f"Error running command: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run Telegram bot handler tests")
    parser.add_argument(
        "--type", 
        choices=["unit", "integration", "all"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--handler",
        help="Specific handler to test (e.g., login, product, buy)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run with coverage reporting"
    )
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install test dependencies before running"
    )
    
    args = parser.parse_args()
    
    # Ensure we're in the right directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print(f"Running tests from: {project_root}")
    
    # Install dependencies if requested
    if args.install_deps:
        print("\nInstalling test dependencies...")
        if not run_command("pip install pytest pytest-asyncio pytest-cov", "Installing pytest and plugins"):
            print("Failed to install dependencies")
            return 1
    
    # Build the pytest command
    cmd_parts = []
    
    if args.coverage:
        cmd_parts.extend([
            "python", "-m", "pytest",
            "--cov=handlers",
            "--cov=services", 
            "--cov=core",
            "--cov-report=html",
            "--cov-report=term-missing"
        ])
    else:
        cmd_parts.extend(["python", "-m", "pytest"])
    
    # Add verbosity
    if args.verbose:
        cmd_parts.append("-v")
    else:
        cmd_parts.append("-q")
    
    # Add test type marker
    if args.type == "unit":
        cmd_parts.extend(["-m", "unit"])
    elif args.type == "integration":
        cmd_parts.extend(["-m", "integration"])
    
    # Add specific handler test
    if args.handler:
        test_file = f"tests/test_handlers/test_{args.handler}_handler.py"
        if os.path.exists(test_file):
            cmd_parts.append(test_file)
        else:
            print(f"Handler test file not found: {test_file}")
            return 1
    else:
        cmd_parts.append("tests/")
    
    # Add common pytest options
    cmd_parts.extend([
        "--tb=short",  # Shorter traceback format
    ])
    
    # Run the tests
    command = " ".join(cmd_parts)
    success = run_command(command, f"Running {args.type} tests")
    
    if args.coverage and success:
        print("\nCoverage report generated in htmlcov/index.html")
    
    return 0 if success else 1


def run_specific_tests():
    """Run specific test scenarios"""
    scenarios = {
        "login": "Test login handler functionality",
        "product": "Test product management",
        "buy": "Test purchase flow",
        "user": "Test user management",
        "estoque": "Test inventory management",
        "start": "Test bot initialization",
        "commands": "Test command listing",
        "all_handlers": "Test all handlers",
        "quick": "Quick smoke tests",
        "full": "Full test suite with coverage"
    }
    
    print("Available test scenarios:")
    for key, description in scenarios.items():
        print(f"  {key}: {description}")
    
    choice = input("\nSelect a scenario (or 'custom' for custom command): ").strip()
    
    if choice == "custom":
        custom_cmd = input("Enter custom pytest command: ").strip()
        return run_command(custom_cmd, "Custom test command")
    
    elif choice == "quick":
        return run_command(
            "python -m pytest tests/test_handlers/test_start_handler.py::TestStartHandler::test_start_command_basic -v",
            "Quick smoke test"
        )
    
    elif choice == "full":
        return run_command(
            "python -m pytest tests/ --cov=handlers --cov=services --cov=core --cov-report=html -v",
            "Full test suite with coverage"
        )
    
    elif choice == "all_handlers":
        return run_command(
            "python -m pytest tests/test_handlers/ -v",
            "All handler tests"
        )
    
    elif choice in scenarios and choice != "all_handlers":
        test_file = f"tests/test_handlers/test_{choice}_handler.py"
        if os.path.exists(test_file):
            return run_command(
                f"python -m pytest {test_file} -v",
                f"Testing {choice} handler"
            )
        else:
            print(f"Test file not found: {test_file}")
            return False
    
    else:
        print(f"Unknown scenario: {choice}")
        return False


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Interactive mode
        try:
            success = run_specific_tests()
            sys.exit(0 if success else 1)
        except KeyboardInterrupt:
            print("\nTest execution cancelled.")
            sys.exit(1)
    else:
        # Command line mode
        sys.exit(main())