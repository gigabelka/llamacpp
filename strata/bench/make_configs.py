"""Build the A/B run configs for Qwen3.8-Flash-Next IQ3_S from the installed run config.

Usage: python make_configs.py <installed-config.json> <out-dir>

Each variant is a full copy of the installed config with the top-level keys the
Strata server reads (drafting, draft_vocab, reasoning_effort, sampling), the
person's engine options in user_args, and its own engine log.
"""
import json
import sys
from pathlib import Path

BASE = Path(sys.argv[1])
OUT = Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)

VOCAB_DIR = Path(r"C:\Users\viktor\AppData\Local\Strata\terminal\0.1.69\data")
VOCAB_FILES = {"cjk": "draft_vocab.bin", "en": "draft_vocab_en.bin", "cyrillic": "draft_vocab_cyrillic.bin",
               "fr": "draft_vocab_fr.bin", "latin": "draft_vocab_latin.bin"}

COMMON = {
    "reasoning_effort": "none",
}

CARD = {"temperature": 0.7, "top_p": 0.8, "top_k": 20, "min_p": 0.0,
        "presence_penalty": 1.5, "frequency_penalty": 0.0, "repetition_penalty": 1.0}
CODING = {"temperature": 0.6, "top_p": 0.8, "top_k": 20, "min_p": 0.0,
          "presence_penalty": 0.0, "frequency_penalty": 0.0, "repetition_penalty": 1.0,
          "seed": 1}
GREEDY = dict(CODING, temperature=0.0)

VARIANTS = [
    # id, drafting, draft-conf, vocab, sampling, extra user args
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

base = json.loads(BASE.read_text(encoding="utf-8-sig"))
for vid, drafting_mode, conf, vocab, sampling, extra in VARIANTS:
    cfg = json.loads(json.dumps(base))
    cfg.update(COMMON)
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
    cfg["log"] = str(OUT / f"{vid}.engine.log")
    cfg["port"] = 8080
    cfg["host"] = "127.0.0.1"
    path = OUT / f"{vid}.json"
    path.write_text(json.dumps(cfg, indent=1), encoding="utf-8")
    print(f"{path}  drafting={drafting_mode} draft-conf={conf} vocab={vocab} temp={sampling['temperature']} top_p={sampling['top_p']}")
