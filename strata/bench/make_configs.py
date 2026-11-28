"""Build the A/B run configs for a Strata model from an installed/repository run config.

Usage: python make_configs.py <base-config.json> <out-dir> [--family noreason|reason|nvfp4]

Each variant is a full copy of the base config with the top-level keys the
Strata server reads (drafting, draft_vocab, reasoning_effort, effort_position,
sampling), the person's engine options in user_args, and an engine log in the repository
`logs/` directory (gitignored).

--family noreason (the default) writes the b0..b12 table of the 2026-11-27 report.
--family reason writes the r0..r2 table of the reasoning configuration: the same
engine, context and drafter, sampling/level/effort_position as the variables.
--family nvfp4 writes the v0..v3 table of the NVFP4 model: the MTP's verify window
(--spec 2/4/6) and the start without a drafter. DFlash2 is not an arm: Strata refuses it
for NVFP4 (strata_control/drafting.py, SUPPORTED_FAMILIES and _EXCLUDED_NAME) and the
server falls back to MTP with "DFlash2 is for Qwen3.8-Flash-Next only".
"""
import argparse
import json
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("base")
ap.add_argument("out")
ap.add_argument("--family", choices=("noreason", "reason", "nvfp4"), default="noreason")
a = ap.parse_args()

BASE = Path(a.base)
# Absolute: Strata resolves a config's "log" against the run config's own "cwd", and the repo
# layouts here pass the out-dir relatively (strata/README.md section 7).
OUT = Path(a.out).resolve()
OUT.mkdir(parents=True, exist_ok=True)
# Engine logs of every variant land in the repository-root logs/ folder, which is gitignored.
# The configs themselves stay in the out-dir.
LOGS = Path(__file__).resolve().parents[2] / "logs"
LOGS.mkdir(parents=True, exist_ok=True)

VOCAB_DIR = Path(r"C:\Users\viktor\AppData\Local\Strata\terminal\0.1.69\data")
VOCAB_FILES = {"cjk": "draft_vocab.bin", "en": "draft_vocab_en.bin", "cyrillic": "draft_vocab_cyrillic.bin",
               "fr": "draft_vocab_fr.bin", "latin": "draft_vocab_latin.bin"}

CARD = {"temperature": 0.7, "top_p": 0.8, "top_k": 20, "min_p": 0.0,
        "presence_penalty": 1.5, "frequency_penalty": 0.0, "repetition_penalty": 1.0}
CODING = {"temperature": 0.6, "top_p": 0.8, "top_k": 20, "min_p": 0.0,
          "presence_penalty": 0.0, "frequency_penalty": 0.0, "repetition_penalty": 1.0,
          "seed": 1}
GREEDY = dict(CODING, temperature=0.0)

# id, drafting, draft-conf, vocab, sampling, extra user args
NORESON_VARIANTS = [
    ("b0", "dflash2", "0.35", "cyrillic", CARD, []),
    ("b1", "dflash2", "0.35", "en", CODING, []),
    ("b2", "dflash2", "0.5", "en", CODING, []),
    ("b3", "dflash2", "0.7", "en", CODING, []),
    ("b4", "dflash2", "0.7", "latin", CODING, []),
    ("b5", "dflash2", "0.7", "en", CODING, ["--kv-resident", "49152"]),
    ("b6", "dflash2", "0.7", "en", dict(CODING, top_p=0.95), []),
    ("b7", "off", None, None, GREEDY, []),
    ("b8", "off", None, None, CODING, []),
    ("b9", "dflash2", "0.35", "en", GREEDY, []),
    ("b10", "dflash2", "0.35", "en", GREEDY, ["--prompt-cache", "0"]),
    ("b11", "off", None, None, GREEDY, ["--prompt-cache", "0"]),
    ("b12", "dflash2", "0.35", "en", GREEDY, ["--expert-cache-cpu-order"]),
]

# id, temperature, top_p, effort_position. reasoning_effort stays "high" (the config key takes
# none/low/medium/high only — "xhigh" is refused at startup — and "high" is the template's xhigh;
# a request's own level is what bench.py --effort varies, on one engine start).
# "anthropic_thinking": "on_request" was tried and cannot help here: with a config reasoning_effort
# set, Service.with_shared fills output_config for every Anthropic request that names no thinking,
# so an unasked request thinks at the config level whatever that key says.
REASON_SAMPLING = {"top_k": 20, "min_p": 0.0, "presence_penalty": 0.0, "frequency_penalty": 0.0,
                   "repetition_penalty": 1.0, "seed": 1}
REASON_VARIANTS = [
    ("r0", 1.0, 0.95, "end"),      # the reasoning config itself
    ("r1", 0.6, 0.8, "end"),       # the noreason sampler set: does the card's loop warning bite?
    ("r2", 1.0, 0.95, "start"),    # effort in the system block: what a level switch costs in cache
]

# id, drafting, extra user args. The MTP's verify window is --spec (4 in the installed
# config); a --spec in user_args replaces that pair, it does not add a second one.
NVFP4_VARIANTS = [
    ("v0", "mtp", []),                    # the installed config as it stands
    ("v1", "mtp", ["--spec", "2"]),       # shorter window: fewer drafts, cheaper verification
    ("v2", "mtp", ["--spec", "6"]),       # deeper window: more drafts, lower acceptance likely
    ("v3", "off", []),                    # no drafter at all: the price of speculation
]

base = json.loads(BASE.read_text(encoding="utf-8-sig"))

if a.family == "reason":
    for vid, temperature, top_p, position in REASON_VARIANTS:
        cfg = json.loads(json.dumps(base))
        cfg["reasoning_effort"] = "high"
        cfg["effort_position"] = position
        cfg["sampling"] = dict(REASON_SAMPLING, temperature=temperature, top_p=top_p)
        cfg.pop("draft_vocab", None)          # the file, not the name: --mtp-draft-vocab in user_args
        cfg["log"] = str(LOGS / f"{vid}.engine.log")
        cfg["port"] = 8080
        cfg["host"] = "127.0.0.1"
        path = OUT / f"{vid}.json"
        path.write_text(json.dumps(cfg, indent=1), encoding="utf-8")
        print(f"{path}  reasoning_effort={cfg['reasoning_effort']} effort_position={position} temp={temperature} top_p={top_p}")
elif a.family == "nvfp4":
    for vid, drafting_mode, extra in NVFP4_VARIANTS:
        cfg = json.loads(json.dumps(base))
        cfg["reasoning_effort"] = "none"
        cfg.pop("draft_vocab", None)
        cfg["drafting"] = drafting_mode
        cfg["sampling"] = dict(CODING)
        # the rope flags (if any) come from the base config's user_args and stay
        cfg["user_args"] = list(base.get("user_args") or []) + list(extra)
        cfg["log"] = str(LOGS / f"{vid}.engine.log")
        cfg["port"] = 8080
        cfg["host"] = "127.0.0.1"
        path = OUT / f"{vid}.json"
        path.write_text(json.dumps(cfg, indent=1), encoding="utf-8")
        print(f"{path}  drafting={drafting_mode} user_args={cfg['user_args']}")
else:
    for vid, drafting_mode, conf, vocab, sampling, extra in NORESON_VARIANTS:
        cfg = json.loads(json.dumps(base))
        cfg["reasoning_effort"] = "none"
        cfg.pop("draft_vocab", None)          # the file, not the name: --mtp-draft-vocab in user_args
        cfg["drafting"] = drafting_mode
        cfg["sampling"] = dict(sampling)
        user = []
        if drafting_mode == "dflash2":
            vocab_file = VOCAB_DIR / VOCAB_FILES[vocab]
            if not vocab_file.is_file():
                raise SystemExit(f"missing draft vocabulary: {vocab_file}")
            user = ["--draft-conf", conf, "--mtp-draft-vocab", str(vocab_file)] + list(extra)
        cfg["user_args"] = user
        cfg["log"] = str(LOGS / f"{vid}.engine.log")
        cfg["port"] = 8080
        cfg["host"] = "127.0.0.1"
        path = OUT / f"{vid}.json"
        path.write_text(json.dumps(cfg, indent=1), encoding="utf-8")
        print(f"{path}  drafting={drafting_mode} draft-conf={conf} vocab={vocab} temp={sampling['temperature']} top_p={sampling['top_p']}")
