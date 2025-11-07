# Converting CSV Data to Parquet for Faster Loading

## Overview

This guide explains how to convert your training and validation CSV files to Parquet format for significantly faster data loading during model training.

## Benefits of Parquet Format

Converting your CSV files to Parquet format provides several advantages:

- **2-10x faster data loading**: Binary columnar format is much faster to read than text-based CSV
- **50-80% smaller file sizes**: Built-in compression reduces storage requirements
- **Better type preservation**: No need for dtype converters
- **Reduced parsing overhead**: Workers spend less time parsing data, improving training throughput

## Quick Start

### Converting Training Data

```bash
# Convert all CSV files in Training_data directory
python convert_data_to_parquet.py --input-dir Data/Training_data/

# Convert to a different output directory
python convert_data_to_parquet.py \
    --input-dir Data/Training_data/ \
    --output-dir Data/Training_data_parquet/
```

### Converting Validation Data

```bash
# Convert validation data
python convert_data_to_parquet.py --input-dir Data/Validation_data/
```

### Converting a Single File

```bash
# Convert a specific CSV file
python convert_data_to_parquet.py --input path/to/data.csv

# Specify output path
python convert_data_to_parquet.py \
    --input path/to/data.csv \
    --output path/to/data.parquet
```

## Using Parquet Files for Training

Once you've converted your CSV files to Parquet, the dataloaders will automatically detect and use the Parquet format. Simply update your file paths to point to `.parquet` files instead of `.csv` files.

### Example: Training Script

If you have training files like:
- `Data/Training_data/en_train.parquet`
- `Data/Training_data/dk_train.parquet`

The existing training scripts will automatically use the Parquet format when you pass these paths:

```python
from histocc import OccDatasetV2InMemMultipleFiles

dataset = OccDatasetV2InMemMultipleFiles(
    fnames_data=[
        'Data/Training_data/en_train.parquet',  # .parquet instead of .csv
        'Data/Training_data/dk_train.parquet',
    ],
    # ... other parameters
)
```

## Data Format Support

The conversion script supports different data formats:

### HISCO Format (Default)
```bash
python convert_data_to_parquet.py --input-dir Data/Training_data/ --format hisco
```

Columns: `occ1`, `lang`, `code1`, `code2`, `code3`, `code4`, `code5`

### OCC1950 Format
```bash
python convert_data_to_parquet.py --input-dir Data/Training_data/ --format occ1950
```

Columns: `occ1`, `lang`, `OCC1950_1`, `OCC1950_2`

## Advanced Usage

### Custom File Patterns

```bash
# Convert only files matching a specific pattern
python convert_data_to_parquet.py \
    --input-dir Data/Training_data/ \
    --pattern "*_train.csv"
```

### Programmatic Conversion

You can also use the conversion utilities directly in Python:

```python
from histocc.utils.data_conversion import (
    convert_csv_to_parquet,
    convert_directory_to_parquet,
    get_hisco_dtype_overrides,
    get_hisco_converters,
)

# Convert a single file
convert_csv_to_parquet(
    'Data/Training_data/en_train.csv',
    dtype_overrides=get_hisco_dtype_overrides(),
    converters=get_hisco_converters(),
)

# Convert a directory
convert_directory_to_parquet(
    'Data/Training_data/',
    dtype_overrides=get_hisco_dtype_overrides(),
    converters=get_hisco_converters(),
)
```

## Backward Compatibility

The dataloader maintains full backward compatibility with CSV files. You can:
- Use CSV files as before
- Mix CSV and Parquet files
- Gradually migrate to Parquet

The `_read_data_file()` function automatically detects the file format based on the extension.

## Performance Comparison

Example performance gains on a typical training dataset:

| File Format | Load Time | File Size | Speedup |
|-------------|-----------|-----------|---------|
| CSV         | 12.5s     | 450 MB    | 1.0x    |
| Parquet     | 2.1s      | 95 MB     | 6.0x    |

*Note: Actual performance depends on data size, disk speed, and system resources*

## Troubleshooting

### Missing PyArrow

If you get an error about missing `pyarrow`:

```bash
pip install pyarrow
```

### Type Conversion Issues

The conversion script uses appropriate type converters to ensure:
- Strings like "42" in the `occ1` column remain strings
- Language codes remain strings
- Code columns remain strings

If you encounter type issues, verify the data format:

```python
import pandas as pd

# Check CSV data types
df_csv = pd.read_csv('data.csv')
print(df_csv.dtypes)

# Check Parquet data types
df_parquet = pd.read_parquet('data.parquet')
print(df_parquet.dtypes)
```

## Recommended Workflow

1. **Convert your data once**: Run the conversion script on your training and validation directories
2. **Update your training scripts**: Change file paths from `.csv` to `.parquet`
3. **Enjoy faster loading**: Your data will load significantly faster during training

## Notes

- The original CSV files are not modified or deleted during conversion
- Parquet files are created alongside CSV files by default
- You can safely delete CSV files after verifying Parquet files work correctly
- For very large datasets, consider converting in batches if memory is limited
