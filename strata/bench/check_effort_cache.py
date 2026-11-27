"""Does changing the reasoning level keep the prompt cache? (the `effort_position` question)

Usage: python check_effort_cache.py [--base http://127.0.0.1:8080] [--model qwen3.8-flash-next-iq3_s]

Sends the same long prompt twice: first at the config's default level (xhigh), then at low, and
prints the second request's `cached_tokens` / TTFT. With `effort_position: "end"` the two prompts
share their prefix (the level goes in a tail system turn before the answer), so the engine reuses
the conversation; with "start" the level sits in the system block and the prefix changes, so almost
nothing is reused. Run it on both server configs and compare. The first request on a fresh server is
a cold prefill; run the script twice and read the second run.
"""
import argparse
import json
import time
import urllib.request

FILLER = ("def util_{n}(x: int) -> int:\n    return x * {n} + {m}\n\n")


def prompt_text(lines: int = 400) -> str:
    body = "".join(FILLER.format(n=n, m=n * 3 + 1) for n in range(1, lines + 1))
    # a unique tail keeps this text out of the benchmark prompts' cached prefixes
    return ("Read this code. What does util_137 return for x=2? Answer with one expression only.\n\n"
            + body + "\n(check-effort-cache marker 7f31)")


def ask(base: str, model: str, effort: str, timeout: float) -> dict:
    body = {"model": model, "max_tokens": 64, "reasoning_effort": effort,
            "messages": [{"role": "user", "content": prompt_text()}]}
    req = urllib.request.Request(base.rstrip("/") + "/v1/chat/completions",
                                 data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    t = time.perf_counter()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode())
    usage = data.get("usage") or {}
    return {"effort": effort, "wall_s": round(time.perf_counter() - t, 3),
            "prompt_tokens": usage.get("prompt_tokens"),
            "cached_tokens": ((usage.get("prompt_tokens_details") or {}).get("cached_tokens")),
            "completion_tokens": usage.get("completion_tokens")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8080")
    ap.add_argument("--model", default="qwen3.8-flash-next-iq3_s")
    ap.add_argument("--timeout", type=float, default=900.0)
    a = ap.parse_args()
    for effort in ("xhigh", "low", "xhigh"):
        row = ask(a.base, a.model, effort, a.timeout)
        print(json.dumps(row), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
