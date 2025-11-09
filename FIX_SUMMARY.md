# Summary: Fix for Low Accuracy in Finetuned Models

## Issue Resolved

**Problem**: Finetuned models and predictions using `predict_on_pst.py` showed very low accuracy (e.g., 6%) even when predictions were manifestly very good - i.e., the correct codes were being predicted.

**Root Cause**: The accuracy calculation in `histocc/eval_metrics.py` (method `_acc`) used a flawed formula that unfairly penalized models when they provided multiple predictions (e.g., top-5) but ground truth had fewer codes (e.g., just 1).

## Technical Details

### The Problematic Formula

```python
# OLD (incorrect)
res = (pred_in_true + true_in_pred) / (2 * max(len(y_true), len(y_pred)))
```

**Why this was wrong**: The denominator `2 * max(len(y_true), len(y_pred))` grows with the maximum count, which unfairly penalizes scenarios where predictions outnumber ground truth.

**Example**:
- Ground truth: 1 code
- Predictions: 5 codes (with the correct one included)
- Old accuracy: (1 + 1) / (2 * 5) = **20%** ❌

### The Fixed Formula

```python
# NEW (correct)
precision_like = pred_in_true / len(y_pred)  # What fraction of predictions are correct?
recall_like = true_in_pred / len(y_true)     # What fraction of ground truth was found?
res = (precision_like + recall_like) / 2     # Average of both
```

**Why this is better**: It properly balances two aspects:
1. **Precision-like**: Rewards models for not making too many wrong predictions
2. **Recall-like**: Rewards models for finding all the ground truth codes

**Same Example**:
- Ground truth: 1 code
- Predictions: 5 codes (with the correct one included)
- New accuracy: (1/5 + 1/1) / 2 = **60%** ✅

## Impact

### Accuracy Score Improvements

| Scenario | Old Accuracy | New Accuracy | Improvement |
|----------|--------------|--------------|-------------|
| 1 truth, 3 preds (1 correct) | 33.3% | 66.7% | +33.3pp |
| 1 truth, 5 preds (1 correct) | 20.0% | 60.0% | +40.0pp |
| 1 truth, 10 preds (1 correct) | 10.0% | 55.0% | +45.0pp |

### Cases That Work Correctly (No Change)

| Scenario | Both Old & New |
|----------|----------------|
| Perfect match (1 code) | 100% ✅ |
| Perfect match (2 codes) | 100% ✅ |
| No match | 0% ✅ |
| Partial match (1 of 2) | 50% ✅ |

## Files Modified

1. **`histocc/eval_metrics.py`**
   - Fixed the `_acc()` method (lines 96-157)
   - Added comprehensive docstring with examples
   - Added edge case handling (empty predictions/truth)

2. **`tests/test_accuracy_metric.py`** (NEW)
   - Comprehensive test suite for accuracy calculations
   - Tests for various scenarios (perfect match, partial match, no match, etc.)
   - Tests for realistic top-k prediction scenarios

3. **`ACCURACY_FIX_DOCUMENTATION.md`** (NEW)
   - Detailed explanation of the problem and solution
   - Comparison tables showing improvements
   - Guidance on backward compatibility

4. **`example_accuracy_evaluation.py`** (NEW)
   - Example script showing how to use the fixed metric
   - Demonstrates per-observation metrics
   - Includes interpretation guidance

## How to Verify the Fix

### Option 1: Re-run Your Predictions
```python
from histocc import OccCANINE, EvalEngine

# Load your model
model = OccCANINE("path/to/your/model.bin", hf=False, system="pst")

# Run predictions
predictions = model(your_data, k_pred=10)

# Evaluate with fixed accuracy
eval_engine = EvalEngine(model, ground_truth, predictions, pred_col="pst_")
accuracy = eval_engine.accuracy()
print(f"Accuracy: {accuracy:.2%}")  # Should now be much higher!
```

### Option 2: Run the Demonstration
```bash
python /tmp/demonstrate_fix.py
```

This shows the before/after comparison for various scenarios.

### Option 3: Run the Tests
```bash
python -m unittest tests.test_accuracy_metric
```

## What This Means for Your Work

If you've been seeing ~6% accuracy on your finetuned PST models:

1. **The models are likely performing better than the metric suggested**
   - The old metric was undercounting actual performance
   - The new metric provides a fairer assessment

2. **Re-evaluate your models**
   - Run predictions again with the fixed code
   - You should see accuracy scores that better reflect reality
   - Expect scores in the 50-70% range if correct codes are in top-k predictions

3. **Consider the other metrics too**
   - **Precision**: Shows how many of your predictions are correct
   - **Recall**: Shows how many ground truth codes you found
   - **F1**: Harmonic mean of precision and recall (more conservative)
   - **Accuracy**: Now the arithmetic mean of precision and recall (balanced)

## Backward Compatibility Note

⚠️ **Breaking Change**: Existing accuracy scores will change when recalculated. However:
- This makes the metric more accurate and fair
- Other metrics (precision, recall, F1) are unchanged
- The change primarily benefits scenarios with imbalanced prediction/truth counts

## Security

- No security vulnerabilities introduced
- CodeQL scan: 0 alerts ✅
- All changes are in metric calculation logic only

## Next Steps

1. ✅ Fix implemented and tested
2. ✅ Documentation created
3. ✅ Example scripts provided
4. ✅ Security verified
5. **Recommended**: Re-run your PST predictions with the fixed code
6. **Recommended**: Compare new accuracy scores with precision/recall/F1

## Questions?

If you need further clarification or encounter any issues:
- Review `ACCURACY_FIX_DOCUMENTATION.md` for detailed explanation
- Run `example_accuracy_evaluation.py` to see the metric in action
- Check the test cases in `tests/test_accuracy_metric.py` for expected behavior

---

**Fix Author**: GitHub Copilot Agent  
**Date**: November 2025  
**PR**: copilot/debug-finetuned-models-accuracy
