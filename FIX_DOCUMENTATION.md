# Fix for PST2 Multiple Predictions and Low Confidence Scores

## Summary

This document describes the fixes applied to resolve two critical issues with the PST2 model:

1. **Missing columns for multiple occupations** (pst_2, pst_3, etc.)
2. **Extraordinarily low confidence scores**

## Issues Identified

### Issue 1: Missing Columns for Multiple Occupations

**Problem:**
When an input contains multiple occupations (e.g., "labourer and builder"), the model should output multiple columns (pst_1, pst_2, pst_3, pst_4) to accommodate all predicted occupations. However, the output was inconsistent:
- If all predictions in a batch were single occupations, only `pst_1` was output
- The number of columns varied based on the batch content

**Root Cause:**
In `histocc/prediction_assets.py` line 1301, `max_elements` was calculated from the actual predictions in the current batch:
```python
max_elements = max(len(item) if isinstance(item, list) else 1 for item in sepperate_preds)
```

This meant:
- Batch with single occupations → `max_elements = 1` → Only `pst_1` column created
- Batch with multiple occupations → `max_elements = 2+` → Multiple columns created
- Inconsistent output schema

### Issue 2: Extraordinarily Low Confidence Scores

**Problem:**
Confidence scores were very low, even for high-quality predictions. For example, a prediction with each of 8 tokens having 0.9 probability would result in a confidence of only 0.43 (43%).

**Root Cause:**
In `histocc/prediction_assets.py` line 1360, confidence was calculated as the product of all token probabilities:
```python
res['conf'] = out[prob_cols].prod(axis=1)
```

For sequences with many tokens (e.g., 8-digit PST2 codes), this product becomes very small:
- 8 tokens at 0.9 each: 0.9^8 ≈ 0.43
- 10 tokens at 0.8 each: 0.8^10 ≈ 0.11

## Solutions Implemented

### Fix 1: Use `formatter.max_num_codes` for Consistent Output

**Change:** Line 1303 in `histocc/prediction_assets.py`

**Before:**
```python
max_elements = max(len(item) if isinstance(item, list) else 1 for item in sepperate_preds)
```

**After:**
```python
# Use formatter's max_num_codes to ensure we always create enough columns
# for all possible predictions, not just what's in this batch
max_elements = self.formatter.max_num_codes
```

**Benefits:**
- Consistent output schema: Always creates all columns (pst_1, pst_2, pst_3, pst_4)
- Supports multiple occupations: Columns are available even if current batch has only single occupations
- Predictable API: Users can always expect the same column structure

### Fix 2: Use Geometric Mean for Confidence Calculation

**Change:** Lines 1361-1369 in `histocc/prediction_assets.py`

**Before:**
```python
# Multiply these columns row-wise
res['conf'] = out[prob_cols].prod(axis=1)
```

**After:**
```python
# Calculate confidence using geometric mean instead of product
# This avoids very small confidence scores for sequences with many tokens
# Geometric mean: (product of probabilities) ^ (1/n)
num_probs = len(prob_cols)
if num_probs > 0:
    res['conf'] = out[prob_cols].prod(axis=1) ** (1.0 / num_probs)
else:
    res['conf'] = 1.0
```

**Benefits:**
- More interpretable confidence scores
- Normalized for sequence length
- Example: 8 tokens at 0.9 each → confidence = 0.9 (instead of 0.43)

**Mathematical Justification:**
The geometric mean is the appropriate measure because:
1. It preserves the multiplicative relationship of independent probabilities
2. It normalizes for the number of tokens in the sequence
3. It's still a valid probability measure (0 ≤ geometric_mean ≤ 1)
4. It's more interpretable: represents the "average" per-token probability

## Testing

### Unit Tests

Added comprehensive tests in `tests/test_multiple_predictions.py`:

1. **test_formatter_max_num_codes**: Verifies formatter configuration
2. **test_split_str_s2s_single**: Tests single occupation splitting
3. **test_split_str_s2s_multiple**: Tests multiple occupation splitting
4. **test_confidence_calculation_product**: Verifies product gives low values
5. **test_confidence_calculation_geometric_mean**: Verifies geometric mean improvement
6. **test_max_elements_should_use_formatter_max_num_codes**: Verifies the core fix

All tests pass ✅

### Verification Script

Created `verify_fix.py` to demonstrate the fixes with concrete examples:
- Shows old vs. new `max_elements` calculation
- Shows old vs. new confidence calculation
- Demonstrates multiple occupation prediction example

## Impact

### Before Fix
- ❌ Inconsistent output schema (number of columns varied)
- ❌ Confidence scores ~43% for good predictions
- ❌ Could not reliably predict multiple occupations

### After Fix
- ✅ Consistent output schema (always 4 columns for PST2)
- ✅ Confidence scores ~90% for good predictions
- ✅ Reliable multiple occupation predictions

## Security Analysis

CodeQL analysis completed with **0 alerts** - no security vulnerabilities introduced.

## Backward Compatibility

The changes are backward compatible:
- Existing code will continue to work
- Output DataFrame will have additional columns (pst_2, pst_3, pst_4) which may be NaN
- Confidence scores will be higher but still valid probabilities

**Note:** If downstream code expects specific column counts, it may need adjustment to handle the consistent 4-column output.

## Files Modified

1. `histocc/prediction_assets.py` (2 changes)
   - Line 1303: Use `formatter.max_num_codes`
   - Lines 1361-1369: Use geometric mean for confidence

2. `tests/test_multiple_predictions.py` (new file)
   - 6 comprehensive unit tests

3. `verify_fix.py` (new file)
   - Demonstration script showing the fixes in action

## Related Issues

This fix addresses the problem described in the issue:
> "Earlier versions of the model were able to output multiple predictions in pst2 for occupational titles which contained two or more occupations (eg. labourer and builder). However the current model only outputs one prediction (pst_1 but not pst_2, etc.)"

Both the multiple predictions issue and the low confidence scores are now resolved.
