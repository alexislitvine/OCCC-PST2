#!/usr/bin/env python
import sys, torch
from tqdm import tqdm

DENY = ("decoder.", "linear_decoder.", "lm_head.", "head.", "classifier.")

ALLOW_ROOTS = (
    "char_embeddings.",
    "initial_char_encoder.",
    "chars_to_molecules.",
    "projection.",
    "final_char_encoder.",
    "pooler.",
    "encoder.layer.",   # we will upshift this to encoder.encoder.layer.
    "layer.",           # raw layer.* seen in some dumps
)

def pull_model_sd(obj):
    if isinstance(obj, dict):
        if "model" in obj and isinstance(obj["model"], dict):
            return obj["model"]
        if "state_dict" in obj and isinstance(obj["state_dict"], dict):
            return obj["state_dict"]
    return obj  # assume raw state_dict

def convert(inp, outp):
    raw = torch.load(inp, map_location="cpu", weights_only=False)
    sd  = pull_model_sd(raw)
    out = {}
    kept = dropped = 0

    for k, v in tqdm(list(sd.items()), desc="Scanning"):
        if any(k.startswith(dp) for dp in DENY):
            dropped += 1
            continue

        k_new = None

        # --- transformer blocks ---
        if k.startswith("encoder.encoder.layer."):
            # already perfect for post-strip
            k_new = k
        elif k.startswith("encoder.layer."):
            # need one more 'encoder.' so that strip keeps 'encoder.layer.*'
            k_new = "encoder." + k
        elif k.startswith("layer."):
            # raw layer.* -> add 'encoder.encoder.' so strip -> 'encoder.layer.*'
            k_new = "encoder." + k    # now 'encoder.layer.*'
            k_new = "encoder." + k_new  # now 'encoder.encoder.layer.*'

        # --- other encoder namespaces (should NOT keep 'encoder.' after strip) ---
        elif k.startswith(("char_embeddings.", "initial_char_encoder.",
                           "chars_to_molecules.", "projection.",
                           "final_char_encoder.", "pooler.")):
            k_new = "encoder." + k
        elif k.startswith(("encoder.char_embeddings.", "encoder.initial_char_encoder.",
                           "encoder.chars_to_molecules.", "encoder.projection.",
                           "encoder.final_char_encoder.", "encoder.pooler.")):
            # already with single encoder prefix → OK
            k_new = k

        # unknown namespaces: skip quietly
        if k_new is None:
            dropped += 1
            continue

        out[k_new] = v
        kept += 1

    wrapped = {"model": out, "step": 0}
    torch.save(wrapped, outp)
    print(f"\nKept {kept} tensors, dropped {dropped}.")
    print(f"Wrote: {outp}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: fix_encoder_prefixes.py <in_ckpt> <out_ckpt>")
        sys.exit(2)
    convert(sys.argv[1], sys.argv[2])

