#!/usr/bin/env python
"""
TEST RUNNER & CONFIGURATION
Orchestrates comprehensive internal system testing
"""

import os
import sys
import subprocess
import json
from datetime import datetime

TEST_CONFIG = {
    'project_name': 'Client Portal Internal System',
    'test_phases': [
        'Setup & Authentication',
        'Lead Management',
        'Client Onboarding',
        'Quote Creation',
        'Quote Approval',
        'Job Assignment',
        'Vendor Management',
        'Job Progression',
        'Delivery Management',
        'Invoice & Payment',
        'Integration Verification',
        'Cross-Portal Visibility',
    ],
    'portals_tested': [
        'Account Manager Portal',
        'Production Team Portal',
        'Vendor Portal',
        'Admin Portal',
        'Client Portal (simulated)',
    ],
    'critical_workflows': [
        'Lead → Client → Quote → Job',
        'Quote Approval → Job Auto-Creation',
        'Job → Vendor Assignment → Completion',
        'Job → Delivery → Invoice → Payment',
        'Notification Flow (all events)',
        'Activity Logging (all changes)',
    ],
}

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] {description}")
    print(f"Command: {cmd}")
    print("-" * 80)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=os.path.dirname(__file__))
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def main():
    print("\n" + "="*100)
    print("INTERNAL SYSTEM COMPREHENSIVE TEST SUITE")
    print("="*100)
    
    print(f"\nProject: {TEST_CONFIG['project_name']}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\nTest Phases:")
    for i, phase in enumerate(TEST_CONFIG['test_phases'], 1):
        print(f"  {i:2d}. {phase}")
    
    print("\nPortals Under Test:")
    for portal in TEST_CONFIG['portals_tested']:
        print(f"  • {portal}")
    
    print("\nCritical Workflows:")
    for workflow in TEST_CONFIG['critical_workflows']:
        print(f"  • {workflow}")
    
    print("\n" + "="*100)
    
    # Run the E2E test
    script_path = os.path.join(os.path.dirname(__file__), 'test_internal_system_e2e.py')
    success = run_command(
        f'python "{script_path}"',
        "Running E2E Integration Tests"
    )
    
    print("\n" + "="*100)
    print("TEST SUITE COMPLETE")
    print("="*100)
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
