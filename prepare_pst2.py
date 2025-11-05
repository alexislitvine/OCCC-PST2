"""
@author: sa-tsdj

"""

import glob
import os
from pathlib import Path
import pandas as pd

SCRIPT_DIR = Path(__file__).parent.absolute()
DATA_DIR = SCRIPT_DIR / 'Data' / 'PST2_AUG_RETRAINING'

DTYPES = {
    'pst2_1': str,
    'pst2_2': str,
    'pst2_3': str,
    'pst2_4': str,
    'pst2_5': str,
}


def find_files(include_gpt: bool = True) -> list[str]:
    print("Finding files for PST2 data preparation...")

    files = glob.glob(str(DATA_DIR / 'hisco_inferred' / 'Training_data' / '*'))
    print(f"Found {len(files)} HISCO inferred training files")

    fuzzy_files = [f for f in glob.glob(str(DATA_DIR / 'new_mappings' / 'fuzzy_duplicates' / '*')) if 'pst2' in f]
    files.extend(fuzzy_files)
    print(f"Found {len(fuzzy_files)} fuzzy duplicate files")

    old_recoded_file = str(DATA_DIR / 'pst2_old_recoded' / 'Old_PST2_Training_Data_translated_recoded.csv')
    files.append(old_recoded_file)
    print(f"Added old recoded data file: {os.path.basename(old_recoded_file)}")

    if include_gpt:
        gpt_file = str(DATA_DIR / 'GPT_titles_with_pairs.csv')
        files.append(gpt_file)
        print(f"Added GPT titles file: {os.path.basename(gpt_file)}")

    scheme_file = str(DATA_DIR / 'new_pst2_scheme' / 'pst2_summary_descriptions_clean.csv')
    files.append(scheme_file)
    print(f"Added scheme file: {os.path.basename(scheme_file)}")

    print(f"Total files to process: {len(files)}")
    return files


def load(files: list[str]) -> pd.DataFrame:
    print(f"\nLoading data from {len(files)} file(s)...")

    data_frames = []
    for idx, f in enumerate(files, start=1):
        print(f"Loading file {idx}/{len(files)}: {os.path.basename(f)}")
        df = pd.read_csv(f, dtype=DTYPES)
        df['src'] = f
        print(f"  Loaded {len(df)} records")
        data_frames.append(df)

    data = pd.concat(data_frames, ignore_index=True)
    print(f"Total records loaded: {len(data)}")
    return data


def write_all(explicit_csv: str | None = None):
    print("=" * 70)
    print("PST2 Data Preparation Script")
    print("=" * 70)

    # 🆕 Option: single explicit file
    if explicit_csv:
        explicit_path = Path(explicit_csv)
        if not explicit_path.exists():
            raise FileNotFoundError(f"Explicit CSV not found: {explicit_path}")
        print(f"\nUsing explicit CSV file only: {explicit_path}")
        files = [str(explicit_path)]
    else:
        files = find_files()

    # Load
    print("\nLoading and concatenating data from file(s)...")
    data = load(files)
    print(f"Total records after concatenation: {len(data)}")

    # Clean
    print("\nCleaning data...")
    na_count = data['pst2_1'].isna().sum()
    print(f"Found {na_count} records with missing pst2_1 values")
    data = data[data['pst2_1'].notna()].copy()

    no_comma_count = (~data['pst2_1'].str.contains(',')).sum()
    print(f"Found {no_comma_count} records without comma in pst2_1")
    data = data[data['pst2_1'].str.contains(',')]
    print(f"Records after removing invalid pst2_1 format: {len(data)}")

    code_lens_col1 = [len(x) for x in data['pst2_1'].str.split(',')]
    assert set(code_lens_col1) == {8}
    print("Verified: All PST2 codes have length 8")

    occ1_na_count = data['occ1'].isna().sum()
    print(f"Found {occ1_na_count} records with missing occ1 values")
    data = data[data['occ1'].notna()].copy()

    print("Cleaning linebreaks from occ1 field...")
    data['occ1'] = data['occ1'].transform(lambda x: x.replace('\n', ' '))

    # Write
    print("\nPreparing output files...")
    output_dir = SCRIPT_DIR / 'Data' / 'Training_data_other'
    output_dir.mkdir(parents=True, exist_ok=True)
    fn_out = output_dir / 'pst2.csv'

    if fn_out.exists():
        raise FileExistsError(fn_out)

    print(f"Writing training data to: {fn_out}")
    data.to_csv(fn_out, index=False)
    print(f"Successfully wrote {len(data)} records to {fn_out}")

    print("\nGenerating key mapping...")
    keyset = sorted(set(data['pst2_1']))
    keyset.extend(['?', pd.NA])

    key = pd.DataFrame({
        'system_code': keyset,
        'code': range(len(keyset)),
    })
    key_dir = SCRIPT_DIR / 'Data' / 'pst2' / 'mixer-pst2-v3'
    key_dir.mkdir(parents=True, exist_ok=True)
    key_file = key_dir / 'key_manual.csv'
    print(f"Writing key mapping to: {key_file}")
    key.to_csv(key_file, index=False)
    print(f"Successfully wrote key mapping with {len(key)} entries")

    print("\n" + "=" * 70)
    print("PST2 Data Preparation Completed Successfully!")
    print("=" * 70)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="PST2 Data Preparation Script")
    parser.add_argument(
        "--csv",
        type=str,
        default=None,
        help="Path to an explicit CSV file to process (skips automatic search)."
    )
    args = parser.parse_args()
    write_all(explicit_csv=args.csv)


if __name__ == "__main__":
    main()

