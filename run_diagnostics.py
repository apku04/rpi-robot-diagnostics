#!/usr/bin/env python3
"""
System Diagnostics Runner
Runs all hardware tests and reports status

This is the main entry point for running system diagnostics.
Add new test modules to the TESTS list to extend functionality.
"""

import sys
import time
import importlib.util
from pathlib import Path
from datetime import datetime

# Test configuration
TESTS = [
    {
        'name': 'I2C Multiplexer',
        'module': 'test_multiplexer',
        'critical': True,  # If True, failure stops further tests
        'enabled': True
    },
    {
        'name': 'Temperature Sensors',
        'module': 'test_temperature',
        'critical': False,
        'enabled': True
    },
    {
        'name': 'OLED Displays',
        'module': 'test_oled',
        'critical': False,
        'enabled': True,
        'args': {'visual': False}  # Set to True for visual tests
    }
]

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def load_test_module(module_name):
    """Dynamically load a test module"""
    try:
        module_path = Path(__file__).parent / f"{module_name}.py"
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        print(f"{Colors.FAIL}Error loading module {module_name}: {e}{Colors.ENDC}")
        return None

def print_header():
    """Print diagnostic header"""
    print(f"\n{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKCYAN}           SYSTEM DIAGNOSTICS - HARDWARE TEST SUITE{Colors.ENDC}")
    print(f"{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")

def print_test_header(test_name, test_num, total_tests):
    """Print test section header"""
    print(f"\n{Colors.BOLD}[{test_num}/{total_tests}] {test_name}{Colors.ENDC}")
    print(f"{'-'*70}")

def print_result(status, message):
    """Print test result with color"""
    if status == 'pass':
        print(f"{Colors.OKGREEN}✓ PASS{Colors.ENDC}: {message}")
    else:
        print(f"{Colors.FAIL}✗ FAIL{Colors.ENDC}: {message}")

def print_summary(results, start_time):
    """Print diagnostic summary"""
    elapsed = time.time() - start_time
    
    print(f"\n{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}DIAGNOSTIC SUMMARY{Colors.ENDC}")
    print(f"{Colors.BOLD}{'='*70}{Colors.ENDC}\n")
    
    passed = sum(1 for r in results if r['status'] == 'pass')
    failed = sum(1 for r in results if r['status'] == 'fail')
    skipped = sum(1 for r in results if r['status'] == 'skipped')
    
    print(f"Tests Run:    {len(results)}")
    print(f"{Colors.OKGREEN}Passed:       {passed}{Colors.ENDC}")
    if failed > 0:
        print(f"{Colors.FAIL}Failed:       {failed}{Colors.ENDC}")
    else:
        print(f"Failed:       {failed}")
    if skipped > 0:
        print(f"{Colors.WARNING}Skipped:      {skipped}{Colors.ENDC}")
    print(f"Duration:     {elapsed:.2f}s")
    
    print(f"\n{Colors.BOLD}Test Details:{Colors.ENDC}\n")
    
    for i, result in enumerate(results, 1):
        status_symbol = {
            'pass': f"{Colors.OKGREEN}✓{Colors.ENDC}",
            'fail': f"{Colors.FAIL}✗{Colors.ENDC}",
            'skipped': f"{Colors.WARNING}⊝{Colors.ENDC}"
        }
        
        symbol = status_symbol.get(result['status'], '?')
        print(f"  {symbol} {result['name']}: {result['message']}")
    
    print(f"\n{'='*70}\n")
    
    if failed == 0:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ All critical systems operational{Colors.ENDC}")
        return 0
    else:
        print(f"{Colors.FAIL}{Colors.BOLD}✗ System has failures - check details above{Colors.ENDC}")
        return 1

def run_diagnostics(verbose=True, quick=False):
    """
    Run all diagnostic tests
    
    Args:
        verbose: Print detailed output
        quick: Skip slower tests (visual displays, etc.)
    
    Returns:
        int: Exit code (0 = all pass, 1 = some failures)
    """
    start_time = time.time()
    results = []
    
    if verbose:
        print_header()
    
    enabled_tests = [t for t in TESTS if t['enabled']]
    
    for i, test_config in enumerate(enabled_tests, 1):
        if verbose:
            print_test_header(test_config['name'], i, len(enabled_tests))
        
        # Load test module
        module = load_test_module(test_config['module'])
        
        if module is None:
            results.append({
                'name': test_config['name'],
                'status': 'fail',
                'message': 'Failed to load test module'
            })
            continue
        
        # Check if module has run_test function
        if not hasattr(module, 'run_test'):
            results.append({
                'name': test_config['name'],
                'status': 'fail',
                'message': 'Module missing run_test() function'
            })
            continue
        
        # Run test
        try:
            # Get test arguments if specified
            test_args = test_config.get('args', {})
            
            # Modify args based on quick mode
            if quick and 'visual' in test_args:
                test_args['visual'] = False
            
            # Run test with or without args
            if test_args:
                result = module.run_test(**test_args)
            else:
                result = module.run_test()
            
            # Store result
            results.append({
                'name': test_config['name'],
                'status': result.get('status', 'fail'),
                'message': result.get('message', 'No message'),
                'details': result
            })
            
            if verbose:
                print_result(result.get('status', 'fail'), result.get('message', 'No message'))
                
                # Print additional details if available
                if result.get('error'):
                    print(f"  {Colors.FAIL}Error: {result['error']}{Colors.ENDC}")
            
            # Check if critical test failed
            if test_config.get('critical') and result.get('status') == 'fail':
                if verbose:
                    print(f"\n{Colors.FAIL}{Colors.BOLD}Critical test failed! Stopping diagnostics.{Colors.ENDC}")
                break
                
        except Exception as e:
            results.append({
                'name': test_config['name'],
                'status': 'fail',
                'message': f'Exception: {str(e)}'
            })
            
            if verbose:
                print_result('fail', f'Exception: {str(e)}')
            
            if test_config.get('critical'):
                if verbose:
                    print(f"\n{Colors.FAIL}{Colors.BOLD}Critical test failed! Stopping diagnostics.{Colors.ENDC}")
                break
    
    # Print summary
    if verbose:
        return print_summary(results, start_time)
    else:
        # Return simple pass/fail
        failed = sum(1 for r in results if r['status'] == 'fail')
        return 0 if failed == 0 else 1

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Run system hardware diagnostics',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Run all tests with full output
  %(prog)s --quick            # Run quick tests only (skip visual tests)
  %(prog)s --quiet            # Run silently, only return exit code
  %(prog)s --list             # List all available tests

Exit codes:
  0 - All tests passed
  1 - One or more tests failed
        """
    )
    
    parser.add_argument('--quick', '-q', action='store_true',
                        help='Run quick tests only (skip slower visual tests)')
    parser.add_argument('--quiet', action='store_true',
                        help='Suppress output (only return exit code)')
    parser.add_argument('--list', '-l', action='store_true',
                        help='List all available tests and exit')
    
    args = parser.parse_args()
    
    if args.list:
        print("\nAvailable Tests:")
        print("="*70)
        for i, test in enumerate(TESTS, 1):
            status = "ENABLED" if test['enabled'] else "DISABLED"
            critical = " [CRITICAL]" if test.get('critical') else ""
            print(f"{i}. {test['name']}{critical}")
            print(f"   Module: {test['module']}")
            print(f"   Status: {status}")
            print()
        return 0
    
    # Run diagnostics
    verbose = not args.quiet
    exit_code = run_diagnostics(verbose=verbose, quick=args.quick)
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
