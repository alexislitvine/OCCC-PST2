#!/usr/bin/env python
"""
Test script to verify that tqdm.write is used instead of print
to avoid progress bar output interference.
"""
import os
import sys

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_seq2seq_mixer_engine_uses_tqdm_write():
    """Test that seq2seq_mixer_engine.py uses tqdm.write for logging during training"""
    print("Testing tqdm.write usage in seq2seq_mixer_engine.py...")
    
    with open('histocc/seq2seq_mixer_engine.py', 'r') as f:
        content = f.read()
    
    # Check that tqdm is imported
    if "from tqdm import tqdm" not in content:
        print("✗ tqdm import not found")
        return False
    print("✓ tqdm is imported")
    
    # Split content into lines for analysis
    lines = content.split('\n')
    
    # Find the train_one_epoch function
    in_train_one_epoch = False
    in_evaluate = False
    issues = []
    
    for i, line in enumerate(lines, 1):
        # Track which function we're in
        if line.startswith('def train_one_epoch('):
            in_train_one_epoch = True
            in_evaluate = False
        elif line.startswith('def evaluate('):
            in_evaluate = True
            in_train_one_epoch = False
        elif line.startswith('def ') and not line.strip().startswith('def _'):
            in_train_one_epoch = False
            in_evaluate = False
        
        # Check for problematic print statements in train_one_epoch and evaluate
        if (in_train_one_epoch or in_evaluate) and 'print(' in line:
            # Exclude comments
            if not line.strip().startswith('#'):
                # Check if it's within the training loop (after tqdm iterator creation)
                # We allow print statements that are outside the loop
                if in_train_one_epoch and i > 89:  # After tqdm iterator line
                    issues.append(f"Line {i}: Found print() in train_one_epoch after tqdm initialization: {line.strip()}")
                elif in_evaluate:
                    issues.append(f"Line {i}: Found print() in evaluate function: {line.strip()}")
    
    # Check that tqdm.write is used for batch logging
    if 'tqdm.write(f\'[Epoch {epoch}] Batch' not in content:
        issues.append("Batch logging should use tqdm.write")
    else:
        print("✓ Batch logging uses tqdm.write")
    
    # Check that tqdm.write is used for evaluation logging
    if 'tqdm.write(f\'  Eval Batch' not in content:
        issues.append("Evaluation batch logging should use tqdm.write")
    else:
        print("✓ Evaluation batch logging uses tqdm.write")
    
    # Check that tqdm.write is used for GPU memory logging
    if 'tqdm.write(f\'  GPU Memory' not in content:
        issues.append("GPU memory logging should use tqdm.write")
    else:
        print("✓ GPU memory logging uses tqdm.write")
    
    # Check that tqdm.write is used for evaluation summary
    if 'tqdm.write(f\'EVALUATION RESULTS' not in content:
        issues.append("Evaluation results should use tqdm.write")
    else:
        print("✓ Evaluation results use tqdm.write")
    
    if issues:
        print("\n✗ Issues found:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    
    print("✓ All logging within tqdm context uses tqdm.write")
    return True


def main():
    print("=" * 70)
    print("Testing tqdm Output Management")
    print("=" * 70)
    
    result = test_seq2seq_mixer_engine_uses_tqdm_write()
    
    print("\n" + "=" * 70)
    if result:
        print("✓ All tests passed!")
        print("=" * 70)
        return 0
    else:
        print("✗ Some tests failed!")
        print("=" * 70)
        return 1


if __name__ == '__main__':
    sys.exit(main())
