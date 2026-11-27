"""Check the reasoning API of a running Strata server: levels, thinking blocks, splitting.

Usage: python verify_reasoning_api.py [--base http://127.0.0.1:8080] [--model qwen3.8-flash-next-iq3_s]

Start the server first (strata\\run-iq3_s-coding-reason.bat or `strata serve --profile ...` with
STRATA_ALLOW_THINKING=1 in the environment). Every case sends one non-streamed request with a
short coding question and prints how many reasoning and answer characters came back.

What should hold for the reasoning configuration (config: reasoning_effort xhigh,
effort_position end, anthropic_thinking on_request):
  OpenAI  reasoning_effort off          -> no reasoning, non-empty content
  OpenAI  reasoning_effort low/medium/xhigh -> reasoning present, non-empty content
  OpenAI  chat_template_kwargs enable_thinking false -> no reasoning
  Anthropic thinking enabled (budget)  -> thinking block, text block
  Anthropic thinking disabled          -> no thinking, text
  Anthropic output_config effort low   -> thinking block
  Anthropic no thinking field          -> INFO: with a config reasoning_effort set,
                                          Service.with_shared fills output_config, so it thinks at
                                          the config level ("anthropic_thinking": "on_request"
                                          cannot suppress that)
"""
import argparse
import json
import urllib.error
import urllib.request

QUESTION = "In one paragraph, explain why a Python dict lookup is O(1) on average. Then give a one-line example."
MAX_TOKENS = 2048


def post(url: str, payload: dict, headers: dict, timeout: float) -> tuple[int, dict | str]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST",
                                 headers={"Content-Type": "application/json", **headers})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")


def openai(base: str, model: str, extra: dict, timeout: float) -> dict:
    payload = {"model": model, "max_tokens": MAX_TOKENS,
               "messages": [{"role": "user", "content": QUESTION}], **extra}
    status, data = post(base.rstrip("/") + "/v1/chat/completions", payload, {}, timeout)
    if status != 200 or not isinstance(data, dict):
        return {"status": status, "error": str(data)[:300]}
    message = ((data.get("choices") or [{}])[0].get("message") or {})
    return {"status": status,
            "reasoning_chars": len(message.get("reasoning_content") or message.get("reasoning") or ""),
            "content_chars": len(message.get("content") or ""),
            "finish": (data.get("choices") or [{}])[0].get("finish_reason"),
            "content_preview": (message.get("content") or "")[:120]}


def anthropic(base: str, model: str, extra: dict, timeout: float) -> dict:
    payload = {"model": model, "max_tokens": MAX_TOKENS,
               "messages": [{"role": "user", "content": QUESTION}], **extra}
    status, data = post(base.rstrip("/") + "/v1/messages", payload,
                        {"anthropic-version": "2023-06-01"}, timeout)
    if status != 200 or not isinstance(data, dict):
        return {"status": status, "error": str(data)[:300]}
    thinking = "".join(b.get("thinking") or "" for b in data.get("content") or [] if b.get("type") == "thinking")
    text = "".join(b.get("text") or "" for b in data.get("content") or [] if b.get("type") == "text")
    return {"status": status, "reasoning_chars": len(thinking), "content_chars": len(text),
            "stop": data.get("stop_reason"), "content_preview": text[:120]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8080")
    ap.add_argument("--model", default="qwen3.8-flash-next-iq3_s")
    ap.add_argument("--timeout", type=float, default=900.0)
    a = ap.parse_args()

    cases = [
        ("openai effort=off", "expect no reasoning",
         lambda: openai(a.base, a.model, {"reasoning_effort": "off"}, a.timeout),
         lambda r: r.get("reasoning_chars") == 0 and r.get("content_chars", 0) > 0),
        ("openai effort=low", "expect reasoning",
         lambda: openai(a.base, a.model, {"reasoning_effort": "low"}, a.timeout),
         lambda r: r.get("reasoning_chars", 0) > 0 and r.get("content_chars", 0) > 0),
        ("openai effort=medium", "expect reasoning",
         lambda: openai(a.base, a.model, {"reasoning_effort": "medium"}, a.timeout),
         lambda r: r.get("reasoning_chars", 0) > 0 and r.get("content_chars", 0) > 0),
        ("openai effort=xhigh", "expect reasoning",
         lambda: openai(a.base, a.model, {"reasoning_effort": "xhigh"}, a.timeout),
         lambda r: r.get("reasoning_chars", 0) > 0 and r.get("content_chars", 0) > 0),
        ("openai no effort (config xhigh)", "expect reasoning from the config default",
         lambda: openai(a.base, a.model, {}, a.timeout),
         lambda r: r.get("reasoning_chars", 0) > 0),
        ("openai chat_template_kwargs enable_thinking=false", "expect no reasoning",
         lambda: openai(a.base, a.model, {"chat_template_kwargs": {"enable_thinking": False}}, a.timeout),
         lambda r: r.get("reasoning_chars") == 0 and r.get("content_chars", 0) > 0),
        ("anthropic thinking enabled (budget 31999)", "expect a thinking block",
         lambda: anthropic(a.base, a.model, {"thinking": {"type": "enabled", "budget_tokens": 31999}}, a.timeout),
         lambda r: r.get("reasoning_chars", 0) > 0 and r.get("content_chars", 0) > 0),
        ("anthropic thinking disabled", "expect no thinking",
         lambda: anthropic(a.base, a.model, {"thinking": {"type": "disabled"}}, a.timeout),
         lambda r: r.get("reasoning_chars") == 0 and r.get("content_chars", 0) > 0),
        ("anthropic output_config effort=low", "expect a thinking block",
         lambda: anthropic(a.base, a.model, {"output_config": {"effort": "low"}}, a.timeout),
         lambda r: r.get("reasoning_chars", 0) > 0),
        ("anthropic no thinking field", "INFO only: expects the config default level",
         lambda: anthropic(a.base, a.model, {}, a.timeout),
         None),
    ]

    failed = 0
    for name, note, call, check in cases:
        result = call()
        ok = None if check is None else bool(check(result))
        if ok is False:
            failed += 1
        verdict = "INFO" if ok is None else ("PASS" if ok else "FAIL")
        print(f"[{verdict}] {name} ({note})")
        print(f"        {json.dumps(result, ensure_ascii=False)}", flush=True)

    print(f"{len(cases) - sum(1 for c in cases if c[3] is None)} checked, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
