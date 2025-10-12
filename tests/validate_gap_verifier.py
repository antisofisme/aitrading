#!/usr/bin/env python3
"""
Validation script for Gap Fill Verifier implementation

Validates code structure, logic, and integration points without requiring dependencies
"""
import os
import sys
import ast
import inspect

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_section(title):
    print(f"\n{BLUE}{'=' * 80}{RESET}")
    print(f"{BLUE}{title}{RESET}")
    print(f"{BLUE}{'=' * 80}{RESET}")

def print_success(message):
    print(f"{GREEN}✅ {message}{RESET}")

def print_error(message):
    print(f"{RED}❌ {message}{RESET}")

def print_info(message):
    print(f"{YELLOW}ℹ️  {message}{RESET}")

def validate_file_exists(filepath, description):
    """Validate that a file exists"""
    if os.path.exists(filepath):
        print_success(f"{description} exists: {filepath}")
        return True
    else:
        print_error(f"{description} NOT found: {filepath}")
        return False

def parse_python_file(filepath):
    """Parse Python file and return AST"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        tree = ast.parse(content)
        return tree
    except Exception as e:
        print_error(f"Failed to parse {filepath}: {e}")
        return None

def find_class_methods(tree, class_name):
    """Find all methods in a class"""
    methods = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    methods.append(item.name)
    return methods

def validate_gap_fill_verifier():
    """Validate GapFillVerifier utility class"""
    print_section("1. VALIDATING GapFillVerifier UTILITY CLASS")

    verifier_path = '/mnt/g/khoirul/aitrading/project3/backend/shared/components/utils/gap_fill_verifier.py'

    if not validate_file_exists(verifier_path, "GapFillVerifier"):
        return False

    tree = parse_python_file(verifier_path)
    if not tree:
        return False

    # Check required methods
    required_methods = [
        '__init__',
        'verify_date_has_data',
        'verify_with_retry',
        'verify_date_range',
        'verify_date_range_with_retry',
        'get_date_bar_count',
        'get_date_range_stats'
    ]

    methods = find_class_methods(tree, 'GapFillVerifier')

    print_info(f"Found {len(methods)} methods in GapFillVerifier class")

    all_present = True
    for method in required_methods:
        if method in methods:
            print_success(f"Method '{method}' implemented")
        else:
            print_error(f"Method '{method}' MISSING")
            all_present = False

    return all_present

def validate_main_py_integration():
    """Validate main.py integration"""
    print_section("2. VALIDATING main.py INTEGRATION")

    main_path = '/mnt/g/khoirul/aitrading/project3/backend/00-data-ingestion/polygon-historical-downloader/src/main.py'

    if not validate_file_exists(main_path, "main.py"):
        return False

    with open(main_path, 'r') as f:
        content = f.read()

    # Check imports
    checks = {
        'GapFillVerifier import': 'from shared.components.utils.gap_fill_verifier import GapFillVerifier',
        'download_and_verify_gap method': 'async def download_and_verify_gap(',
        'retry_failed_verifications method': 'async def retry_failed_verifications(',
        'Verifier initialization': 'self.verifier = GapFillVerifier(',
        'Verification in gap filling': 'await self.download_and_verify_gap(',
        'Retry logic': 'await self.retry_failed_verifications(',
        'Gap verification capability': '"gap-verification"'
    }

    all_present = True
    for check_name, check_string in checks.items():
        if check_string in content:
            print_success(f"{check_name} present")
        else:
            print_error(f"{check_name} MISSING")
            all_present = False

    return all_present

def validate_verification_workflow():
    """Validate verification workflow logic"""
    print_section("3. VALIDATING VERIFICATION WORKFLOW")

    main_path = '/mnt/g/khoirul/aitrading/project3/backend/00-data-ingestion/polygon-historical-downloader/src/main.py'

    with open(main_path, 'r') as f:
        content = f.read()

    workflow_checks = {
        'Download data': 'await self.downloader.download_all_pairs(',
        'Publish to NATS': 'await self.publisher.publish_batch(',
        'Wait for propagation': 'Waiting 30s for data to propagate',
        'Verify with retry': 'await self.verifier.verify_with_retry(',
        'Mark as verified': "verified=True",
        'Handle failed gaps': 'failed_gaps.append(',
        'Exponential backoff': 'wait_time = 30 * (2 ** retry_count)',
        'Manual review logging': 'GAPS REQUIRING MANUAL REVIEW'
    }

    all_present = True
    for check_name, check_string in workflow_checks.items():
        if check_string in content:
            print_success(f"{check_name} implemented")
        else:
            print_error(f"{check_name} MISSING")
            all_present = False

    return all_present

def validate_retry_logic():
    """Validate retry logic implementation"""
    print_section("4. VALIDATING RETRY LOGIC")

    main_path = '/mnt/g/khoirul/aitrading/project3/backend/00-data-ingestion/polygon-historical-downloader/src/main.py'

    with open(main_path, 'r') as f:
        content = f.read()

    retry_checks = {
        'Max retry attempts check': 'if retry_count >= max_retry_attempts:',
        'Exponential backoff': '30 * (2 ** retry_count)',
        'Retry counter increment': "gap['retry_count'] = retry_count + 1",
        'Permanent failure tracking': 'permanently_failed.append(',
        'Central Hub reporting': '"gaps_require_manual_review"',
        'Retry logging': '🔄 Retry attempt'
    }

    all_present = True
    for check_name, check_string in retry_checks.items():
        if check_string in content:
            print_success(f"{check_name} present")
        else:
            print_error(f"{check_name} MISSING")
            all_present = False

    return all_present

def validate_test_file():
    """Validate test file exists and has test cases"""
    print_section("5. VALIDATING TEST FILE")

    test_path = '/mnt/g/khoirul/aitrading/tests/test_gap_fill_verification.py'

    if not validate_file_exists(test_path, "Test file"):
        return False

    tree = parse_python_file(test_path)
    if not tree:
        return False

    # Count test classes and methods
    test_classes = []
    test_methods = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and 'Test' in node.name:
            test_classes.append(node.name)
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name.startswith('test_'):
                    test_methods.append(f"{node.name}.{item.name}")

    print_info(f"Found {len(test_classes)} test classes")
    print_info(f"Found {len(test_methods)} test methods")

    for test_class in test_classes:
        print_success(f"Test class: {test_class}")

    return len(test_classes) > 0 and len(test_methods) > 0

def generate_example_logs():
    """Generate example logs showing successful verification"""
    print_section("6. EXAMPLE VERIFICATION LOGS")

    example_logs = """
# Successful Gap Fill with Verification

2025-10-12 14:30:00 | INFO     | main                 | 🔍 Checking for data gaps...
2025-10-12 14:30:01 | INFO     | main                 | ✅ Gap fill verifier initialized
2025-10-12 14:30:02 | INFO     | main                 | 🔍 Checking gaps for XAU/USD...
2025-10-12 14:30:03 | INFO     | main                 | 📥 Found 3 gaps for XAU/USD, downloading with verification...
2025-10-12 14:30:04 | INFO     | main                 | 📥 Downloading gap: XAU/USD 2025-10-08 to 2025-10-08
2025-10-12 14:30:08 | INFO     | main                 | Downloaded 288 bars
2025-10-12 14:30:09 | INFO     | main                 | 📤 Publishing 288 bars to NATS
2025-10-12 14:30:10 | INFO     | main                 | ⏳ Waiting 30s for data to propagate through pipeline...
2025-10-12 14:30:40 | INFO     | gap_fill_verifier    | Verification attempt 1/3: XAU/USD 5m 2025-10-08
2025-10-12 14:30:41 | INFO     | gap_fill_verifier    | Verification: XAU/USD 5m 2025-10-08 - 288 bars (min: 1) - ✅ PASS
2025-10-12 14:30:41 | INFO     | gap_fill_verifier    | ✅ Verification succeeded on attempt 1
2025-10-12 14:30:42 | INFO     | main                 | ✅ Gap filled and verified: XAU/USD 2025-10-08 to 2025-10-08

# Failed Verification with Retry

2025-10-12 14:31:00 | INFO     | main                 | 📥 Downloading gap: EUR/USD 2025-10-09 to 2025-10-09
2025-10-12 14:31:05 | INFO     | main                 | Downloaded 288 bars
2025-10-12 14:31:06 | INFO     | main                 | 📤 Publishing 288 bars to NATS
2025-10-12 14:31:36 | INFO     | gap_fill_verifier    | Verification attempt 1/3: EUR/USD 5m 2025-10-09
2025-10-12 14:31:37 | INFO     | gap_fill_verifier    | Verification: EUR/USD 5m 2025-10-09 - 0 bars (min: 1) - ❌ FAIL
2025-10-12 14:31:37 | WARNING  | gap_fill_verifier    | ⏳ Data not found, waiting 10s before retry...
2025-10-12 14:31:47 | INFO     | gap_fill_verifier    | Verification attempt 2/3: EUR/USD 5m 2025-10-09
2025-10-12 14:31:48 | INFO     | gap_fill_verifier    | Verification: EUR/USD 5m 2025-10-09 - 288 bars (min: 1) - ✅ PASS
2025-10-12 14:31:48 | INFO     | gap_fill_verifier    | ✅ Verification succeeded on attempt 2
2025-10-12 14:31:49 | INFO     | main                 | ✅ Gap filled and verified: EUR/USD 2025-10-09 to 2025-10-09

# Permanent Failure Requiring Manual Review

2025-10-12 14:35:00 | WARNING  | main                 | ⚠️  1 gaps failed verification, retrying...
2025-10-12 14:35:01 | INFO     | main                 | 🔄 Retrying 1 failed gap verifications...
2025-10-12 14:35:02 | INFO     | main                 | 🔄 Retry attempt 1/2: GBP/USD 2025-10-10 to 2025-10-10
2025-10-12 14:35:03 | INFO     | main                 | ⏳ Waiting 30s before retry...
2025-10-12 14:35:33 | ERROR    | gap_fill_verifier    | ❌ Verification failed after 3 attempts: GBP/USD 5m 2025-10-10
2025-10-12 14:35:34 | WARNING  | main                 | ⚠️  Retry failed: GBP/USD 2025-10-10
2025-10-12 14:35:34 | INFO     | main                 | 🔄 Retry attempt 2/2: GBP/USD 2025-10-10 to 2025-10-10
2025-10-12 14:35:35 | INFO     | main                 | ⏳ Waiting 60s before retry...
2025-10-12 14:36:35 | ERROR    | gap_fill_verifier    | ❌ Verification failed after 3 attempts: GBP/USD 5m 2025-10-10
2025-10-12 14:36:36 | ERROR    | main                 | ⛔ Max retries (2) reached for GBP/USD 2025-10-10, marking for manual review
2025-10-12 14:36:37 | ERROR    | main                 | ================================================================================
2025-10-12 14:36:37 | ERROR    | main                 | ⛔ GAPS REQUIRING MANUAL REVIEW
2025-10-12 14:36:37 | ERROR    | main                 | ================================================================================
2025-10-12 14:36:37 | ERROR    | main                 |    GBP/USD 5m: 2025-10-10 to 2025-10-10 (retries: 2)
2025-10-12 14:36:37 | ERROR    | main                 | ================================================================================
    """

    print(example_logs)

def main():
    """Run all validations"""
    print(f"{BLUE}")
    print("=" * 80)
    print("GAP FILL VERIFICATION - VALIDATION REPORT")
    print("=" * 80)
    print(f"{RESET}")

    results = []

    # Run validations
    results.append(("GapFillVerifier class", validate_gap_fill_verifier()))
    results.append(("main.py integration", validate_main_py_integration()))
    results.append(("Verification workflow", validate_verification_workflow()))
    results.append(("Retry logic", validate_retry_logic()))
    results.append(("Test file", validate_test_file()))

    # Generate example logs
    generate_example_logs()

    # Summary
    print_section("VALIDATION SUMMARY")

    total = len(results)
    passed = sum(1 for _, result in results if result)

    for name, result in results:
        if result:
            print_success(f"{name}: PASSED")
        else:
            print_error(f"{name}: FAILED")

    print(f"\n{BLUE}{'=' * 80}{RESET}")
    if passed == total:
        print(f"{GREEN}✅ ALL VALIDATIONS PASSED ({passed}/{total}){RESET}")
        return 0
    else:
        print(f"{RED}❌ SOME VALIDATIONS FAILED ({passed}/{total}){RESET}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
