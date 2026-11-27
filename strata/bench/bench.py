"""Streaming benchmark for a Strata server (OpenAI-compatible /v1/chat/completions).

Usage:
  python -I bench.py --variant b1 --out-dir results [--url http://127.0.0.1:8080] [--model NAME]

Measures, per case: time to first token, decode tokens/s (first to last content
chunk), prompt/prefill tokens/s, reasoning output, and the exact answer hash for
a repeatability check. Writes one JSON file per variant.
"""
import argparse
import hashlib
import json
import statistics
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent


def build_user_text(spec: dict) -> str:
    if "user" in spec:
        return spec["user"]
    lines = []
    for n in range(1, spec["lines"] + 1):
        lines.append(spec["line"].format(n=n, m=n * 3 + 1))
    return spec["user_prefix"] + "".join(lines) + spec["question"]


def gpu_memory() -> list[dict]:
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,memory.used,memory.total,utilization.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=30, check=True).stdout
    except Exception as exc:                                  # noqa: BLE001
        return [{"error": str(exc)}]
    rows = []
    for line in out.strip().splitlines():
        idx, used, total, util = [x.strip() for x in line.split(",")]
        rows.append({"index": int(idx), "used_mib": int(used), "total_mib": int(total), "util_pct": int(util)})
    return rows


def stream_request(url: str, payload: dict, timeout: float) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST",
                                 headers={"Content-Type": "application/json", "Accept": "text/event-stream"})
    content_parts, reasoning_parts = [], []
    chunks_with_content = 0
    chunks_with_reasoning = 0
    t0 = time.perf_counter()
    t_first = None          # first answer (content) delta: ttft_s, as in the no-reasoning runs
    t_first_any = None      # first delta of any kind (reasoning or content): where prefill really ends
    t_last = None           # last content delta
    t_last_any = None       # last delta of any kind
    usage = None
    with urllib.request.urlopen(req, timeout=timeout) as resp:
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
                delta = choice.get("delta") or {}
                piece = delta.get("content")
                rpiece = delta.get("reasoning_content") or delta.get("reasoning")
                if piece or rpiece:
                    now = time.perf_counter()
                    if t_first_any is None:
                        t_first_any = now
                    t_last_any = now
                if piece:
                    if t_first is None:
                        t_first = time.perf_counter()
                    t_last = time.perf_counter()
                    content_parts.append(piece)
                    chunks_with_content += 1
                if rpiece:
                    reasoning_parts.append(rpiece)
                    chunks_with_reasoning += 1
            err = obj.get("error")
            if err:
                raise RuntimeError(f"server error: {err}")
    t_end = time.perf_counter()
    text = "".join(content_parts)
    reasoning = "".join(reasoning_parts)
    completion = None
    if usage:
        completion = usage.get("completion_tokens")
    if completion is None:
        completion = chunks_with_content
    prompt_tokens = (usage or {}).get("prompt_tokens")
    cached = ((usage or {}).get("prompt_tokens_details") or {}).get("cached_tokens")
    decode_s = (t_last - t_first) if (t_first is not None and t_last is not None) else 0.0
    decode_tps = ((completion - 1) / decode_s) if (completion and completion > 1 and decode_s > 0) else None
    span_any = (t_last_any - t_first_any) if (t_first_any is not None and t_last_any is not None) else 0.0
    decode_tps_all = ((completion - 1) / span_any) if (completion and completion > 1 and span_any > 0) else None
    ttft = (t_first - t0) if t_first is not None else None
    ttft_any = (t_first_any - t0) if t_first_any is not None else None
    # prefill ends at the first token of either kind: with thinking on the answer starts much later
    pf_ttft = ttft_any if ttft_any is not None else ttft
    prefill_tps = (prompt_tokens / pf_ttft) if (prompt_tokens and pf_ttft and pf_ttft > 0) else None
    return {
        "ttft_s": round(ttft, 3) if ttft is not None else None,
        "ttft_any_s": round(ttft_any, 3) if ttft_any is not None else None,
        "wall_s": round(t_end - t0, 3),
        "prompt_tokens": prompt_tokens,
        "cached_tokens": cached,
        "completion_tokens": completion,
        "decode_tps": round(decode_tps, 1) if decode_tps else None,
        "decode_tps_all": round(decode_tps_all, 1) if decode_tps_all else None,
        "prefill_tps": round(prefill_tps, 1) if prefill_tps else None,
        "reasoning_chars": len(reasoning),
        "reasoning_chunks": chunks_with_reasoning,
        "content_chars": len(text),
        "content_empty": not text.strip(),
        "content_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "content_preview": text[:400],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", required=True)
    ap.add_argument("--url", default="http://127.0.0.1:8080")
    ap.add_argument("--model", default="qwen3.8-flash-next-iq3_s")
    ap.add_argument("--out-dir", default=str(HERE / "results"))
    ap.add_argument("--config", default="")
    ap.add_argument("--timeout", type=float, default=900.0)
    ap.add_argument("--effort", default="",
                    help="reasoning_effort sent with every request (off/low/medium/high/xhigh); empty: send none, "
                         "the run config's reasoning_effort governs (the no-reasoning runs)")
    ap.add_argument("--max-tokens-short", type=int, default=0,
                    help="override max_tokens of the short cases (thinking spends output: 2048 for reasoning runs)")
    ap.add_argument("--max-tokens-depth", type=int, default=0,
                    help="override max_tokens of the depth case (thinking runs: 512)")
    ap.add_argument("--max-tokens-prefill", type=int, default=0,
                    help="override max_tokens of the prefill case (thinking runs: 256)")
    a = ap.parse_args()

    prompts = json.loads((HERE / "prompts.json").read_text(encoding="utf-8"))
    endpoint = a.url.rstrip("/") + "/v1/chat/completions"
    out = {"variant": a.variant, "model": a.model, "url": a.url, "config": a.config,
           "effort": a.effort or None,
           "max_tokens_override": {"short": a.max_tokens_short, "depth": a.max_tokens_depth,
                                   "prefill": a.max_tokens_prefill},
           "started": datetime.now(timezone.utc).isoformat(), "cases": []}

    if a.config and Path(a.config).is_file():
        cfg = json.loads(Path(a.config).read_text(encoding="utf-8-sig"))
        out["config_sha256"] = hashlib.sha256(Path(a.config).read_bytes()).hexdigest()
        out["drafting"] = cfg.get("drafting")
        out["draft_vocab"] = cfg.get("draft_vocab")
        out["sampling"] = cfg.get("sampling")
        out["reasoning_effort"] = cfg.get("reasoning_effort")
        out["effort_position"] = cfg.get("effort_position")
        out["user_args"] = cfg.get("user_args")
        out["args"] = cfg.get("args")

    out["vram_before"] = gpu_memory()

    def ask(case_id: str, user_text: str, max_tokens: int, temperature: float | None = None,
            seed: int | None = None, system: str | None = None) -> dict:
        messages = ([{"role": "system", "content": system}] if system else []) + \
                   [{"role": "user", "content": user_text}]
        payload = {"model": a.model, "messages": messages, "max_tokens": max_tokens,
                   "temperature": temperature, "seed": seed,
                   "reasoning_effort": a.effort or None,
                   "stream": True, "stream_options": {"include_usage": True}}
        payload = {k: v for k, v in payload.items() if v is not None}
        metrics = stream_request(endpoint, payload, a.timeout)
        metrics.update({"case": case_id, "max_tokens": max_tokens, "effort": a.effort or None})
        out["cases"].append(metrics)
        print(f"{a.variant} {case_id}: ttft_any={metrics['ttft_any_s']}s ttft_content={metrics['ttft_s']}s "
              f"decode={metrics['decode_tps']} decode_all={metrics['decode_tps_all']} t/s "
              f"prefill={metrics['prefill_tps']} t/s tokens={metrics['completion_tokens']} "
              f"reasoning={metrics['reasoning_chars']} chars content={metrics['content_chars']} chars", flush=True)
        return metrics

    short_max = a.max_tokens_short or 0
    depth_max = a.max_tokens_depth or 0
    prefill_max = a.max_tokens_prefill or 0

    # sampling for the measured workload comes from the run config; send nothing to keep it that way
    warm = ask("warmup", "Reply with exactly: READY", 8)
    print(f"{a.variant} warmup reasoning chars: {warm['reasoning_chars']}", flush=True)

    short_hashes: dict[str, list[str]] = {}
    for spec in prompts["short"]:
        for rep in (1, 2):
            m = ask(f"{spec['id']}#{rep}", build_user_text(spec), short_max or spec["max_tokens"],
                    system=spec.get("system"))
            short_hashes.setdefault(spec["id"], []).append(m["content_sha256"])

    depth = prompts["depth"]
    ask(depth["id"], build_user_text(depth), depth_max or depth["max_tokens"], system=depth.get("system"))

    pf = prompts["prefill"]
    ask(pf["id"], build_user_text(pf), prefill_max or pf["max_tokens"], system=pf.get("system"))

    out["vram_after"] = gpu_memory()
    out["repeatable"] = {k: len(set(v)) == 1 for k, v in short_hashes.items()}
    short = [c for c in out["cases"] if "#" in c["case"] and c.get("decode_tps")]
    short_all = [c for c in out["cases"] if "#" in c["case"] and c.get("decode_tps_all")]
    out["summary"] = {
        "short_decode_median_tps": round(statistics.median(c["decode_tps"] for c in short), 1) if short else None,
        "short_decode_median_tps_all": round(statistics.median(c["decode_tps_all"] for c in short_all), 1) if short_all else None,
        "repeatable_all": all(out["repeatable"].values()) if out["repeatable"] else None,
        "reasoning_chars_total": sum(c["reasoning_chars"] for c in out["cases"]),
        "reasoning_cases": sum(1 for c in out["cases"] if c["reasoning_chars"] > 0),
        "answers_empty": sum(1 for c in out["cases"] if c.get("content_empty")),
        "prefill_90k_tps": next((c["prefill_tps"] for c in out["cases"] if c["case"] == "prefill90k"), None),
        "depth16k_decode_tps": next((c["decode_tps"] for c in out["cases"] if c["case"] == "depth16k"), None),
        "depth16k_decode_tps_all": next((c["decode_tps_all"] for c in out["cases"] if c["case"] == "depth16k"), None),
    }
    out["finished"] = datetime.now(timezone.utc).isoformat()
    dest = Path(a.out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = dest / f"{a.variant}-{stamp}.json"
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {path}", flush=True)
    print(json.dumps(out["summary"], ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
