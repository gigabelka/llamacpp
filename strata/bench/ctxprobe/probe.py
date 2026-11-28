"""Context ladder for the NVFP4 configuration: one probe run config, rewritten per step.

Usage (from the repository root):
  python -I strata/bench/ctxprobe/probe.py write --ctx 262144 [--kv q4_0] [--rope-scale 1.5]
  python -I strata/bench/ctxprobe/probe.py start [--profile nvfp4-ctx-probe]
  python -I strata/bench/ctxprobe/probe.py log
  python -I strata/bench/ctxprobe/probe.py smoke [--max-tokens 32]
  python -I strata/bench/ctxprobe/probe.py stop

`write` copies the installed run config of the NVFP4 model and changes only what the
ladder varies: `--max-context`, `--kv`, the yarn flags above the trained 262144, and the
engine log path (the repository-root logs/ folder, gitignored). The saved profile
(`strata profile create nvfp4-ctx-probe --from-config strata/bench/ctxprobe/ctx.json`,
once) points at the file, not at its bytes, so every `start` uses the last `write`.

`log` prints the lines that decide whether the context fits: the slot counts per card,
the free VRAM after the load, how many experts are read from the files, and the ready
line with the served context. `smoke` sends the bench depth prompt (16k) and checks the
answer, so a start that fits the cards but cannot serve a long prompt is caught here.
"""
import argparse
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
BENCH = HERE.parent
REPO = BENCH.parents[1]
LOGS = REPO / "logs"
PROBE = HERE / "ctx.json"
INSTALLED = Path(r"C:\Users\viktor\AppData\Local\Strata\install\strata-nvfp4-nvfp4.json")
STRATA = Path(r"C:\Users\viktor\AppData\Local\Strata\terminal\current\bin\strata.cmd")
PROFILE = "nvfp4-ctx-probe"
MODEL = "qwen3.8-flash-next-nvfp4-nvfp4"
URL = "http://127.0.0.1:8080"
TRAINED = 262144

# The ENGINE flags the ladder varies; everything else stays what setup wrote.
ROPE_FLAGS = ("--rope-scaling", "--rope-scale")


def put(args: list, flag: str, value) -> list:
    """The engine args with one flag's value set (in place when the flag is there, else appended)."""
    if flag in args:
        at = args.index(flag)
        if at + 1 < len(args) and not str(args[at + 1]).startswith("--"):
            args[at + 1] = str(value)
        else:
            args.insert(at + 1, str(value))
    else:
        args.extend([flag, str(value)])
    return args


def drop(args: list, flags) -> list:
    """The engine args without these flags and their values."""
    kept, i = [], 0
    while i < len(args):
        if args[i] in flags:
            i += 2 if i + 1 < len(args) and not str(args[i + 1]).startswith("--") else 1
            continue
        kept.append(args[i])
        i += 1
    return kept


def write_config(ctx: int, kv: str, rope_scale: float | None) -> dict:
    LOGS.mkdir(parents=True, exist_ok=True)
    cfg = json.loads(INSTALLED.read_text(encoding="utf-8-sig"))
    args = list(cfg.get("args") or [])
    put(args, "--max-context", ctx)
    put(args, "--kv", kv)
    args = drop(args, ROPE_FLAGS)
    if rope_scale is not None:
        args = put(args, "--rope-scaling", "yarn")
        put(args, "--rope-scale", f"{rope_scale:g}")
    cfg["args"] = args
    cfg["args_written"] = list(args)
    cfg["log"] = str(LOGS / f"nvfp4-ctx-{ctx}-{kv}.engine.log")
    cfg["port"] = 8080
    cfg["host"] = "127.0.0.1"
    PROBE.write_text(json.dumps(cfg, indent=1), encoding="utf-8")
    return cfg


def strata(*argv: str) -> int:
    """strata.cmd through cmd.exe (a .bat is not an executable image Windows can create directly)."""
    return subprocess.call(["cmd", "/c", str(STRATA), *argv], cwd=str(REPO))


def cfg_log() -> Path:
    cfg = json.loads(PROBE.read_text(encoding="utf-8-sig"))
    return Path(cfg["log"])


def show_log() -> None:
    path = cfg_log()
    if not path.is_file():
        print(f"no engine log yet: {path}")
        return
    print(f"--- {path}")
    keys = ("expert cache auto", "expert cache", "of VRAM free", "read from the files",
            "resident RAM mode", "RAM budget", "ready:", "context", "error", "ERROR", "failed",
            "rope", "yarn", "layer split")
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if any(k in line for k in keys):
            print(line)


def build_user_text(spec: dict) -> str:
    """bench.py's prompt builder, kept identical so the smoke reads the same 16k prompt."""
    lines = [spec["line"].format(n=n, m=n * 3 + 1) for n in range(1, spec["lines"] + 1)]
    return spec["user_prefix"] + "".join(lines) + spec["question"]


def ask(user_text: str, system: str, max_tokens: int) -> dict:
    """One streamed chat completion: the timing bench.py records, for the ladder's price column."""
    payload = {"model": MODEL,
               "messages": ([{"role": "system", "content": system}] if system else []) +
                           [{"role": "user", "content": user_text}],
               "max_tokens": max_tokens, "stream": True, "stream_options": {"include_usage": True}}
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(URL.rstrip("/") + "/v1/chat/completions", data=body, method="POST",
                                 headers={"Content-Type": "application/json", "Accept": "text/event-stream"})
    t0 = time.perf_counter()
    first = last = None
    text, usage = [], None
    with urllib.request.urlopen(req, timeout=900) as resp:
        for raw in resp:
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            try:
                obj = json.loads(data)
            except ValueError:
                continue
            if isinstance(obj.get("usage"), dict):
                usage = obj["usage"]
            for choice in obj.get("choices") or []:
                piece = (choice.get("delta") or {}).get("content")
                if piece:
                    now = time.perf_counter()
                    first = first or now
                    last = now
                    text.append(piece)
            if obj.get("error"):
                raise RuntimeError(obj["error"])
    answer = "".join(text).strip()
    span = (last - first) if first and last and last > first else 0.0
    completion = (usage or {}).get("completion_tokens") or len(text)
    return {
        "prompt_tokens": (usage or {}).get("prompt_tokens"),
        "completion_tokens": completion,
        "ttft_s": round(first - t0, 2) if first else None,
        "decode_tps": round((completion - 1) / span, 1) if completion > 1 and span > 0 else None,
        "content_chars": len(answer),
        "preview": answer[:120],
    }


def smoke(max_tokens: int) -> int:
    prompts = json.loads((BENCH / "prompts.json").read_text(encoding="utf-8"))
    depth = prompts["depth"]
    row = ask(build_user_text(depth), depth.get("system", ""), max_tokens)
    print(json.dumps(row, ensure_ascii=False))
    return 0 if row["content_chars"] else 1


def short(max_tokens: int) -> int:
    """The first short coding prompt: the ladder's decode price, comparable across rungs."""
    prompts = json.loads((BENCH / "prompts.json").read_text(encoding="utf-8"))
    spec = prompts["short"][0]
    row = ask(spec["user"], spec.get("system", ""), max_tokens or spec["max_tokens"])
    row["case"] = spec["id"]
    print(json.dumps(row, ensure_ascii=False))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("write", help="rewrite the probe config for one rung")
    w.add_argument("--ctx", type=int, required=True)
    w.add_argument("--kv", default="int8", choices=("int8", "q4_0", "k8v4"))
    w.add_argument("--rope-scale", type=float, default=None,
                   help="yarn factor; required above the trained 262144 (ctx / 262144)")
    s = sub.add_parser("start", help="runtime start of the saved probe profile")
    s.add_argument("--profile", default=PROFILE)
    s.add_argument("--wait", type=int, default=900)
    sub.add_parser("status", help="runtime status of the probe profile")
    st = sub.add_parser("stop", help="runtime stop of the probe profile")
    st.add_argument("--profile", default=PROFILE)
    sm = sub.add_parser("smoke", help="one 16k depth request against the running server")
    sm.add_argument("--max-tokens", type=int, default=32)
    sh = sub.add_parser("short", help="one short coding prompt: the decode price of this rung")
    sh.add_argument("--max-tokens", type=int, default=512)
    sub.add_parser("log", help="the engine log lines that decide the fit")
    sub.add_parser("show", help="the probe config as written")
    a = ap.parse_args()

    if a.cmd == "write":
        if a.ctx > TRAINED and a.rope_scale is None:
            print(f"refused: {a.ctx} is past the trained {TRAINED}; pass --rope-scale (ctx / {TRAINED})")
            return 2
        if a.ctx <= TRAINED and a.rope_scale is not None:
            print(f"note: {a.ctx} is inside the trained {TRAINED}; the yarn flags are still written")
        cfg = write_config(a.ctx, a.kv, a.rope_scale)
        print(f"{PROBE}  max-context={a.ctx} kv={a.kv} rope-scale={a.rope_scale}  log={cfg['log']}")
        return 0
    if a.cmd == "start":
        return strata("runtime", "start", "--profile", a.profile, "--wait", str(a.wait))
    if a.cmd == "status":
        return strata("runtime", "status", "--profile", PROFILE)
    if a.cmd == "stop":
        return strata("runtime", "stop", "--profile", a.profile)
    if a.cmd == "smoke":
        return smoke(a.max_tokens)
    if a.cmd == "short":
        return short(a.max_tokens)
    if a.cmd == "log":
        show_log()
        return 0
    if a.cmd == "show":
        print(PROBE.read_text(encoding="utf-8"))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
