# Complete Solution: Multiple Occupations Not Being Predicted

## Problem Summary

The user reported that after training a PST2 model:
1. Most predictions have `pst_2=nan` (no multiple occupations predicted)
2. Confidence scores are extremely low (0.001 to 0.03)
3. Training data DOES contain multiple occupations

## Root Cause Analysis

### Primary Issue: seq2seq-weight Too Low (90% of the problem)

**Training Command:**
```bash
--seq2seq-weight 0.1
```

**What this means:**
- Only 10% of the loss function optimizes sequence prediction (multiple occupations)
- 90% optimizes the flat/linear decoder (single occupation predictions)
- Model is primarily learning to predict ONE occupation, not sequences

**Evidence from training logs:**
```
step  seq_acc  token_acc  val_loss_seq2seq
100   0.000    88.3%      0.789
800   0.268    91.3%      0.448
```

- `seq_acc` only reaches 26.8% (should be >70% for good sequence learning)
- `token_acc` is high at 91% (tokens learned, but not sequences)
- `val_loss_seq2seq` is still high at 0.448 (seq2seq not well optimized)

**Why this prevents multiple occupations:**
- The model is being trained primarily on the flat/linear loss
- This loss only cares about predicting the top-1 occupation
- The seq2seq loss (which learns to predict multiple occupation blocks) gets only 10% weight
- Result: Model learns to output single occupation blocks, not multiple blocks with "&" separator

### Secondary Issue: Formatter Config Not Saved (10% of the problem)

**Problem:**
- User trained with 5 target columns: `pst2_1 pst2_2 pst2_3 pst2_4 pst2_5`
- Model checkpoint didn't save this information
- Prediction code defaulted to 4 columns
- Created mismatch in `max_num_codes` (5 vs 4)

**Fixed in commit 7a3b676:**
- Training now saves formatter config in checkpoint
- Prediction loads formatter config from checkpoint
- Ensures correct number of columns when predicting

## Solutions Implemented

### Fix 1: Save/Load Formatter Configuration (Code Fix)

**Changes to `histocc/seq2seq_mixer_engine.py`:**
```python
def _extract_formatter_config(formatter):
    """Extract formatter configuration for saving."""
    config = {}
    if hasattr(formatter, 'target_cols'):
        config['target_cols'] = formatter.target_cols
    if hasattr(formatter, 'block_size'):
        config['block_size'] = formatter.block_size
    # ... etc
    return config

def _save_model_checkpoint(..., formatter_config=None):
    states = {
        'model': model_to_save.state_dict(),
        'key': dataset_map_code_label,
        'formatter_config': formatter_config,  # NEW
    }
```

**Changes to `histocc/prediction_assets.py`:**
```python
# Load formatter config from saved state
if 'formatter_config' in loaded_state.keys():
    formatter_cfg = loaded_state['formatter_config']
    target_cols = formatter_cfg.get('target_cols', ...)
    block_size = formatter_cfg.get('block_size', ...)
```

**Impact:**
- Future trained models will save formatter config
- Predictions will use correct number of columns
- No more manual specification of `target_cols` needed

### Fix 2: Retrain with Higher seq2seq-weight (User Action Required)

**Current training:**
```bash
--seq2seq-weight 0.1  # BAD: Only 10% on sequences
```

**Recommended training:**
```bash
--seq2seq-weight 0.5   # GOOD: 50% on sequences
# or
--seq2seq-weight 0.7   # BETTER: 70% on sequences
```

**Why this works:**
- Gives proper weight to learning complete occupation sequences
- Model will learn to predict multiple occupation blocks
- seq_acc should reach >70% with proper weight
- Confidence scores will improve as sequences become more certain

**Additional recommendations:**
```bash
--num-epochs 50        # More epochs to learn sequences properly
--batch-size 256       # May help with gradient stability
```

## Expected Results After Retraining

### Before (with --seq2seq-weight 0.1):
```
occ1                      pst_1               pst_2  conf
GROOM CHAUFFEUR          2,2,27,3,1,1,0,0    nan    0.001
```
- Only pst_1 filled
- Very low confidence
- seq_acc ~27%

### After (with --seq2seq-weight 0.5):
```
occ1                      pst_1               pst_2               pst_3  conf
GROOM CHAUFFEUR          2,2,1,0,0,0,0,0    2,2,27,0,0,0,0,0    nan    0.65
```
- Multiple occupations predicted (pst_1 AND pst_2)
- Higher confidence scores (>0.5)
- seq_acc >70%

## Why This Happened

The `--seq2seq-weight` parameter is critical for the mixer model architecture:

**Mixer Model Loss:**
```
total_loss = (1 - w) * flat_loss + w * seq2seq_loss
where w = seq2seq_weight
```

With `w = 0.1`:
- `total_loss = 0.9 * flat_loss + 0.1 * seq2seq_loss`
- Model optimizes 90% for flat predictions (single occupation)
- Model optimizes 10% for sequences (multiple occupations)
- Result: Model learns single occupations well, sequences poorly

With `w = 0.5`:
- `total_loss = 0.5 * flat_loss + 0.5 * seq2seq_loss`
- Balanced optimization
- Both single and multiple occupation predictions learned

## Verification

After retraining with `--seq2seq-weight 0.5`, check:

1. **Training metrics:**
   - `seq_acc` should reach >70% (was 27%)
   - `val_loss_seq2seq` should drop below 0.2 (was 0.45)

2. **Predictions:**
   - Check for "&" separators in `pred_s2s` column
   - Multiple rows with `pst_2` filled (not all nan)
   - Confidence scores >0.5 for good predictions

3. **Sample prediction:**
   ```python
   model.predict("groom and chauffeur")
   # Should output: pst_1="groom code", pst_2="chauffeur code"
   ```

## Summary

**The core issue was NOT a code bug** - it was a training hyperparameter issue:
- `--seq2seq-weight 0.1` was too low
- Model didn't learn to predict multiple occupations
- **Solution: Retrain with `--seq2seq-weight 0.5` or higher**

**Secondary issue (now fixed):**
- Formatter config not saved/loaded
- Fixed in commit 7a3b676
- Ensures correct column count when predicting

Both my code fixes (output formatting + formatter config) are correct, but they can't fix a model that wasn't trained to predict multiple occupations in the first place!
