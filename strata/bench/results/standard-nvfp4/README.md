# Strata standard benchmark: NVIDIA GeForce RTX 5060 Ti, NVIDIA GeForce RTX 5060 Ti

Protocol `strata-qwen38-thinking-v1-draft.1` (draft), run `20261128T073500Z-b999ccc4`, started 2026-11-28T07:35:00Z. **Status: complete.**

Written by `strata bench run`. The machine-readable result is [results.json](results.json); every request, its raw usage and timings and the client event offsets are in [outputs.jsonl](outputs.jsonl).

## Hardware and software

- GPU: NVIDIA GeForce RTX 5060 Ti (15.9 GiB dedicated); NVIDIA GeForce RTX 5060 Ti (15.9 GiB dedicated)
- CPU: AMD Ryzen 9 9950X 16-Core Processor; RAM: 61.7 GiB
- Storage of the model files: ssd Micron_7450_MTFDKBA800TFS (nvme)
- OS: Windows 10.0.22621; drivers: gpu-driver 617.42; runtime: cuda 13.4
- Strata commit: `b28ca95e3e6847f2d5e317994f253b66716deeaa`; engine 0.1.69; release build
- Background work: not measured

## Model and configuration

- Model: qwen3.8-flash-next-nvfp4-nvfp4; quantization NVFP4; revision not measured; source revision not measured
- Files: `expert-profile.bin` `8f59b4aa8873209d...`; `ple-fp8.gguf` `37f89b8ce5a34259...`; `qwen-nvfp4-gptq-dense.gguf` `abdf74336b53d8f7...`; `token-embd-bf16.gguf` `386203af9070c7b4...`
- Track: **custom** (no notes given by the operator)
- Context 524288 tokens; server capacity 1 slot(s)
- Sampling: temperature 1.0, top_p 0.95, top_k 20, min_p 0.0, presence_penalty 0.0, repetition_penalty 1.0, reasoning_effort xhigh; thinking on, preserved
- Engine options: `config.json`; chat template: `provenance/chat_template.jinja`

## Method

The frozen requests of `bench/prompts/standard-v1` (corpus `e75eff8b9feea04f...`) were sent over loopback HTTP, streaming, one at a time, in this order: 1 warm-up (excluded), 3 repetitions of the short, 4K and 16K prompts, and the twelve sanity checks. Prompt and decode speed are the engine's own `timings`; time to first token is the client's monotonic clock from dispatch to the first nonempty reasoning, answer or tool-call delta. No request was retried. Time after the model loaded: 8 min 46 s.

## Results

| Case | Prompt tok/s | Decode tok/s | TTFT s | First answer s | Total s | Capped |
| --- | --- | --- | --- | --- | --- | --- |
| short | n/a | 16.5 (14.8-16.9) n=3 | 2.95 (2.58-3.11) n=3 | 9.41 (6.92-10.61) n=3 | 30.8 (23.2-31.7) n=3 | 0/3 |
| prompt-4k | 460.1 (456.2-461.5) n=3 | 16.1 (15.7-16.1) n=3 | 9.02 (9.00-9.09) n=3 | 23.14 (23.00-23.28) n=2 | 40.7 (40.7-41.2) n=3 | 2/3 |
| prompt-16k | 877.5 (871.5-882.0) n=3 | 15.9 (15.3-16.1) n=3 | 18.77 (18.64-18.94) n=3 | 37.45 (37.45-37.45) n=1 | 51.0 (50.5-52.1) n=3 | 3/3 |

Cells are median (min-max) n=samples. Short is a prompt of about 80 tokens: its prompt rate is dominated by the fixed cost of a request, so it is not shown; read prompt speed from prompt-4k and prompt-16k. Capped = requests that reached the 512-token cap, reasoning and answer together. A capped request's total time is the time to the cap, not to an answer, and it has no first-answer time when it was still reasoning.

| Phase | Planned | Completed | Truncated | Failed | Skipped |
| --- | ---: | ---: | ---: | ---: | ---: |
| warmup | 1 | 0 | 1 | 0 | 0 |
| performance | 9 | 4 | 5 | 0 | 0 |
| sanity | 12 | 12 | 0 | 0 | 0 |
| concurrency | 0 | 0 | 0 | 0 | 0 |

Sanity checks: **11 of 12**.

| Case | Result | Reason |
| --- | --- | --- |
| I1 | pass | the expected JSON value |
| I2 | pass | the expected JSON value |
| I3 | pass | the expected JSON value |
| I4 | pass | the exact expected text |
| R1 | pass | the exact expected text |
| R2 | pass | the exact expected text |
| R3 | pass | the exact expected text |
| R4 | pass | the expected JSON value |
| T1 | fail | expected one structured tool call, got 0 |
| T2 | pass | the expected tool call |
| T3 | pass | the expected tool call |
| T4 | pass | the expected tool call |

## Failures, exclusions and limitations

- No request failed.
- Excluded from speed summaries: performance-prompt-16k-r2: first_answer_s is not available for this request
- Excluded from speed summaries: performance-prompt-16k-r3: first_answer_s is not available for this request
- Excluded from speed summaries: performance-prompt-4k-r1: first_answer_s is not available for this request
- Prompt-prefix reuse is the shared template prefix only; the cache was not emptied between requests, and the expert cache stays warm and evolves. These are not cold-model measurements.
- Output caps include reasoning; a request that reaches its cap is `truncated` and fails its sanity check.
- The runner cannot see other programs on the machine, the repeat-stop and loop-recovery switches of the server, or the quantization repository's revision; see `missing` in results.json for every value it could not read.
- The server had answered 53 request(s) before this run.
