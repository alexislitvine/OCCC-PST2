# Learning Statistics Logging

## Overview
This document describes the logging functionality implemented to save training statistics for later analysis and plotting.

## Implementation

### CSV Logging in trainer.py (Legacy Training Loop)

**Function:** `save_history_to_csv(history, model_name)`

**Location:** `histocc/trainer.py`

**Purpose:** Saves training history to CSV files for later analysis and plotting.

**Output Files:** `../Tmp training plots/{model_name}_history.csv`

**CSV Columns:**
- `epoch`: Epoch number (1-indexed)
- `train_loss`: Training loss for the epoch
- `train_acc`: Training accuracy for the epoch
- `val_loss`: Validation loss for the epoch
- `val_acc`: Validation accuracy for the epoch

**Integration:**
- Called automatically after each evaluation in `run_eval()` and `run_eval_simple()`
- Creates CSV files alongside existing plot images

### CSV Logging in Modern Training Engines

**Files:** `histocc/seq2seq_engine.py`, `histocc/seq2seq_mixer_engine.py`

**Function:** `update_summary(step, metrics, filename, log_wandb=False)`

**Location:** `histocc/utils/log_util.py`

**Purpose:** Logs detailed training metrics at configurable intervals during training.

**Output Files:** `{save_dir}/logs.csv`

**CSV Columns (seq2seq_engine.py):**
- `step`: Training step number
- `batch_time`: Average batch processing time
- `batch_time_data`: Average data loading time
- `train_loss`: Training loss
- `val_loss`: Validation loss
- `seq_acc`: Sequence accuracy
- `token_acc`: Token accuracy
- `lr`: Learning rate

**CSV Columns (seq2seq_mixer_engine.py):**
- All columns from seq2seq_engine.py, plus:
- `val_loss_linear`: Validation loss for linear decoder
- `val_loss_seq2seq`: Validation loss for seq2seq decoder
- `flat_acc`: Flat accuracy metric

**Integration:**
- Called automatically during training at `eval_interval` steps
- Supports optional Weights & Biases (wandb) logging

## Usage

### For Legacy Training (trainer.py)

The CSV logging happens automatically when using `trainer_loop()` or `trainer_loop_simple()`:

```python
from histocc import trainer_loop

model, history = trainer_loop(
    model=model,
    epochs=50,
    model_name='my_model',
    data=data,
    loss_fn=loss_fn,
    reference_loss=0.5,
    optimizer=optimizer,
    device=device,
    scheduler=scheduler,
)

# CSV file is automatically created at:
# ../Tmp training plots/my_model_history.csv
```

### For Modern Training (seq2seq engines)

The CSV logging happens automatically during training:

```python
from histocc.seq2seq_engine import train

train(
    model=model,
    data_loaders=data_loaders,
    loss_fn=loss_fn,
    optimizer=optimizer,
    device=device,
    scheduler=scheduler,
    save_dir='./checkpoints',
    total_steps=10000,
    eval_interval=1000,  # Log every 1000 steps
)

# CSV file is automatically created at:
# ./checkpoints/logs.csv
```

## Plotting from CSV Files

You can easily load and plot the logged data using pandas:

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load CSV data
df = pd.read_csv('../Tmp training plots/my_model_history.csv')

# Plot training and validation loss
plt.figure(figsize=(10, 6))
plt.plot(df['epoch'], df['train_loss'], label='Training Loss')
plt.plot(df['epoch'], df['val_loss'], label='Validation Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.title('Training Progress')
plt.legend()
plt.grid(True)
plt.savefig('training_progress.png')
```

For modern training engines:

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load CSV data
df = pd.read_csv('./checkpoints/logs.csv')

# Plot multiple metrics
fig, axes = plt.subplots(2, 2, figsize=(15, 10))

# Loss plot
axes[0, 0].plot(df['step'], df['train_loss'], label='Train')
axes[0, 0].plot(df['step'], df['val_loss'], label='Val')
axes[0, 0].set_title('Loss')
axes[0, 0].legend()

# Accuracy plot
axes[0, 1].plot(df['step'], df['seq_acc'], label='Seq Acc')
axes[0, 1].plot(df['step'], df['token_acc'], label='Token Acc')
axes[0, 1].set_title('Accuracy')
axes[0, 1].legend()

# Learning rate plot
axes[1, 0].plot(df['step'], df['lr'])
axes[1, 0].set_title('Learning Rate')

# Batch time plot
axes[1, 1].plot(df['step'], df['batch_time'])
axes[1, 1].set_title('Batch Time (seconds)')

plt.tight_layout()
plt.savefig('detailed_metrics.png')
```

## Testing

Tests are provided to verify the logging functionality:

```bash
# Test CSV logging in trainer.py
python tests/test_csv_logging.py

# Test overall training statistics
python tests/test_training_stats.py
```

## Benefits

1. **Persistence**: All training metrics are saved to disk for future analysis
2. **Reproducibility**: Easy to recreate plots and analyze training runs
3. **Comparison**: CSV format allows easy comparison of different training runs
4. **Flexibility**: Can create custom plots and analyses after training completes
5. **Integration**: Compatible with data science tools (pandas, numpy, matplotlib, etc.)
