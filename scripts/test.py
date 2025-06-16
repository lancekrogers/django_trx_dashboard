#!/usr/bin/env python
"""
Test runner script for uv.
This provides a clean interface for running tests with uv.

Usage:
    uv run python scripts/test.py
    uv run python scripts/test.py --unit
    uv run python scripts/test.py --integration
    uv run python scripts/test.py --coverage
"""

import sys
import os
import subprocess

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_tests():
    """Run tests based on command line arguments."""
    args = sys.argv[1:]
    
    if not args or '--help' in args or '-h' in args:
        print(__doc__)
        print("\nOptions:")
        print("  --unit         Run only unit tests")
        print("  --integration  Run only integration tests")
        print("  --views        Run only view tests")
        print("  --models       Run only model tests")
        print("  --coverage     Run with coverage report")
        print("  --parallel     Run tests in parallel")
        print("  --failfast     Stop on first failure")
        print("  <app>          Run tests for specific app")
        print("  <test_path>    Run specific test")
        return
    
    # Build command
    cmd = [sys.executable, 'manage.py', 'test']
    
    # Handle special flags
    if '--coverage' in args:
        args.remove('--coverage')
        # Run with coverage
        coverage_cmd = [sys.executable, '-m', 'coverage', 'run', '--source=.', 'manage.py', 'test']
        coverage_cmd.extend(args)
        result = subprocess.run(coverage_cmd)
        if result.returncode == 0:
            # Show coverage report
            subprocess.run([sys.executable, '-m', 'coverage', 'report'])
            subprocess.run([sys.executable, '-m', 'coverage', 'html'])
            print("\nCoverage report generated in htmlcov/")
        return
    
    # Handle test markers
    if '--unit' in args:
        args.remove('--unit')
        cmd.extend(['--tag', 'unit'])
    elif '--integration' in args:
        args.remove('--integration')
        cmd.extend(['--tag', 'integration'])
    elif '--views' in args:
        args.remove('--views')
        cmd.extend(['--tag', 'views'])
    elif '--models' in args:
        args.remove('--models')
        cmd.extend(['--tag', 'models'])
    
    # Handle parallel
    if '--parallel' in args:
        args.remove('--parallel')
        cmd.extend(['--parallel', 'auto'])
    
    # Handle failfast
    if '--failfast' in args:
        args.remove('--failfast')
        cmd.append('--failfast')
    
    # Add remaining args (specific tests)
    cmd.extend(args)
    
    # Add verbosity
    if not any('-v' in arg for arg in args):
        cmd.extend(['-v', '2'])
    
    # Run tests
    subprocess.run(cmd)


if __name__ == '__main__':
    run_tests()