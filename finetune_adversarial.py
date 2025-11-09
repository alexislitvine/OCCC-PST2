from histocc import OccCANINE
import pandas as pd

df = pd.read_csv("data/labelled_data/EN_PSTI_CAMPOP_train.csv")
df_adv = pd.read_csv("data/adversarial_data/merged_results.csv")

# Merge and stor to data/tmp
df = pd.concat([df, df_adv], ignore_index=True)
df.to_csv("data/tmp/merged_data.csv", index=False)

mod_pst = OccCANINE( # PST model
    "models/mixer-psti-ft/last.bin", 
    hf=False, 
    system="PSTI",
    use_within_block_sep=True,
    verbose=True
)

mod_pst.finetune(
    dataset="data/tmp/merged_data.csv",
    save_path="models/mixer-psti-2nd-stage",
    input_col="occ1",
    target_cols=["PSTI_1", "PSTI_2", "PSTI_3", "PSTI_4", "PSTI_5"],
    language="en",
    language_col="lang",
    save_interval=1000,
    log_interval=1000,
    eval_interval=1000,
    drop_bad_labels=True,
    allow_codes_shorter_than_block_size=True,
    share_val=0.1,
    learning_rate=5e-5,
    num_epochs=3,
    warmup_steps=1000,
    seq2seq_weight=0.1,
    freeze_encoder=False
)





