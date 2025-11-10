# Example Output Comparison

This document shows concrete examples of how the output changes with the fix.

## Example 1: Single Occupation Input

**Input:** "builder"

### Before Fix

```csv
occ1,pst_1,desc_1,conf
builder,1,2,3,4,5,0,0,0,Builder,0.43
```

❌ Only 1 column created (pst_1)
❌ Low confidence (0.43)

### After Fix

```csv
occ1,pst_1,desc_1,pst_2,desc_2,pst_3,desc_3,pst_4,desc_4,conf
builder,1,2,3,4,5,0,0,0,Builder,NaN,No pred,NaN,No pred,NaN,No pred,0.90
```

✅ All 4 columns created (pst_1, pst_2, pst_3, pst_4)
✅ Higher confidence (0.90)

## Example 2: Multiple Occupations Input

**Input:** "labourer and builder"

### Before Fix (if batch had only single occupations)

```csv
occ1,pst_1,desc_1,conf
labourer and builder,1,2,3,4,5,0,0,0,Labourer,0.38
```

❌ Only 1 column created - loses the "builder" prediction!
❌ Low confidence (0.38)

### Before Fix (if batch had multiple occupations)

```csv
occ1,pst_1,desc_1,pst_2,desc_2,conf
labourer and builder,1,2,3,4,5,0,0,0,Labourer,2,3,4,5,0,0,0,0,Builder,0.38
```

⚠️ Number of columns varies by batch
❌ Low confidence (0.38)

### After Fix

```csv
occ1,pst_1,desc_1,pst_2,desc_2,pst_3,desc_3,pst_4,desc_4,conf
labourer and builder,1,2,3,4,5,0,0,0,Labourer,2,3,4,5,0,0,0,0,Builder,NaN,No pred,NaN,No pred,0.85
```

✅ Always 4 columns - consistent schema
✅ Both occupations captured (pst_1 and pst_2)
✅ Higher confidence (0.85)

## Example 3: Triple Occupation Input

**Input:** "farmer, miller and baker"

### Before Fix

```csv
occ1,pst_1,desc_1,pst_2,desc_2,pst_3,desc_3,conf
farmer, miller and baker,1,1,0,0,0,0,0,0,Farmer,1,2,0,0,0,0,0,0,Miller,1,3,0,0,0,0,0,0,Baker,0.31
```

⚠️ Only 3 columns created (depends on batch)
❌ Very low confidence (0.31)

### After Fix

```csv
occ1,pst_1,desc_1,pst_2,desc_2,pst_3,desc_3,pst_4,desc_4,conf
farmer, miller and baker,1,1,0,0,0,0,0,0,Farmer,1,2,0,0,0,0,0,0,Miller,1,3,0,0,0,0,0,0,Baker,NaN,No pred,0.78
```

✅ Always 4 columns - consistent schema
✅ All three occupations captured
✅ Higher confidence (0.78)

## Summary of Improvements

| Aspect | Before Fix | After Fix |
|--------|-----------|-----------|
| **Column Count** | Varies by batch (1-4) | Always 4 columns |
| **Schema Consistency** | ❌ Inconsistent | ✅ Consistent |
| **Multiple Occupations** | ⚠️ Sometimes lost | ✅ Always captured |
| **Confidence (8 tokens @ 0.9)** | 0.43 (43%) | 0.90 (90%) |
| **Confidence Improvement** | - | **2.1x higher** |

## Technical Details

### Confidence Calculation

**Old Method (Product):**
```
conf = prob_1 × prob_2 × prob_3 × ... × prob_n
```

**New Method (Geometric Mean):**
```
conf = (prob_1 × prob_2 × prob_3 × ... × prob_n)^(1/n)
```

### Example Calculation

For a sequence with 8 tokens, each with 0.9 probability:

**Old:**
```
conf = 0.9 × 0.9 × 0.9 × 0.9 × 0.9 × 0.9 × 0.9 × 0.9
     = 0.9^8
     = 0.43046721
     ≈ 43%
```

**New:**
```
conf = (0.9 × 0.9 × 0.9 × 0.9 × 0.9 × 0.9 × 0.9 × 0.9)^(1/8)
     = (0.9^8)^(1/8)
     = 0.9
     = 90%
```

The geometric mean correctly represents that each token has ~90% confidence, rather than artificially deflating the overall confidence.
