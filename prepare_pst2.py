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
    # Find HISCO sets
    files = glob.glob(str(DATA_DIR / 'hisco_inferred' / 'Training_data' / '*'))

    # Find new "fuzzy" English data
    files.extend(
        [f for f in glob.glob(str(DATA_DIR / 'new_mappings' / 'fuzzy_duplicates' / '*')) if 'pst2' in f]
    )

    # Find the "old" but recoded data
    files.append(str(DATA_DIR / 'pst2_old_recoded' / 'Old_PST2_Training_Data_translated_recoded.csv'))

    # Add the GPT titles
    if include_gpt:
        files.append(str(DATA_DIR / 'GPT_titles_with_pairs.csv'))

    # Add from scheme
    files.append(str(DATA_DIR / 'new_pst2_scheme' / 'pst2_summary_descriptions_clean.csv'))

    return files


DTYPES = {
    'pst2_1': str,
    'pst2_2': str,
    'pst2_3': str,
    'pst2_4': str,
    'pst2_5': str,
}


def load(files: list[str]) -> pd.DataFrame:
    data = pd.read_csv(files[0], dtype=DTYPES)
    data['src'] = files[0]

    for f in files[1:]:
        _data = pd.read_csv(f, dtype=DTYPES)
        _data['src'] = f
        data = pd.concat([data, _data])

    return data


def write_all():
    files = find_files()

    # Load
    data = pd.concat([
        pd.read_csv(f, dtype=DTYPES) for f in files
    ])
    # Seems there is 135 broken records stemming from 'pst2_summary_descriptions_clean'
    assert data['pst2_1'].isna().sum() == 135
    data = data[data['pst2_1'].notna()].copy()

    # There are cases where PST code does not contain ',', which by definition
    # is error
    (~data['pst2_1'].str.contains(',')).sum() == 135
    data = data[data['pst2_1'].str.contains(',')]

    # All codes should have length 8
    code_lens_col1 = [len(x) for x in data['pst2_1'].str.split(',')]
    assert set(code_lens_col1) == {8}

    # Seems there is 1 weird NaN observation for "occ1"
    assert data['occ1'].isna().sum() == 1
    data = data[data['occ1'].notna()].copy()

    # There are TONS of cases of linebreaks
    data['occ1'] = data['occ1'].transform(lambda x: x.replace('\n', ' '))

    # Write
    output_dir = SCRIPT_DIR / 'Data' / 'Training_data_other'
    output_dir.mkdir(parents=True, exist_ok=True)
    fn_out = output_dir / 'pst2.csv'

    if fn_out.exists():
        raise FileExistsError(fn_out)

    data.to_csv(fn_out, index=False)

    # Time for the ugliest of all manual key insertions
    keyset = sorted(set(data['pst2_1']))
    keyset.extend(['?', pd.NA])

    key = pd.DataFrame({
        'system_code': keyset,
        'code': range(len(keyset)),
    })
    key_dir = SCRIPT_DIR / 'Data' / 'pst2' / 'mixer-pst2-v3'
    key_dir.mkdir(parents=True, exist_ok=True)
    key.to_csv(key_dir / 'key_manual.csv', index=False)


def main():
    write_all()


if __name__ == '__main__':
    main()
