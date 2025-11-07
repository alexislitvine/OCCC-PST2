#!/usr/bin/env python
"""
Convert CSV training/validation data files to Parquet format for faster loading.

This script converts CSV data files to Parquet format, which provides:
- Significantly faster data loading (2-10x speedup)
- Better compression (typically 50-80% smaller files)
- Preserved data types (no need for converters)

Usage:
    # Convert a single CSV file
    python convert_data_to_parquet.py --input path/to/data.csv
    
    # Convert all CSV files in a directory
    python convert_data_to_parquet.py --input-dir path/to/Training_data/
    
    # Convert with specific output directory
    python convert_data_to_parquet.py --input-dir path/to/Training_data/ --output-dir path/to/Training_data_parquet/
    
    # Convert for OCC1950 data format
    python convert_data_to_parquet.py --input-dir path/to/data/ --format occ1950
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from histocc.utils.data_conversion import (
    convert_csv_to_parquet,
    convert_directory_to_parquet,
    get_hisco_dtype_overrides,
    get_hisco_converters,
    get_occ1950_dtype_overrides,
    get_occ1950_converters,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description='Convert CSV data files to Parquet format for faster loading',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Input options (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '--input',
        type=str,
        help='Path to a single CSV file to convert'
    )
    input_group.add_argument(
        '--input-dir',
        type=str,
        help='Directory containing CSV files to convert'
    )
    
    # Output options
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output path for Parquet file (only with --input). Default: replace .csv with .parquet'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Output directory for Parquet files (only with --input-dir). Default: same as input directory'
    )
    
    # Data format
    parser.add_argument(
        '--format',
        type=str,
        choices=['hisco', 'occ1950'],
        default='hisco',
        help='Data format type (default: hisco)'
    )
    
    # File pattern
    parser.add_argument(
        '--pattern',
        type=str,
        default='*.csv',
        help='Glob pattern for CSV files when using --input-dir (default: *.csv)'
    )
    
    return parser.parse_args()


def main():
    args = parse_args()
    
    # Get dtype overrides and converters based on format
    if args.format == 'hisco':
        dtype_overrides = get_hisco_dtype_overrides()
        converters = get_hisco_converters()
    elif args.format == 'occ1950':
        dtype_overrides = get_occ1950_dtype_overrides()
        converters = get_occ1950_converters()
    else:
        dtype_overrides = None
        converters = None
    
    try:
        if args.input:
            # Convert single file
            if args.output_dir:
                print("Warning: --output-dir is ignored when using --input")
            
            parquet_path = convert_csv_to_parquet(
                args.input,
                args.output,
                dtype_overrides=dtype_overrides,
                converters=converters,
            )
            print(f"\n✓ Successfully converted to {parquet_path}")
            
        else:
            # Convert directory
            if args.output:
                print("Warning: --output is ignored when using --input-dir")
            
            parquet_files = convert_directory_to_parquet(
                args.input_dir,
                args.output_dir,
                dtype_overrides=dtype_overrides,
                converters=converters,
                pattern=args.pattern,
            )
            
            if parquet_files:
                print(f"\n✓ Successfully converted {len(parquet_files)} files")
                print(f"\nTo use Parquet files for training, update file paths to point to .parquet files")
                print("The dataloader will automatically detect and use the Parquet format")
            else:
                print("\n✗ No files were converted")
                sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n✗ Conversion interrupted by user", file=sys.stderr)
        sys.exit(130)
    except (IOError, OSError) as e:
        print(f"\n✗ File I/O error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
