"""
@author: sa-tsdj

"""


import glob
import os
from pathlib import Path

import pandas as pd


# Use relative path from script location to Data directory
SCRIPT_DIR = Path(__file__).parent.absolute()
DATA_DIR = SCRIPT_DIR / 'Data' / 'PST2_AUG_RETRAINING'


def find_files(include_gpt: bool = True) -> list[str]:
    print("Finding files for PST2 data preparation...")
    
    # Find HISCO sets
    files = glob.glob(str(DATA_DIR / 'hisco_inferred' / 'Training_data' / '*'))
    print(f"Found {len(files)} HISCO inferred training files")

    # Find new "fuzzy" English data
    fuzzy_files = [f for f in glob.glob(str(DATA_DIR / 'new_mappings' / 'fuzzy_duplicates' / '*')) if 'pst2' in f]
    files.extend(fuzzy_files)
    print(f"Found {len(fuzzy_files)} fuzzy duplicate files")

    # Find the "old" but recoded data
    old_recoded_file = str(DATA_DIR / 'pst2_old_recoded' / 'Old_PST2_Training_Data_translated_recoded.csv')
    files.append(old_recoded_file)
    print(f"Added old recoded data file: {os.path.basename(old_recoded_file)}")

    # Add the GPT titles
    if include_gpt:
        gpt_file = str(DATA_DIR / 'GPT_titles_with_pairs.csv')
        files.append(gpt_file)
        print(f"Added GPT titles file: {os.path.basename(gpt_file)}")

    # Add from scheme
    scheme_file = str(DATA_DIR / 'new_pst2_scheme' / 'pst2_summary_descriptions_clean.csv')
    files.append(scheme_file)
    print(f"Added scheme file: {os.path.basename(scheme_file)}")
    
    print(f"Total files to process: {len(files)}")
    return files


DTYPES = {
    'pst2_1': str,
    'pst2_2': str,
    'pst2_3': str,
    'pst2_4': str,
    'pst2_5': str,
}


def load(files: list[str]) -> pd.DataFrame:
    print(f"\nLoading data from {len(files)} files...")
    
    print(f"Loading file 1/{len(files)}: {os.path.basename(files[0])}")
    data = pd.read_csv(files[0], dtype=DTYPES)
    data['src'] = files[0]
    print(f"  Loaded {len(data)} records")

    for idx, f in enumerate(files[1:], start=2):
        print(f"Loading file {idx}/{len(files)}: {os.path.basename(f)}")
        _data = pd.read_csv(f, dtype=DTYPES)
        _data['src'] = f
        print(f"  Loaded {len(_data)} records")
        data = pd.concat([data, _data])

    print(f"Total records loaded: {len(data)}")
    return data


def write_all():
    print("=" * 70)
    print("PST2 Data Preparation Script")
    print("=" * 70)
    
    files = find_files()

    # Load
    print("\nLoading and concatenating data from all files...")
    data = pd.concat([
        pd.read_csv(f, dtype=DTYPES) for f in files
    ])
    print(f"Total records after concatenation: {len(data)}")
    
    # Seems there is 135 broken records stemming from 'pst2_summary_descriptions_clean'
    print("\nCleaning data...")
    na_count = data['pst2_1'].isna().sum()
    print(f"Found {na_count} records with missing pst2_1 values")
    assert data['pst2_1'].isna().sum() == 135
    data = data[data['pst2_1'].notna()].copy()
    print(f"Records after removing missing pst2_1: {len(data)}")

    # There are cases where PST code does not contain ',', which by definition
    # is error
    no_comma_count = (~data['pst2_1'].str.contains(',')).sum()
    print(f"Found {no_comma_count} records without comma in pst2_1")
    (~data['pst2_1'].str.contains(',')).sum() == 135
    data = data[data['pst2_1'].str.contains(',')]
    print(f"Records after removing invalid pst2_1 format: {len(data)}")

    # All codes should have length 8
    code_lens_col1 = [len(x) for x in data['pst2_1'].str.split(',')]
    assert set(code_lens_col1) == {8}
    print("Verified: All PST2 codes have length 8")

    # Seems there is 1 weird NaN observation for "occ1"
    occ1_na_count = data['occ1'].isna().sum()
    print(f"Found {occ1_na_count} records with missing occ1 values")
    assert data['occ1'].isna().sum() == 1
    data = data[data['occ1'].notna()].copy()
    print(f"Records after removing missing occ1: {len(data)}")

    # There are TONS of cases of linebreaks
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

    # Time for the ugliest of all manual key insertions
    print("\nGenerating key mapping...")
    keyset = sorted(set(data['pst2_1']))
    keyset.extend(['?', pd.NA])
    print(f"Created key mapping with {len(keyset)} unique codes")

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
    write_all()


if __name__ == '__main__':
    main()
