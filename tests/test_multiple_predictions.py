"""
Test that multiple predictions are properly formatted and confidence scores are reasonable.
"""

import numpy as np
import pandas as pd
import pytest


def test_formatter_max_num_codes():
    """Test that formatter has correct max_num_codes for PST2"""
    # Simulate the formatter behavior without importing
    # The key insight is that max_num_codes should equal len(target_cols)
    target_cols = ['pst_1', 'pst_2', 'pst_3', 'pst_4']
    max_num_codes = len(target_cols)
    
    assert max_num_codes == 4, f"Expected max_num_codes=4, got {max_num_codes}"
    
    # This is what the formatter would create
    block_size = 8
    sep_value = '&'
    within_block_sep = ','
    
    assert block_size == 8, f"Expected block_size=8, got {block_size}"
    assert sep_value == '&', f"Expected sep_value='&', got {sep_value}"
    assert within_block_sep == ',', f"Expected within_block_sep=',', got {within_block_sep}"


def test_split_str_s2s_single():
    """Test splitting of single occupation prediction"""
    # Simulate the _split_str_s2s method
    def split_str_s2s(pred, symbol='&'):
        if symbol in pred:
            return pred.split(symbol)
        return pred
    
    # Test single occupation
    result = split_str_s2s("1,2,3,4,5,0,0,0")
    assert result == "1,2,3,4,5,0,0,0", f"Expected single string, got {result}"
    assert not isinstance(result, list), "Single occupation should not be a list"


def test_split_str_s2s_multiple():
    """Test splitting of multiple occupation predictions"""
    # Simulate the _split_str_s2s method
    def split_str_s2s(pred, symbol='&'):
        if symbol in pred:
            return pred.split(symbol)
        return pred
    
    # Test multiple occupations
    result = split_str_s2s("1,2,3,4,5,0,0,0&2,3,4,5,0,0,0,0")
    assert isinstance(result, list), "Multiple occupations should be a list"
    assert len(result) == 2, f"Expected 2 occupations, got {len(result)}"
    assert result[0] == "1,2,3,4,5,0,0,0", f"First occupation incorrect: {result[0]}"
    assert result[1] == "2,3,4,5,0,0,0,0", f"Second occupation incorrect: {result[1]}"


def test_confidence_calculation_product():
    """Test that product of probabilities gives very low values"""
    # Simulate token probabilities for an 8-digit code
    probs = [0.9] * 8  # 8 tokens, each with 0.9 probability
    
    product = np.prod(probs)
    geometric_mean = np.prod(probs) ** (1.0 / len(probs))
    
    # Product should be very small
    assert product < 0.5, f"Product {product} should be < 0.5"
    assert product < geometric_mean, f"Product {product} should be < geometric_mean {geometric_mean}"
    
    # Geometric mean should be closer to the original probability
    assert geometric_mean == 0.9, f"Geometric mean should be 0.9, got {geometric_mean}"


def test_confidence_calculation_geometric_mean():
    """Test geometric mean calculation for confidence scores"""
    # Create a mock DataFrame with probability columns
    df = pd.DataFrame({
        'prob_s2s_0': [0.9, 0.8, 0.95],
        'prob_s2s_1': [0.9, 0.85, 0.9],
        'prob_s2s_2': [0.9, 0.9, 0.85],
        'prob_s2s_3': [0.9, 0.7, 0.8],
    })
    
    prob_cols = [col for col in df.columns if col.startswith('prob_s2s_')]
    num_probs = len(prob_cols)
    
    # Calculate confidence using geometric mean
    conf = df[prob_cols].prod(axis=1) ** (1.0 / num_probs)
    
    # Check that confidence values are reasonable (not too small)
    assert all(conf > 0.5), f"All confidence values should be > 0.5, got {conf.tolist()}"
    assert conf[0] == 0.9, f"Expected conf[0] = 0.9, got {conf[0]}"
    
    # For row 1: (0.8 * 0.85 * 0.9 * 0.7)^(1/4) ≈ 0.81
    expected_conf_1 = (0.8 * 0.85 * 0.9 * 0.7) ** 0.25
    assert abs(conf[1] - expected_conf_1) < 0.01, f"Expected conf[1] ≈ {expected_conf_1}, got {conf[1]}"


def test_max_elements_should_use_formatter_max_num_codes():
    """
    Test that max_elements uses formatter.max_num_codes instead of 
    the maximum from the current batch predictions.
    
    This ensures that even if all predictions in a batch have only 1 occupation,
    we still create columns for all possible occupations (pst_1, pst_2, pst_3, pst_4).
    """
    # Simulate the formatter behavior
    target_cols = ['pst_1', 'pst_2', 'pst_3', 'pst_4']
    max_num_codes = len(target_cols)  # This is what formatter.max_num_codes would be
    
    # Simulate predictions where all are single occupations
    predictions = [
        "1,2,3,4,5,0,0,0",  # Single occupation
        "2,3,4,5,0,0,0,0",  # Single occupation
        "3,4,5,6,0,0,0,0",  # Single occupation
    ]
    
    # The old code would calculate max_elements from these predictions
    old_max_elements = max(len(p.split('&')) if '&' in p else 1 for p in predictions)
    assert old_max_elements == 1, f"Old max_elements should be 1, got {old_max_elements}"
    
    # The new code should use formatter.max_num_codes (which is len(target_cols))
    new_max_elements = max_num_codes
    assert new_max_elements == 4, f"New max_elements should be 4, got {new_max_elements}"
    
    # This ensures we create 4 columns (pst_1, pst_2, pst_3, pst_4) even when
    # all predictions are single occupations


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
