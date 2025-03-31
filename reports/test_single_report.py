#!/usr/bin/env python
"""
Helper script to run a single test class or test method
Usage:
  python test_single_report.py ReportConfigurationTests.test_list_report_configurations
"""

import sys
import os
import django
from django.test.runner import DiscoverRunner

# Setup Django environment
# Try to detect settings module name from project structure
# If your settings module has a different path, adjust this line
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def run_single_test(test_path):
    """
    Run a single test class or test method
    
    Args:
        test_path: String in format 'TestClass.test_method' or just 'TestClass'
    """
    # Split into class and method (if provided)
    parts = test_path.split('.')
    
    if len(parts) == 1:
        # Only class name provided
        test_label = f'reports.tests.{parts[0]}'
    else:
        # Class and method provided
        test_label = f'reports.tests.{parts[0]}.{parts[1]}'
    
    # Run the test
    test_runner = DiscoverRunner(verbosity=1, interactive=True)
    failures = test_runner.run_tests([test_label])
    
    sys.exit(bool(failures))

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python test_single_report.py TestClassName[.test_method_name]")
        sys.exit(1)
    
    run_single_test(sys.argv[1])