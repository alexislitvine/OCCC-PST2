# Multi-GPU Training Support

OccCANINE now supports automatic multi-GPU training for faster model training and fine-tuning.

## Features

- **Automatic Detection**: The code automatically detects available GPUs and enables multi-GPU training when 2 or more GPUs are present.
- **Backward Compatible**: Single GPU and CPU training continue to work exactly as before.
- **Zero Configuration**: No code changes or additional parameters are required - it works out of the box!
- **Supported Scripts**: 
  - `FINETUNE_MODEL.py` - Fine-tuning with the OccCANINE class
  - `train.py` - Main training script

## How It Works

When you run training or fine-tuning scripts, the code will:

1. Detect the number of available CUDA GPUs
2. If 2+ GPUs are available, wrap the model with `torch.nn.DataParallel`
3. Distribute batches across all available GPUs automatically
4. Print a message indicating how many GPUs are being used

## Usage

### Fine-tuning (FINETUNE_MODEL.py)

Simply run the script as you normally would:

```python
from histocc import OccCANINE
import pandas as pd

model = OccCANINE()
df = pd.read_csv("histocc/Data/TOYDATA.csv", nrows=1000)
df["lang"] = "en"

model.finetune(
    df, 
    ["hisco_1"], 
    batch_size=32, 
    save_name="Finetuned_toy_model"
)
```

If multiple GPUs are available, you'll see output like:
```
Using 4 GPUs for training
```

### Training from Scratch (train.py)

Run the training script normally:

```bash
python train.py --checkpoint-path path/to/checkpoint/ --batch-size 256 --epochs 50
```

The script will automatically use all available GPUs.

## Requirements

- PyTorch with CUDA support
- Multiple NVIDIA GPUs
- Properly configured CUDA drivers

## Performance Considerations

- **Batch Size**: When using multiple GPUs, you may want to increase the batch size proportionally. For example, if you used `batch_size=32` on 1 GPU, try `batch_size=128` on 4 GPUs.
- **Memory**: Each GPU will load a copy of the model, so ensure each GPU has enough memory.
- **Data Loading**: The data loading may become a bottleneck with multiple GPUs. Consider increasing the number of data loader workers if needed.

## Technical Details

The implementation uses `torch.nn.DataParallel`, which:
- Replicates the model on each GPU
- Splits each batch across the GPUs
- Gathers the results and combines gradients
- Is ideal for single-node, multi-GPU training

For distributed training across multiple nodes, consider using `torch.nn.parallel.DistributedDataParallel` (not currently implemented).

## Troubleshooting

### Not Using All GPUs

If you want to restrict training to specific GPUs, set the `CUDA_VISIBLE_DEVICES` environment variable:

```bash
# Use only GPU 0 and 1
export CUDA_VISIBLE_DEVICES=0,1
python FINETUNE_MODEL.py
```

### Out of Memory Errors

If you encounter out-of-memory errors:
1. Reduce the batch size
2. Ensure each GPU has enough free memory
3. Check that you're not running other GPU-intensive processes

### Checking GPU Usage

Monitor GPU usage during training:
```bash
watch -n 1 nvidia-smi
```

You should see the model loaded on all GPUs and utilization across all devices.
