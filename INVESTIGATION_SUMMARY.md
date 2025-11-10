# Investigation: Multiple Predictions and Low Confidence Issue

## User's Report

After training a PST2 model, the user reports:
1. **Missing multiple predictions**: Most rows have `pst_2=nan` instead of predicting a second occupation
2. **Extremely low confidence scores**: Values like 0.017, 0.002, 0.0005, etc.
3. **Training metrics show issues**:
   - `seq_acc` only reaches 0.268 (should be much higher)
   - `token_acc` is ~91% (reasonable)

## My Fix (Commit c984e5b)

### What I Fixed
1. **Column generation**: Changed `max_elements` from batch-dependent to `formatter.max_num_codes`
   - **Result**: All 4 columns (pst_1, pst_2, pst_3, pst_4) are now always created
   - **Status**: ✅ Working correctly

2. **Confidence calculation**: Changed from product to geometric mean
   - **Result**: Confidence = (product of probs)^(1/n) instead of just product
   - **Status**: ✅ Working correctly (but doesn't help if underlying probs are low)

### What My Fix Does NOT Address

My fix ensures **OUTPUT FORMATTING** is consistent, but it cannot fix:
1. **Model not predicting multiple occupations** - The model outputs single blocks without "&" separators
2. **Low token probabilities** - The model assigns ~1-2% probability per token

## Root Cause Analysis

### Issue 1: Missing Multiple Predictions

The model is **not learning to predict multiple occupation blocks**. Evidence:
- Most predictions have no "&" separator in the `pred_s2s` output
- This results in `pst_2=nan` after formatting
- A few predictions have `pst_2="0"` (Unknown code), showing the model CAN predict 2 blocks but rarely does

**Possible causes:**
1. Training data may not have multiple occupations with "&" separator
2. Model architecture or loss function doesn't encourage multiple block predictions
3. Training hyperparameters (learning rate, warmup, etc.) may be suboptimal
4. Formatter configuration for PST2 may be incorrect

### Issue 2: Low Confidence Scores

Confidence scores of 0.017 (1.7%) indicate:
- With geometric mean: Each token has ~1.7% probability
- This is a **model quality issue**, not a calculation issue

**The model is genuinely uncertain** about its predictions. Evidence:
- `seq_acc` = 0.268 (only 26.8% of sequences are completely correct)
- Low token probabilities result in low confidence

## What Needs Investigation

1. **Training Data Format**:
   ```bash
   # Check if training data has examples like:
   # input: "labourer and builder"
   # output: "1,2,3,4,5,0,0,0&2,3,4,5,0,0,0,0"
   ```

2. **Formatter Configuration**:
   - Is `use_within_block_sep=True` set correctly?
   - Are `target_cols` set to `['pst_1', 'pst_2', 'pst_3', 'pst_4']`?
   - Is `sep_value='&'` set correctly?

3. **Model Architecture**:
   - Which model is being used? (seq2seq, mix, or flat?)
   - Is the architecture appropriate for multiple block predictions?

4. **Training Command**:
   - What are the training parameters?
   - Is the loss function configured correctly?

5. **Comparison with "Earlier Versions"**:
   - What changed between the working version and current version?
   - Was there a code change, data change, or hyperparameter change?

## Recommendations

1. **Verify training data**:
   ```python
   # Check a sample of training data
   import pandas as pd
   df = pd.read_parquet('path/to/training/data.parquet')
   # Look for examples with multiple occupations
   print(df[df['pst_1'].notna() & df['pst_2'].notna()].head())
   ```

2. **Check formatter configuration**:
   ```python
   from histocc.formatter import construct_general_purpose_formatter
   formatter = construct_general_purpose_formatter(
       block_size=8,
       target_cols=['pst_1', 'pst_2', 'pst_3', 'pst_4'],
       use_within_block_sep=True
   )
   print(formatter)
   ```

3. **Increase training duration**:
   - The model may need more training steps to learn multiple blocks
   - Consider training for 2000+ steps instead of 800

4. **Adjust learning rate/warmup**:
   - Current metrics suggest the model may be converging too quickly
   - Try increasing warmup percentage or decreasing learning rate

5. **Review loss function**:
   - Ensure `BlockOrderInvariantLoss` is configured correctly
   - Check that it's encouraging multiple block predictions

## Conclusion

**My fix is correct** for ensuring consistent output schema, but the core issue is that the **model is not learning to predict multiple occupations**. This requires investigation of:
- Training data format
- Model architecture
- Training hyperparameters
- Loss function configuration

The user needs to provide more information about their training setup to diagnose further.
