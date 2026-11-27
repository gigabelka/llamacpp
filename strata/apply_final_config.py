"""Apply the chosen coding/no-reasoning settings to the installed model run config.

Usage: python -I apply_final_config.py [--config PATH]

Writes the model config Strata uses as the base of every launch, keeps a copy of
the previous file, and writes the same settings to
strata/qwen3.8-flash-next-iq3_s.coding-noreason.json for the report.
"""
import argparse
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT = Path(r"C:\Users\viktor\AppData\Local\Strata\install\strata-iq3_s.json")
VOCAB = Path(r"C:\Users\viktor\AppData\Local\Strata\terminal\0.1.69\data\draft_vocab_en.bin")
COPY = HERE / "qwen3.8-flash-next-iq3_s.coding-noreason.json"

SAMPLING = {
    "temperature": 0.6,
    "top_p": 0.8,
    "top_k": 20,
    "min_p": 0.0,
    "presence_penalty": 0.0,
    "frequency_penalty": 0.0,
    "repetition_penalty": 1.0,
    "seed": 1,
}
USER_ARGS = ["--draft-conf", "0.35", "--mtp-draft-vocab", str(VOCAB)]

ap = argparse.ArgumentParser()
ap.add_argument("--config", default=str(DEFAULT))
a = ap.parse_args()
path = Path(a.config)

cfg = json.loads(path.read_text(encoding="utf-8-sig"))
backup = HERE / "backup" / "strata-iq3_s.json.before-final"
if not backup.exists():
    shutil.copyfile(path, backup)


def merge_args(args, user):
    """The engine args with the person's options on top (the same rule as strata_control.user_args.merge)."""
    flags = {user[i] for i in range(0, len(user), 2) if user[i].startswith("--")}
    kept, i = [], 0
    while i < len(args):
        flag = args[i]
        if flag in flags:
            i += 2 if i + 1 < len(args) and not str(args[i + 1]).startswith("--") else 1
            continue
        kept.append(flag)
        i += 1
    return kept + list(user)


cfg["drafting"] = "dflash2"
cfg["reasoning_effort"] = "none"
cfg["sampling"] = dict(SAMPLING)
cfg["user_args"] = list(USER_ARGS)
if isinstance(cfg.get("args"), list):
    cfg["args"] = merge_args(cfg["args"], USER_ARGS)
    cfg["args_written"] = list(cfg["args"])
path.write_text(json.dumps(cfg, indent=1), encoding="utf-8")
COPY.write_text(json.dumps(cfg, indent=1), encoding="utf-8")
print(f"applied to {path}")
print(f"copy: {COPY}")
print(f"backup: {backup}")
