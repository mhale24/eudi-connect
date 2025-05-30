#!/usr/bin/env python
"""Utility script to run tests individually to isolate test failures."""
import argparse
import os
import subprocess
import sys
from typing import List, Tuple


def find_tests(directory: str, pattern: str = "test_*.py") -> List[str]:
    """Find all test files in the given directory.
    
    Args:
        directory: Directory to search for test files
        pattern: Pattern to match test files
        
    Returns:
        List of test file paths
    """
    test_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                test_files.append(os.path.join(root, file))
    return test_files


def discover_test_functions(test_file: str) -> List[str]:
    """Discover all test functions in a test file.
    
    Args:
        test_file: Path to test file
        
    Returns:
        List of test function names
    """
    cmd = ["python", "-m", "pytest", test_file, "--collect-only", "-q"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error collecting tests from {test_file}:")
        print(result.stderr)
        return []
    
    test_functions = []
    for line in result.stdout.splitlines():
        if "::" in line:
            test_functions.append(line.strip())
    
    return test_functions


def run_test(test_function: str) -> Tuple[bool, str]:
    """Run a single test function.
    
    Args:
        test_function: Full test function identifier
        
    Returns:
        Tuple of (success, output)
    """
    cmd = ["python", "-m", "pytest", test_function, "-v"]
    print(f"Running test: {test_function}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    return result.returncode == 0, result.stdout + result.stderr


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run tests individually")
    parser.add_argument("--test-dir", default="tests", 
                        help="Directory containing tests")
    parser.add_argument("--pattern", default="test_*.py",
                        help="Pattern to match test files")
    parser.add_argument("--output", default="test_results.txt",
                        help="Output file for test results")
    args = parser.parse_args()
    
    test_files = find_tests(args.test_dir, args.pattern)
    
    all_tests = []
    for test_file in test_files:
        all_tests.extend(discover_test_functions(test_file))
    
    print(f"Found {len(all_tests)} tests")
    
    results = []
    success_count = 0
    failure_count = 0
    
    for test in all_tests:
        success, output = run_test(test)
        if success:
            success_count += 1
            results.append(f"PASS: {test}")
        else:
            failure_count += 1
            results.append(f"FAIL: {test}\n{output}")
    
    print(f"\nResults: {success_count} passed, {failure_count} failed")
    
    with open(args.output, "w") as f:
        f.write("\n".join(results))
    
    print(f"Test results written to {args.output}")
    
    return 0 if failure_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
