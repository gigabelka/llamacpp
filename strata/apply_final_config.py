"""Apply the chosen coding/no-reasoning settings to an installed model run config.

Usage:
  python -I apply_final_config.py [--config PATH] [--repo-copy PATH] [--log PATH]
                                  [--backup-name NAME] [--drafting dflash2|mtp|off]
                                  [--draft-conf P] [--draft-vocab PATH | --no-draft-vocab]
                                  [--max-context N] [--kv int8|q4_0] [--rope-scale F]

Writes the model config Strata uses as the base of every launch, keeps a copy of
the previous file, and writes the same settings to the repository copy of the run
config for the report. The defaults are the IQ3_S no-reasoning configuration
(strata/README.md sections 3-5); the NVFP4 configuration is the same call with
--drafting mtp --no-draft-vocab --max-context 524288 --kv int8 --rope-scale 2
(no DFlash2 for that model, and MTP keeps its own draft vocabulary).
"""
import argparse
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGS = HERE.parent / "logs"
STRATA_DATA = Path(r"C:\Users\viktor\AppData\Local\Strata\Strata-data")
VOCAB = Path(r"C:\Users\viktor\AppData\Local\Strata\terminal\0.1.69\data\draft_vocab_en.bin")

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
ROPE_FLAGS = ("--rope-scaling", "--rope-scale")

ap = argparse.ArgumentParser()
ap.add_argument("--config", default=r"C:\Users\viktor\AppData\Local\Strata\install\strata-iq3_s.json")
ap.add_argument("--repo-copy", default=str(HERE / "qwen3.8-flash-next-iq3_s.coding-noreason.json"))
ap.add_argument("--log", default=str(LOGS / "iq3_s-coding-noreason.engine.log"))
ap.add_argument("--backup-name", default="strata-iq3_s.json.before-final")
ap.add_argument("--drafting", default="dflash2", choices=("dflash2", "mtp", "off"))
ap.add_argument("--draft-conf", default="0.35", help="DFlash2 only; the MTP ignores it")
ap.add_argument("--draft-vocab", default=str(VOCAB), help="DFlash2 draft head subset; MTP has its own")
ap.add_argument("--no-draft-vocab", dest="draft_vocab", action="store_const", const="")
ap.add_argument("--max-context", type=int, default=None, help="leave the config's own when omitted")
ap.add_argument("--kv", default=None, choices=("int8", "q4_0"))
ap.add_argument("--rope-scale", type=float, default=None,
                help="past the trained 262144: writes --rope-scaling yarn and this factor")
ap.add_argument("--reasoning-effort", default="none", choices=("none", "low", "medium", "high"))
a = ap.parse_args()

path = Path(a.config)
copy_path = Path(a.repo_copy)
LOGS.mkdir(parents=True, exist_ok=True)

cfg = json.loads(path.read_text(encoding="utf-8-sig"))
backup = HERE / "backup" / a.backup_name
if not backup.exists():
    shutil.copyfile(path, backup)

user_args: list[str] = []
if a.drafting == "dflash2":
    user_args += ["--draft-conf", a.draft_conf]
    if a.draft_vocab:
        user_args += ["--mtp-draft-vocab", a.draft_vocab]
if a.rope_scale is not None:
    user_args += ["--rope-scaling", "yarn", "--rope-scale", f"{a.rope_scale:g}"]


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


def put(args, flag, value):
    """Set one flag's value in place, or append the pair."""
    if flag in args:
        at = args.index(flag)
        if at + 1 < len(args) and not str(args[at + 1]).startswith("--"):
            args[at + 1] = str(value)
        else:
            args.insert(at + 1, str(value))
    else:
        args.extend([flag, str(value)])
    return args


cfg["drafting"] = a.drafting
cfg["reasoning_effort"] = a.reasoning_effort
cfg["sampling"] = dict(SAMPLING)
cfg["user_args"] = list(user_args)
if isinstance(cfg.get("args"), list):
    args = cfg["args"]
    if a.max_context is not None:
        args = put(args, "--max-context", a.max_context)
    if a.kv is not None:
        args = put(args, "--kv", a.kv)
    if a.rope_scale is None:                       # no stale yarn flags from an earlier call
        kept, i = [], 0
        while i < len(args):
            if args[i] in ROPE_FLAGS:
                i += 2 if i + 1 < len(args) and not str(args[i + 1]).startswith("--") else 1
                continue
            kept.append(args[i])
            i += 1
        args = kept
    cfg["args"] = merge_args(args, user_args)
    cfg["args_written"] = list(cfg["args"])
path.write_text(json.dumps(cfg, indent=1), encoding="utf-8")
# The copy is the run config of the repository's no-reasoning launcher: it follows
# `terminal\current` after an update and writes its engine log into the
# repository-root logs/ folder (gitignored).
copy_cfg = json.loads(json.dumps(cfg))
copy_cfg["cwd"] = r"C:\Users\viktor\AppData\Local\Strata\terminal\current"
copy_cfg["log"] = a.log
copy_path.write_text(json.dumps(copy_cfg, indent=1), encoding="utf-8")
print(f"applied to {path}")
print(f"copy: {copy_path}")
print(f"backup: {backup}")
print(f"drafting={a.drafting} reasoning_effort={a.reasoning_effort} user_args={user_args}")
