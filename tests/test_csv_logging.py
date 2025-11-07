#!/usr/bin/env python
"""
Test script to verify CSV logging functionality for training history.
"""
import os
import sys

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_csv_logging_function_exists():
    """Test that save_history_to_csv function is defined"""
    print("Testing CSV logging function definition...")
    
    # Get the base directory (parent of tests directory)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Test trainer.py
    with open(os.path.join(base_dir, 'histocc/trainer.py'), 'r') as f:
        content = f.read()
    
    if 'def save_history_to_csv' not in content:
        print("✗ save_history_to_csv function NOT found in trainer.py")
        return False
    
    print("✓ save_history_to_csv function found in trainer.py")
    
    # Check that it's called in run_eval
    if 'save_history_to_csv(history, model_name)' not in content:
        print("✗ save_history_to_csv is not called in trainer.py")
        return False
    
    print("✓ save_history_to_csv is called in run_eval")
    
    # Check imports
    if 'import csv' not in content:
        print("✗ csv module is not imported")
        return False
    
    print("✓ csv module is imported")
    
    if 'OrderedDict' not in content:
        print("✗ OrderedDict is not imported")
        return False
    
    print("✓ OrderedDict is imported")
    
    return True


def test_csv_logging_features():
    """Test that CSV logging features are present in the code"""
    print("\nTesting CSV logging implementation details...")
    
    # Get the base directory (parent of tests directory)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    with open(os.path.join(base_dir, 'histocc/trainer.py'), 'r') as f:
        content = f.read()
    
    features = [
        ('CSV file path creation', '_history.csv'),
        ('CSV DictWriter usage', 'csv.DictWriter'),
        ('CSV header writing', 'writer.writeheader()'),
        ('Epoch column', "'epoch'"),
        ('Train loss column', "'train_loss'"),
        ('Train accuracy column', "'train_acc'"),
        ('Validation loss column', "'val_loss'"),
        ('Validation accuracy column', "'val_acc'"),
    ]
    
    for name, pattern in features:
        if pattern in content:
            print(f"✓ {name} feature found")
        else:
            print(f"✗ {name} feature NOT found")
            return False
    
    return True


def test_csv_logging_integration():
    """Test that CSV logging is integrated into evaluation functions"""
    print("\nTesting CSV logging integration...")
    
    # Get the base directory (parent of tests directory)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    with open(os.path.join(base_dir, 'histocc/trainer.py'), 'r') as f:
        content = f.read()
    
    # Find run_eval function
    if 'def run_eval(' not in content:
        print("✗ run_eval function not found")
        return False
    
    # Extract run_eval function body (approximate)
    run_eval_start = content.find('def run_eval(')
    run_eval_end = content.find('\ndef ', run_eval_start + 1)
    run_eval_body = content[run_eval_start:run_eval_end]
    
    if 'save_history_to_csv(history, model_name)' not in run_eval_body:
        print("✗ save_history_to_csv not called in run_eval")
        return False
    
    print("✓ save_history_to_csv is called in run_eval")
    
    # Find run_eval_simple function
    if 'def run_eval_simple(' not in content:
        print("✗ run_eval_simple function not found")
        return False
    
    # Extract run_eval_simple function body (approximate)
    run_eval_simple_start = content.find('def run_eval_simple(')
    # Find the next function or end of file
    next_func = content.find('\ndef ', run_eval_simple_start + 1)
    if next_func == -1:
        run_eval_simple_body = content[run_eval_simple_start:]
    else:
        run_eval_simple_body = content[run_eval_simple_start:next_func]
    
    if 'save_history_to_csv(history, model_name)' not in run_eval_simple_body:
        print("✗ save_history_to_csv not called in run_eval_simple")
        return False
    
    print("✓ save_history_to_csv is called in run_eval_simple")
    
    return True


def main():
    """Run all tests"""
    print("="*80)
    print("Testing CSV Logging Functionality")
    print("="*80)
    
    tests = [
        ("CSV Logging Function Exists", test_csv_logging_function_exists),
        ("CSV Logging Features", test_csv_logging_features),
        ("CSV Logging Integration", test_csv_logging_integration),
    ]
    
    all_passed = True
    for test_name, test_func in tests:
        try:
            if not test_func():
                print(f"\n✗ {test_name} FAILED")
                all_passed = False
            else:
                print(f"\n✓ {test_name} PASSED")
        except Exception as e:
            print(f"\n✗ {test_name} FAILED with exception: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    print("\n" + "="*80)
    if all_passed:
        print("All tests PASSED ✓")
        print("="*80)
        return 0
    else:
        print("Some tests FAILED ✗")
        print("="*80)
        return 1


if __name__ == '__main__':
    sys.exit(main())
