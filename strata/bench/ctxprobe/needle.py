"""Needle in a haystack for a running Strata server: does it still retrieve a fact deep in a long prompt?

Usage:
  python -I strata/bench/ctxprobe/needle.py [--url http://127.0.0.1:8080] [--lines 5000]
                                          [--depth 0.5] [--max-tokens 16] [--needle TEXT]

The prompt is filler lines from bench/prompts.json (`prefill`) with one unique sentence
put at `--depth` of the way in; the question asks for that sentence's code. Reports the
token count the server saw, the wall time (prefill dominates), and whether the code came
back. Used to prove the contexts past the trained 262144 (yarn) still retrieve; it is not
part of bench.py's fixed workload, so results stay comparable across configs.
"""
import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent
MODEL = "qwen3.8-flash-next-nvfp4-nvfp4"
NEEDLE = "Note for the reader: the vault code for the north terminal is 7-QX-4412."
QUESTION = "\nWhat is the vault code for the north terminal? Answer with the code only."


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8080")
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--lines", type=int, default=5000)
    ap.add_argument("--depth", type=float, default=0.5, help="where the needle sits, 0..1")
    ap.add_argument("--max-tokens", type=int, default=16)
    ap.add_argument("--needle", default=NEEDLE)
    ap.add_argument("--code", default="7-QX-4412", help="what the answer must contain")
    a = ap.parse_args()

    spec = json.loads((BENCH / "prompts.json").read_text(encoding="utf-8"))["prefill"]
    at = int(a.lines * a.depth)
    parts = []
    for n in range(1, a.lines + 1):
        if n == at:
            parts.append(a.needle + "\n\n")
        parts.append(spec["line"].format(n=n, m=n * 3 + 1))
    user = spec["user_prefix"] + "".join(parts) + QUESTION
    payload = {"model": a.model, "messages": [{"role": "user", "content": user}],
               "max_tokens": a.max_tokens, "stream": False}
    req = urllib.request.Request(a.url.rstrip("/") + "/v1/chat/completions",
                                 data=json.dumps(payload).encode("utf-8"), method="POST",
                                 headers={"Content-Type": "application/json"})
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=1800) as resp:
        obj = json.loads(resp.read().decode("utf-8"))
    wall = time.perf_counter() - t0
    msg = (obj.get("choices") or [{}])[0].get("message") or {}
    answer = (msg.get("content") or "").strip()
    usage = obj.get("usage") or {}
    row = {"prompt_tokens": usage.get("prompt_tokens"), "wall_s": round(wall, 1),
           "prefill_tps": round(usage.get("prompt_tokens", 0) / wall, 1) if wall else None,
           "answer": answer[:200], "found": a.code in answer}
    print(json.dumps(row, ensure_ascii=False))
    return 0 if row["found"] else 1


if __name__ == "__main__":
    sys.exit(main())
