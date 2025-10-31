# Multi-GPU Training Guide

This repository now supports multi-GPU training using PyTorch's Distributed Data Parallel (DDP).

## Requirements

- PyTorch with CUDA support
- Multiple GPUs available on your system
- NCCL backend (included with PyTorch CUDA builds)

## Single GPU Training (Default)

To train on a single GPU, simply run the training scripts as before:

```bash
python finetune.py --dataset path/to/data.csv --target-cols col1 col2 --save-path ./output
```

```bash
python train_mixer.py --train-data path/to/train.csv --val-data path/to/val.csv --save-dir ./output
```

## Multi-GPU Training

### Using torch.distributed.launch (PyTorch < 2.0)

For PyTorch versions before 2.0, use `torch.distributed.launch`:

```bash
python -m torch.distributed.launch \
    --nproc_per_node=4 \
    finetune.py \
    --distributed \
    --dataset path/to/data.csv \
    --target-cols col1 col2 \
    --save-path ./output \
    --batch-size 128
```

### Using torchrun (PyTorch >= 2.0, Recommended)

For PyTorch 2.0 and later, use `torchrun`:

```bash
torchrun --nproc_per_node=4 \
    finetune.py \
    --distributed \
    --dataset path/to/data.csv \
    --target-cols col1 col2 \
    --save-path ./output \
    --batch-size 128
```

### Example with train_mixer.py

```bash
torchrun --nproc_per_node=4 \
    train_mixer.py \
    --distributed \
    --train-data path/to/train1.csv path/to/train2.csv \
    --val-data path/to/val.csv \
    --save-dir ./output \
    --batch-size 512 \
    --formatter hisco
```

## Important Notes

1. **Batch Size**: When using multiple GPUs, the effective batch size is `batch_size * num_gpus`. You may want to adjust your batch size accordingly.

2. **Gradient Accumulation**: The effective global batch size across all GPUs is the batch size per GPU multiplied by the number of GPUs.

3. **Saving and Loading**: Model checkpoints are saved only from the main process (rank 0) to avoid conflicts. The saved model is the unwrapped model (without DDP wrapper).

4. **Logging**: Logs and W&B metrics are only recorded from the main process to avoid duplicate logs.

5. **Data Distribution**: The data is automatically distributed across GPUs using DistributedSampler, ensuring each GPU processes different batches.

## Multi-Node Multi-GPU Training

For training across multiple nodes, use the following with torchrun:

```bash
# On node 0 (master node):
torchrun \
    --nproc_per_node=4 \
    --nnodes=2 \
    --node_rank=0 \
    --master_addr=<master_node_ip> \
    --master_port=29500 \
    finetune.py \
    --distributed \
    --dataset path/to/data.csv \
    --target-cols col1 col2 \
    --save-path ./output

# On node 1:
torchrun \
    --nproc_per_node=4 \
    --nnodes=2 \
    --node_rank=1 \
    --master_addr=<master_node_ip> \
    --master_port=29500 \
    finetune.py \
    --distributed \
    --dataset path/to/data.csv \
    --target-cols col1 col2 \
    --save-path ./output
```

## Troubleshooting

### NCCL Errors
If you encounter NCCL errors, ensure that:
- All GPUs are visible and functioning properly
- Your CUDA and NCCL versions are compatible
- Network connectivity between nodes is stable (for multi-node training)

### Different Results Between Single and Multi-GPU
This can happen due to:
- Batch normalization layers (not used in this codebase)
- Different random seeds across processes
- Ensure you're using the same total effective batch size for fair comparison

### Out of Memory
If you run out of memory with multi-GPU training:
- Reduce the batch size per GPU
- The total effective batch size will still be larger than single GPU training
