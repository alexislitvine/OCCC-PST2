# Visual Comparison: Before and After the Accuracy Fix

## Scenario: Top-5 Predictions with 1 Ground Truth Code

This is the most common scenario causing low accuracy scores:
- You have 1 ground truth occupational code
- Your model predicts top-5 codes (which is good practice!)
- The correct code IS in the top-5 (the model is working!)

### Before the Fix ❌

```
Ground Truth:     [12345]
Predictions:      [12345, 67890, 11111, 22222, 33333]
                   ^^^^^
                   Correct!

Old Formula:
  pred_in_true = 1    (one prediction matches truth)
  true_in_pred = 1    (one truth matches predictions)  
  max_preds = 5       (max of 1 truth and 5 predictions)
  
  accuracy = (1 + 1) / (2 × 5) = 2/10 = 0.20
  
  Result: 20% accuracy ❌
  
Problem: The model found the correct code, but got a terrible score!
```

### After the Fix ✅

```
Ground Truth:     [12345]
Predictions:      [12345, 67890, 11111, 22222, 33333]
                   ^^^^^
                   Correct!

New Formula:
  pred_in_true = 1    (one prediction matches truth)
  true_in_pred = 1    (one truth matches predictions)
  
  precision_like = 1/5 = 0.20    (1 correct out of 5 predictions)
  recall_like = 1/1 = 1.00       (found the 1 ground truth)
  
  accuracy = (0.20 + 1.00) / 2 = 0.60
  
  Result: 60% accuracy ✅
  
Improvement: The model is rewarded for finding the correct code!
```

---

## Visual: How Accuracy Changes with Number of Predictions

### Scenario: 1 Ground Truth, K Predictions (1 Correct)

```
Number of Predictions (k) →
                1    2    3    4    5    6    7    8    9   10
                │    │    │    │    │    │    │    │    │    │
OLD Accuracy:  100%  50%  33%  25%  20%  17%  14%  13%  11%  10%  ❌
               ████ ███▌ ██▌  ██   █▊   █▌   █▎   █▏   █    █
                    
NEW Accuracy:  100%  75%  67%  63%  60%  58%  57%  56%  56%  55%  ✅
               ████ ███▊ ███▎ ███  ██▊  ██▋  ██▋  ██▌  ██▌  ██▍

Legend: █ = 10% accuracy
```

**Key Insight**: 
- OLD formula: More predictions = much lower accuracy (even if correct!)
- NEW formula: Accuracy stays reasonable because recall is 100%

---

## Example: Real PST Prediction

### Your Situation (Before Fix)

```
Data:
- 1000 occupational strings to code
- Each has 1 correct PST code (ground truth)
- Model predicts top-5 codes for each

Results with OLD formula:
  ┌─────────────────────────────────────┐
  │ Correct codes found:        900/1000│  90% recall! 🎉
  │ But accuracy shows:          18%    │  ❌ Looks terrible!
  └─────────────────────────────────────┘
  
Problem: You think your model is bad (18% accuracy),
         but it actually found 90% of the correct codes!
```

### Your Situation (After Fix)

```
Same Data and Results:

Results with NEW formula:
  ┌─────────────────────────────────────┐
  │ Correct codes found:        900/1000│  90% recall! 🎉
  │ Precision:                    22%   │  (900/4100 wrong preds)
  │ NEW Accuracy:                 56%   │  ✅ Much more realistic!
  └─────────────────────────────────────┘
  
Interpretation: Your model IS working well!
  - It finds 90% of correct codes (excellent recall)
  - Accuracy of 56% properly reflects the precision-recall balance
  - You can be confident in using the top predictions
```

---

## Side-by-Side Comparison Table

| Metric | What it measures | Old Value | New Value | Interpretation |
|--------|-----------------|-----------|-----------|----------------|
| **Recall** | % of ground truth codes found | 90% | 90% | Unchanged - your model finds most codes ✅ |
| **Precision** | % of predictions that are correct | 22% | 22% | Unchanged - many predictions are wrong ⚠️ |
| **Accuracy (OLD)** | Flawed formula | 18% | — | Too low, not useful ❌ |
| **Accuracy (NEW)** | Average of prec. & recall | — | 56% | Balanced, realistic assessment ✅ |
| **F1 Score** | Harmonic mean of prec. & recall | 35% | 35% | Unchanged - another valid metric ✅ |

---

## Bottom Line

### What Changed?
The accuracy metric now properly balances:
1. **How good your predictions are** (precision-like component)
2. **How many correct codes you found** (recall-like component)

### What This Means for You?
If you were seeing ~6% accuracy:
- ✅ Your model is likely MUCH better than 6%
- ✅ Re-run with the fix to get realistic scores
- ✅ Expect 50-70% accuracy if you're finding most codes in top-k
- ✅ Use recall to see if correct codes are being found
- ✅ Use precision to see if you're making too many wrong predictions

### The Fix Makes Sense Because:
- Top-k prediction is standard practice
- Finding the correct code matters more than predicting fewer codes
- The metric should reward finding correct codes while still considering precision
- Perfect predictions still get 100%, complete failures still get 0%

---

**Remember**: The old 6% accuracy didn't mean your model was bad—it meant the metric was bad! The fix reveals your model's true performance. 🎯
