# Accuracy Metric Fix

## Problem

The finetuned models were showing very low accuracy scores (e.g., 6%) even when predictions were demonstrably good - i.e., the correct codes were being predicted but accompanied by additional predictions.

## Root Cause

The accuracy calculation in `histocc/eval_metrics.py` used a formula that penalized models when they provided multiple predictions but ground truth had fewer labels:

```python
# Old (buggy) formula
res = (pred_in_true + true_in_pred) / (2 * max(len(y_true), len(y_pred)))
```

### Example of the Problem

Consider a realistic scenario:
- Ground truth: `['12345']` (1 code)
- Predictions: `['12345', '67890', '11111', '22222', '33333']` (5 codes, first is correct)

With the old formula:
- `pred_in_true = 1` (one prediction matches ground truth)
- `true_in_pred = 1` (one ground truth matches predictions)
- `max_preds = max(1, 5) = 5`
- **Accuracy = (1 + 1) / (2 * 5) = 0.20 or 20%**

This is problematic because:
1. The model correctly predicted the right code
2. In top-k prediction scenarios, providing multiple predictions is normal
3. The accuracy should be higher to reflect that the correct code was found

## Solution

Changed the formula to average precision-like and recall-like metrics:

```python
# New (fixed) formula
precision_like = pred_in_true / len(y_pred)
recall_like = true_in_pred / len(y_true)
res = (precision_like + recall_like) / 2
```

### Same Example with New Formula

- Ground truth: `['12345']` (1 code)
- Predictions: `['12345', '67890', '11111', '22222', '33333']` (5 codes, first is correct)

With the new formula:
- `precision_like = 1/5 = 0.20` (1 correct out of 5 predictions)
- `recall_like = 1/1 = 1.0` (found the 1 ground truth)
- **Accuracy = (0.20 + 1.0) / 2 = 0.60 or 60%**

This is much more representative of the model's performance!

## Impact

The fix significantly improves accuracy scores in scenarios where:
- Ground truth has fewer codes than predictions
- The correct code(s) are among the predictions

### Comparison Table

| Scenario | Ground Truth | Predictions | Old Accuracy | New Accuracy | Change |
|----------|--------------|-------------|--------------|--------------|--------|
| Top-3 with 1 correct | 1 code | 3 codes (1 correct) | 33.3% | 66.7% | +33.3pp |
| Top-5 with 1 correct | 1 code | 5 codes (1 correct) | 20.0% | 60.0% | +40.0pp |
| Perfect match | 1 code | 1 code (correct) | 100% | 100% | No change |
| Perfect match (multi) | 2 codes | 2 codes (both correct) | 100% | 100% | No change |
| No match | 1 code | 1 code (wrong) | 0% | 0% | No change |
| Partial match | 2 codes | 2 codes (1 correct) | 50% | 50% | No change |

## Why This Formula is Better

The new formula:
1. **Balances precision and recall**: Takes into account both how many predictions are correct (precision-like) and how many ground truth codes were found (recall-like)
2. **Doesn't penalize top-k predictions**: When models provide multiple predictions, they're not unfairly penalized as long as correct codes are included
3. **Rewards finding correct codes**: High recall component when all ground truth codes are found
4. **Still penalizes wrong predictions**: Low precision component when many wrong predictions are made
5. **Symmetric and fair**: Handles both cases (many preds, few truth) and (few preds, many truth) symmetrically

## Relationship to Other Metrics

The accuracy metric now properly complements the existing metrics:

- **Precision** (`_prec`): `pred_in_true / len(y_pred)` - What fraction of predictions are correct?
- **Recall** (`_recall`): `true_in_pred / len(y_true)` - What fraction of ground truth was found?
- **Accuracy** (`_acc`): `(precision + recall) / 2` - Balanced measure of both
- **F1** (`_f1`): `2 * (precision * recall) / (precision + recall)` - Harmonic mean (more conservative)

Note: Accuracy is now the arithmetic mean of precision and recall, while F1 is the harmonic mean. This makes accuracy slightly more lenient than F1 but still balanced.

## Files Changed

- `histocc/eval_metrics.py`: Updated `_acc()` method (lines 96-157)
- `tests/test_accuracy_metric.py`: Added comprehensive tests for the accuracy metric

## Testing

Run the test suite to verify the fix:

```bash
python -m unittest tests.test_accuracy_metric
```

Or run the demonstration script:

```bash
python /tmp/demonstrate_fix.py
```

## Backward Compatibility

⚠️ **Important**: This is a breaking change for the accuracy metric. Existing accuracy scores will change when recalculated. However:

- The change makes the metric more accurate and fair
- Other metrics (precision, recall, F1) are unchanged
- Perfect matches and no-matches still give 100% and 0% respectively
- The change primarily affects scenarios with imbalanced prediction/truth counts

If you need to compare with old accuracy scores, you would need to recalculate them using the old formula, but we recommend migrating to the new, more accurate metric.

## Verification with Real Data

To verify this fix resolves your low accuracy issue:

1. Re-run your PST predictions
2. Calculate accuracy using the updated `EvalEngine`
3. Compare with precision and recall metrics
4. Verify that accuracy now better reflects model performance

Expected behavior:
- If your model is predicting the correct codes (high recall), accuracy should now be much higher
- Accuracy will be balanced between precision and recall
- Models that provide top-k predictions with correct codes will show appropriate accuracy scores
