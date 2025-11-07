# Warmup and TF32 Configuration Changes

## Summary
This update changes the warmup configuration from a fixed number of steps to a percentage of total training steps, and ensures TF32 matmul precision is enabled for improved performance on Ampere GPUs.

## Changes Made

### 1. Dynamic Warmup Steps (3-10% of total steps)

**Previous Behavior:**
- Warmup steps were configured as a fixed number via `--warmup-steps` argument
- Most scripts defaulted to 0 (no warmup) or 500 steps

**New Behavior:**
- Warmup is now configured as a percentage of total training steps via `--warmup-pct` argument
- Default is 0.05 (5% of total steps), which falls in the recommended 3-10% range
- Calculation: `num_warmup_steps = int(total_steps * warmup_pct)`

**Files Modified:**
- `train.py` - Changed `--warmup-steps` to `--warmup-pct` (default: 0.05)
- `train_mixer.py` - Changed `--warmup-steps` to `--warmup-pct` (default: 0.05)
- `train_v2.py` - Changed `--warmup-steps` to `--warmup-pct` (default: 0.05)
- `finetune.py` - Changed `--warmup-steps` to `--warmup-pct` (default: 0.05)
- `finetune_with_wrapper.py` - Updated to pass `warmup_pct` instead of `warmup_steps`
- `histocc/prediction_assets.py` - Updated `finetune()` method to use `warmup_pct` parameter (default: 0.05)
- `histocc/seq2seq_wrapper.py` - Hardcoded 5% warmup (0.05 * total_steps)

**Example Usage:**
```bash
# Use default 5% warmup
python train_mixer.py --save-dir ./models --train-data data.csv --val-data val.csv

# Use 3% warmup
python train_mixer.py --warmup-pct 0.03 --save-dir ./models --train-data data.csv --val-data val.csv

# Use 10% warmup
python finetune.py --warmup-pct 0.10 --dataset data.csv --save-path ./finetuned
```

### 2. TF32 Matmul Precision

**New Feature:**
- Enabled TF32 (TensorFloat-32) precision for matrix multiplication operations
- Provides significant speedup on NVIDIA Ampere (A100, RTX 30xx) and newer GPUs
- Maintains nearly the same accuracy as FP32 while being much faster

**Implementation:**
Added to all training scripts:
```python
if torch.cuda.is_available():
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True
```

**Files Modified:**
- `train.py` - Added TF32 support
- `train_mixer.py` - Added TF32 support
- `train_v2.py` - Added TF32 support
- `finetune.py` - Enhanced existing TF32 support
- `histocc/prediction_assets.py` - Added TF32 support to `finetune()` method
- `histocc/seq2seq_wrapper.py` - Added TF32 support to `_train_model()` method

**Note:** TF32 is automatically disabled on GPUs that don't support it (pre-Ampere), so this change is safe for all hardware.

## Benefits

1. **Adaptive Warmup**: Warmup duration now scales with training length
   - Short training runs get proportionally shorter warmup
   - Long training runs get proportionally longer warmup
   - More robust across different dataset sizes and epoch counts

2. **Improved Performance**: TF32 can provide 2-4x speedup on compatible hardware
   - Faster training times
   - Lower training costs
   - No significant loss in model quality

## Backward Compatibility

The old `--warmup-steps` argument has been replaced with `--warmup-pct`. Users will need to update their training scripts:

**Old:**
```bash
python train_mixer.py --warmup-steps 500 ...
```

**New:**
```bash
# For equivalent warmup (if total_steps = 10000):
python train_mixer.py --warmup-pct 0.05 ...
```

## Testing

A comprehensive test suite has been added in `tests/test_warmup_pct.py` that verifies:
- All training scripts use `--warmup-pct` instead of `--warmup-steps`
- Default warmup percentage is 0.05 (5%)
- Warmup steps are calculated correctly as `int(total_steps * warmup_pct)`
- TF32 is enabled in all training scripts

Run tests with:
```bash
python -m unittest tests.test_warmup_pct -v
```
