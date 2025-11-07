"""
Example: Converting CSV training data to Parquet format

This example demonstrates how to convert CSV training/validation files to 
Parquet format for faster data loading during training.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.absolute()))
# Import directly from the module to avoid histocc package initialization
sys.path.insert(0, str(Path(__file__).parent.absolute() / 'histocc' / 'utils'))

from data_conversion import (
    convert_csv_to_parquet,
    convert_directory_to_parquet,
    get_hisco_dtype_overrides,
    get_hisco_converters,
)


def example_convert_single_file():
    """Example: Convert a single CSV file to Parquet."""
    print("=" * 60)
    print("Example 1: Converting a single CSV file")
    print("=" * 60)
    
    # Convert the toy data file
    csv_path = "histocc/Data/TOYDATA.csv"
    
    parquet_path = convert_csv_to_parquet(
        csv_path,
        dtype_overrides=get_hisco_dtype_overrides(),
        converters=get_hisco_converters(),
    )
    
    print(f"\n✓ Converted {csv_path} to {parquet_path}")
    print("\nTo use in training, simply pass the .parquet file path instead of .csv")
    
    # Clean up
    parquet_path.unlink()
    print(f"\n(Cleaned up {parquet_path})")


def example_convert_directory():
    """Example: Convert all CSV files in a directory to Parquet."""
    print("\n" + "=" * 60)
    print("Example 2: Converting a directory of CSV files")
    print("=" * 60)
    
    # For demonstration, we'll create a temporary directory with sample files
    import tempfile
    import pandas as pd
    import shutil
    
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # Create some sample CSV files
        for i in range(3):
            csv_path = temp_dir / f"train_{i}.csv"
            df = pd.DataFrame({
                'occ1': [f'occupation_{i}_{j}' for j in range(1000)],
                'lang': ['en'] * 1000,
                'code1': [str(j % 100) for j in range(1000)],
                'code2': [str((j + 1) % 100) for j in range(1000)],
            })
            df.to_csv(csv_path, index=False)
        
        print(f"\nCreated sample directory: {temp_dir}")
        print(f"Files: {list(temp_dir.glob('*.csv'))}")
        
        # Convert all CSV files to Parquet
        parquet_files = convert_directory_to_parquet(
            temp_dir,
            dtype_overrides=get_hisco_dtype_overrides(),
            converters=get_hisco_converters(),
        )
        
        print(f"\n✓ Converted {len(parquet_files)} files to Parquet format")
        print("\nParquet files created:")
        for pf in parquet_files:
            print(f"  - {pf.name}")
    
    finally:
        # Clean up
        shutil.rmtree(temp_dir)
        print(f"\n(Cleaned up {temp_dir})")


def example_performance_comparison():
    """Example: Compare loading performance between CSV and Parquet."""
    print("\n" + "=" * 60)
    print("Example 3: Performance comparison")
    print("=" * 60)
    
    import time
    import pandas as pd
    import tempfile
    
    # Create a larger sample file for better benchmark
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        csv_path = temp_dir / "benchmark.csv"
        
        # Create a dataset with 50,000 rows
        print("\nCreating benchmark dataset (50,000 rows)...")
        df = pd.DataFrame({
            'occ1': [f'occupation_{i}' for i in range(50000)],
            'lang': ['en'] * 50000,
            'code1': [str(i % 1000) for i in range(50000)],
            'code2': [str((i + 1) % 1000) for i in range(50000)],
            'code3': [str((i + 2) % 1000) for i in range(50000)],
        })
        df.to_csv(csv_path, index=False)
        
        # Convert to Parquet
        parquet_path = convert_csv_to_parquet(
            csv_path,
            dtype_overrides=get_hisco_dtype_overrides(),
            converters=get_hisco_converters(),
        )
        
        # Benchmark loading times
        n_iterations = 5
        
        print(f"\nBenchmarking loading times ({n_iterations} iterations)...")
        
        # CSV loading
        start = time.time()
        for _ in range(n_iterations):
            _ = pd.read_csv(csv_path)
        csv_time = time.time() - start
        
        # Parquet loading
        start = time.time()
        for _ in range(n_iterations):
            _ = pd.read_parquet(parquet_path)
        parquet_time = time.time() - start
        
        print(f"\nResults:")
        print(f"  CSV loading:     {csv_time:.3f}s ({csv_time/n_iterations:.4f}s per iteration)")
        print(f"  Parquet loading: {parquet_time:.3f}s ({parquet_time/n_iterations:.4f}s per iteration)")
        print(f"  Speedup:         {csv_time/parquet_time:.2f}x faster with Parquet")
        
        # File size comparison
        import os
        csv_size = os.path.getsize(csv_path) / (1024 * 1024)  # MB
        parquet_size = os.path.getsize(parquet_path) / (1024 * 1024)  # MB
        
        print(f"\nFile sizes:")
        print(f"  CSV:        {csv_size:.2f} MB")
        print(f"  Parquet:    {parquet_size:.2f} MB")
        print(f"  Compression: {csv_size/parquet_size:.2f}x smaller with Parquet")
        
    finally:
        # Clean up
        import shutil
        shutil.rmtree(temp_dir)
        print(f"\n(Cleaned up {temp_dir})")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("CSV to Parquet Conversion Examples")
    print("=" * 60)
    
    example_convert_single_file()
    example_convert_directory()
    example_performance_comparison()
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print("\nParquet format provides:")
    print("  • Faster data loading (typically 2-10x)")
    print("  • Smaller file sizes (typically 2-5x compression)")
    print("  • Better type preservation")
    print("  • Backward compatible with existing CSV workflow")
    print("\nFor more information, see PARQUET_CONVERSION_GUIDE.md")
    print("=" * 60)


if __name__ == '__main__':
    main()
