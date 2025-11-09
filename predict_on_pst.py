# run_predictions_and_format.py
from pathlib import Path
import pandas as pd
import datetime
from tqdm import tqdm
from histocc import OccCANINE
import unicodedata
import re  # NEW

def detect_encoding(p: Path) -> str:
    """
    Minimal, dependency-free probe. Tries common encodings in order.
    Returns the first that cleanly decodes.
    """
    candidates = ["utf-8", "utf-8-sig", "cp1252", "latin1"]
    data = p.read_bytes()
    for enc in candidates:
        try:
            data.decode(enc)
            return enc
        except UnicodeDecodeError:
            continue
    return "latin1"  # last-resort fallback

def normalize_series_nfc(s: pd.Series) -> pd.Series:
    return s.astype(str).map(lambda x: unicodedata.normalize("NFC", x))

# cleaning function (remove commas, semicolons, colons, slashes, dots)
def clean_string(text: str) -> str:
    if text is None:
        return ""
    # Normalize to NFC first to avoid mixed accent forms
    s = unicodedata.normalize("NFC", str(text))
    # Remove , ; : . / and backslash \
    s = re.sub(r"[,\.;:/\\]", "", s)
    # Collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s

# import the formatting module:
from format_preds import (
    format_predictions,
    serialize_formatted_entries,
    write_quarter_samples,
    write_json,
)

def select_csv_file(directory: Path) -> Path:
    directory = Path(directory)
    csv_files = list(directory.glob("*.csv"))
    if not csv_files:
        print(f"No CSV files found in {directory}")
        raise SystemExit(1)
    print("Available CSV files:")
    for idx, file in enumerate(csv_files, start=1):
        print(f"{idx}. {file.name}")
    choice = int(input("Enter the number of the file to predict: "))
    return csv_files[choice - 1]


def main():
    tqdm.pandas(desc="Cleaning strings")

    data_dir = Path(input("Enter the directory containing CSV files: ").strip())
    csv_file = select_csv_file(data_dir)
    file_base = csv_file.stem

    predicted_dir = data_dir.parent / "predicted"
    predicted_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")

    HOW_MANY_PREDS = 10
    chunksize = 10000
    EXCEL_FRIENDLY = True
    out_enc = "utf-8-sig" if EXCEL_FRIENDLY else "utf-8"

    print("Preprocessing data…")
    with open(csv_file, "r", encoding="latin1") as f:
        total_lines = sum(1 for _ in f) - 1

    source_enc = detect_encoding(csv_file)
    print(f"Detected input encoding: {source_enc}")

    reader = pd.read_csv(csv_file, chunksize=chunksize, encoding=source_enc)
    clean_chunks = []

    for chunk in tqdm(reader,
                      total=(total_lines // chunksize) + 1,
                      desc="Preprocessing chunks",
                      unit="chunk"):
        mask = (
            chunk["occ1_original"].notna()
            & chunk["occ1_original"].astype(str).str.strip().astype(bool)
        )
        chunk = chunk.loc[mask].copy()
        clean_chunks.append(chunk)

    df = pd.concat(clean_chunks, ignore_index=True)
    df = df.drop_duplicates(subset=["id"])

    # Normalize accents first
    df["occ1_original"] = normalize_series_nfc(df["occ1_original"])

    # Clean strings
    df["occ1_clean"] = df["occ1_original"].progress_map(clean_string)
    df = df[df["occ1_clean"].astype(str).str.strip().astype(bool)]

    # Deduplicate by cleaned string BEFORE saving and predicting
    before = len(df)
    df = df.drop_duplicates(subset=["occ1_clean"], keep="first")
    after = len(df)
    print(f"Removed {before - after} duplicate string(s) based on 'occ1_clean'.")

    # ✅ Save cleaned + deduplicated copy
    cleaned_csv_out = predicted_dir / f"{file_base}_cleaned_{ts}.csv"
    df.to_csv(cleaned_csv_out, index=False, encoding=out_enc)
    print(f"→ Saved cleaned & deduplicated CSV: {cleaned_csv_out.name}")

    if len(df["id"].unique()) != len(df):
        raise ValueError("Non unique ids after preprocessing!")

    # --- run predictions on df (same as before) ---
    mod_hisco = OccCANINE(verbose=True)
    mod_pst = OccCANINE(
        "/home/alexis/PST_PREDICT/models/mixer-pst2_conservative_latin_only_05112025/last.bin",
        hf=False,
        system="pst",
        use_within_block_sep=True,
        verbose=True,
    )

    print("Running HISCO predictions…")
    pred_hisco = mod_hisco(df.occ1_clean.tolist(), k_pred=HOW_MANY_PREDS)
    pred_hisco["id"] = df["id"].tolist()
    pred_hisco["occ1"] = df["occ1_original"].tolist()
    pred_hisco["occ1_clean"] = df["occ1_clean"].tolist()
    hisco_out = predicted_dir / f"{file_base}_predictions_hisco_{ts}.csv"
    pred_hisco.to_csv(hisco_out, index=False, encoding=out_enc)
    print(f"→ Saved HISCO to {hisco_out.name}")

    print("Running PST predictions…")
    pred_pst = mod_pst(df.occ1_clean.tolist(), k_pred=HOW_MANY_PREDS)
    pred_pst["id"] = df["id"].tolist()
    pred_pst["occ1"] = df["occ1_original"].tolist()
    pred_pst["occ1_clean"] = df["occ1_clean"].tolist()
    pst_out = predicted_dir / f"{file_base}_predictions_pst_{ts}.csv"
    pred_pst.to_csv(pst_out, index=False, encoding=out_enc)
    print(f"→ Saved PST   to {pst_out.name}")

    # 4) path to PST2 lookup json
    #    prompt so you can point to the exact file you want
    lookup_path = Path(input("Path to updatedPST2CodeDict.json: ").strip())
    if not lookup_path.exists():
        raise FileNotFoundError(f"Lookup not found: {lookup_path}")

    # 5) Format & merge predictions -> combined JSON (with progress bars)
    print("Formatting/merging predictions…")
    entries, stats = format_predictions(
        hisco_csv_path=hisco_out,
        pst2_csv_path=pst_out,
        pst2_lookup_json_path=lookup_path,
        csv_encoding=out_enc,
    )

    # Log duplicates like the Node script
    if stats.duplicate_strings:
        print("Duplicate entries found for the following strings:")
        for s, c in stats.duplicate_strings:
            print(f'"{s}" occurs {c} times')
    else:
        print("No duplicate entries found.")

    combined_json = predicted_dir / f"{file_base}_processedPredictions_{ts}.json"
    write_json(combined_json, serialize_formatted_entries(entries))
    print(f"→ Wrote combined formatted JSON: {combined_json.name}")
    print(
        f"Total predictions processed: {stats.total_predictions_processed} | "
        f"Failures: {stats.failures}"
    )

    # # 6) Create 4 sampled chunks as JSON + CSV (titles) beside the combined JSON
    # print("Writing 4 sampled quarter-chunks (JSON + CSV)…")
    # write_quarter_samples(
    #     formatted_entries=entries,
    #     out_dir=predicted_dir,
    #     base_name=f"{file_base}_titles",
    #     sample_size=300,
    #     seed=42,
    #     csv_encoding=out_enc,
    # )
    print("All done ✅")

if __name__ == "__main__":
    main()
