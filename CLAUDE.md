# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository. All answers must be in Russian.

## What this repo is

This is **not** a source tree for llama.cpp. It is a collection of Windows launch
scripts and configuration for running a pre-built `llama-server.exe` locally,
plus two long-form design docs (in Russian):

- `README.md` — feature/architecture overview and test-bench spec.
- `CALCULATE.md` — the VRAM-budget methodology: formulas for weights / KV cache /
  recurrent state / compute buffer, reverse problems (max `-ngl`, max `-c`,
  min KV quant), and a fully calibrated worked example for `Qwen3.8-27B` on
  RTX 5060 Ti 16 GB cards. Treat this as the authoritative reference when changing
  any `-c`, `-ts`, `-ub`, `-ctk`, or `-ctv` value.
- `*.jinja` — chat templates passed to the server via `--chat-template-file`.
- `cuda13/*.bat` — the launch scripts.

There is no build, no test suite, no linter. "Running" the project means
executing one of the `.bat` files (see below).

## Layout of the launch scripts

All scripts live in `cuda13/` and point at the CUDA 13.x build
(`c:\Llamacpp\cuda13\llama-server.exe`). An earlier `cuda12/` set (the same
configs against a CUDA 12.x build) has been removed — `README.md` still describes
it, so trust this file and the actual tree instead.

Scripts differ by model file, card count, and the VRAM-sensitive knobs:

| script                           | model (GGUF)                            | GPUs  | `-c`   | `-ts`    | `-ctk`/`-ctv` | `-b`/`-ub` |
| -------------------------------- | --------------------------------------- | ----- | ------ | -------- | ------------- | ---------- |
| `qwen-qwen38-27-4km.bat`         | lmstudio-community Q4_K_M               | 0,1   | 262144 | 17,13    | q8_0 / q8_0   | 1024 / 256 |
| `qwen-qwen38-27-6k.bat`          | lmstudio-community Q6_K                 | 0,1,2 | 262144 | 11,10,9  | q8_0 / q8_0   | 2048 / 512 |
| `unsloth-qwen38-27-3kxl.bat`     | unsloth UD-Q3_K_XL                      | 0,1   | 229376 | 17,13    | f16 / f16     | 1024 / 256 |
| `unsloth-qwen38-27-4km.bat`      | unsloth UD-Q4_K_M                       | 0,1   | 180224 | 17,13    | f16 / f16     | 1024 / 256 |
| `unsloth-qwen38-27-5km.bat`      | unsloth UD-Q5_K_M                       | 0,1   | 262144 | 16,14    | q8_0 / q4_0   | 1024 / 256 |
| `unsloth-qwen38-27-6km.bat`      | unsloth UD-Q6_K_M                       | 0,1   | 65336  | 17,13    | f16 / f16     | 1024 / 256 |
| `unsloth-qwen38-27-6km-test.bat` | unsloth UD-Q6_K_M                       | 0,1,2 | 262144 | 12,11,7  | q8_0 / q8_0   | 2048 / 256 |
| `ornith-ornith15-35-8k.bat`      | ornith-ai Ornith-1.5-35B Q8_0           | 0,1,2 | 262144 | 14,13,13 | q8_0 / q8_0   | 2048 / 256 |
| `davidau-qwen38-27-turbo-6k.bat` | DavidAU TurboFCF NEO-CODER-MAX-MTP Q6_K | 0,1,2 | 262144 | 12,11,7  | q8_0 / q8_0   | 2048 / 256 |

Card count is set per script via `CUDA_VISIBLE_DEVICES` (with
`CUDA_DEVICE_ORDER=PCI_BUS_ID`), so the number of `-ts` fields must match it.
Everything else — `-ngl 99`, `-sm layer`, `-fa on`, `-kvu`, `-np 1`, `-n -1`,
`--cache-reuse 256`, `--no-mmproj`, `--spec-type draft-mtp`, `-t 16`,
`--threads-batch 16`, port 1234 — is identical across scripts.

### Two sampling/template profiles

The scripts fall into two groups, and this is the main thing to keep straight
when copying one to make another:

- **current profile** (`qwen-*`, `*-6km-test`, `ornith-*`):
  `--jinja` + `--chat-template-file` + `--reasoning-effort medium`,
  model-author sampling defaults (`--temp 1.0 --top-k 20 --top-p 0.95
  --min-p 0.0`), no repeat/DRY penalties, `--spec-draft-n-max 2–3`.
  `davidau-*` is the current profile tuned for code and deviates on purpose:
  `--temp 0.6` (the model card's “Thinking Mode (Precise Coding)” set) and
  `--reasoning-effort xhigh`, with `--repeat-penalty 1.0 --presence-penalty 0.0
  --frequency-penalty 0.0` spelled out because the author insists penalties stay
  off on MTP builds. Do not “normalise” it back to `--temp 1.0 / medium`.
- **older unsloth profile** (`unsloth-qwen38-27-{3kxl,4km,5km,6km}.bat`):
  low temperature (0.15–0.6), `--min-p 0.05`, DRY penalties
  (`--dry-multiplier`, `--dry-base 1.75`, `--dry-allowed-length`,
  `--dry-penalty-last-n`), `--spec-draft-n-max 4–6`, and **no `--jinja`** —
  so their `--chat-template-file` has no effect and the GGUF's built-in template
  is used instead. If a change is meant to affect the chat template on those
  scripts, add `--jinja` as well.

Deep speculation (`--spec-draft-n-max 6`) in the older profile only pays off on
trivial prompts; the current profile deliberately keeps it at 2–3.

### Per-model notes

`ornith-ornith15-35-8k.bat` runs a different model family —
`Ornith-1.5-35B-Q8_0.gguf` (`c:\Users\viktor\.lmstudio\models\ornith-ai\Ornith-1.5-35B-A3B-GGUF\`),
arch `qwen35moe`:

- MoE (256 experts, 8 active, `expert_ff 512` + a shared expert), `d = 2048`,
  40 blocks + `blk.40.nextn.*` (one MTP head, `nextn_predict_layers = 1`), so
  `--spec-type draft-mtp` applies just like on Qwen3.8-27B. Hybrid as well:
  `full_attention_interval = 4` → 10 attention layers, 30 SSM layers
  (`d_inner 4096`, `d_state 128`, `n_group 16`); native context 262144;
- `n_head_kv = 2` (vs 4 on Qwen3.8-27B) makes KV ~3.2× cheaper —
  `q8_0/q8_0` costs 10 880 B/token → 2720 MiB at `-c 262144`. The weights are the
  tight part instead (35.2 GB of the 48 GB across three cards), which is why `-ts`
  is almost even (`14,13,13`) rather than skewed like the Qwen3.8 configs, and why
  `-ub` stays at 256. Tighten in the §4 order but start with `-ub` / `-ts`, not
  `-c` — lowering context barely frees anything here;
- vision is off (`--no-mmproj`) even though `mmproj-Ornith-1.5-35B-BF16.gguf` sits
  next to the model and `ornith15-35.jinja` renders image/video blocks — add
  `--mmproj` to enable it (~0.9 GB VRAM);
- `Ornith-1.5-35B-Q6_K.gguf` (27.2 GB) is in the same directory if more headroom
  is needed;
- measured at `-c 262144 -ts 14,13,13 -ub 256`: `nvidia-smi` 14898 / 15214 / 13914
  MiB of 16311, nothing on CPU, ~84 t/s generation with MTP accepting ~78 % of
  drafts. CUDA1 is the tightest card — shift to `14,12,14` if it ever OOMs.
  `--cache-reuse 256` is accepted but logged as unsupported for this context type.

`davidau-qwen38-27-turbo-6k.bat` runs a DavidAU remix of the same Qwen3.8-27B —
`Qwen3.8-27B-TurboFCFusion-735-882-Here-Uncen-NEO-CODER-MAX-MTP-Q6_K.gguf`
(`c:\Users\viktor\.lmstudio\models\DavidAU\Qwen3.8-27B-TURBO-Fable-Cold-Fusion-735-882-Heretic-Uncensored-NEO-CODER-MAX-MTP-GGUF\`),
so it started as a copy of `qwen-qwen38-27-6k.bat` but has since been retuned for
code — it now differs in `-m`, template, `-ts`, `-ub`, sampling, reasoning effort
and prompt cache:

- arch `qwen35`, 65 blocks (64 + one MTP head, `nextn_predict_layers = 1`) and the
  exact geometry of Qwen3.8-27B (`d 5120`, `n_head 24`, `n_head_kv 4`, `n_ff 17408`,
  `full_attention_interval 4`, native context 262144) — `--spec-type draft-mtp`
  applies unchanged;
- it passes `qwen38-27-turbo.jinja`, not `qwen38-27.jinja` (see below); that
  template accepts only `xhigh` (its default) / `medium` / `low` for
  `--reasoning-effort` and raises on anything else — note there is **no** `high`.
  `medium` injects no instruction at all; `xhigh` prepends “think carefully …
  prioritize correctness” to the system block, which is why the coding config uses
  it;
- the weights are 22 920 MiB — ~1 530 MiB heavier than lmstudio's Q6_K (21 392 MiB),
  so it runs at `-c 262144 -ts 12,11,7 -b 2048 -ub 256`: `12,11,7` + `-ub 256` is
  the geometry measured fastest on this bench (32.2 vs 30.1 t/s for
  `11,10,9` + `-ub 512`), and `-ub 256` halves the compute buffer (≈ 1.6 GiB per
  card, `CALCULATE.md` §6.4) — that is the headroom the heavier weights need.
  Measured at that setting: `nvidia-smi` 13 304 / 14 069 / 12 382 MiB of 16 311
  (GPU1 includes ~1 600 MiB of desktop usage), nothing on CPU, 32.1 t/s generation
  with MTP accepting 83 % of drafts at `mean len 3.24`. If it OOMs, go
  `-ts 11,11,8`, then `-ctv q4_0`, and only then `-c`;
- it is the only script with `-cram 24576`: the default 8 GiB prompt cache cannot
  hold even two entries for this context type (one is 2.6–7.3 GiB), so the log
  fills with `making room for prompt cache entry, removing oldest entry` and every
  turn re-prefills the whole prompt (133k tokens ≈ 225 s at ~595 t/s). 24 GiB of
  the box's 61.6 GiB keeps 4–8 branches hot; the model is fully on GPU, so losing
  its mmap pages to the cache is harmless;
- `--cache-reuse` is **not** passed: like on `ornith-*`, the server logs
  `cache_reuse is not supported by this context, it will be disabled` — a hybrid
  recurrent context has no KV shifting;
- at the default verbosity this build prints no `load_tensors` / `llama_kv_cache` /
  `compute buffer size` lines at all — add `--verbose` when you need the `CALCULATE.md`
  §4 breakdown, and read card occupancy from `nvidia-smi` otherwise;
- `--reasoning-preserve` stays at its default (**on**). This is a cache decision,
  not a quality one: with `--no-reasoning-preserve` the template drops `<think>`
  from every assistant turn before the last user query, so the prefix is rewritten
  on each turn and the prompt cache stops hitting;
- vision is off (`--no-mmproj`) even though `mmproj-F32.gguf` (1.76 GiB) sits next
  to the model;
- the author's own defaults are baked into the GGUF (`temp 1.0 / top-k 20 /
  top-p 0.95`); the script overrides `temp` to `0.6` on purpose, because the model
  card lists 1.0 for general tasks and 0.6 for “precise coding”.

`unsloth-qwen38-27-6km-test.bat` is the three-card experiment for UD-Q6_K_M: it
is the only script with `-ot "token_embd.weight=CUDA0"` and a deliberately skewed
`-ts 12,11,7` (GPU2 sits on a Gen4 x4 link, so layers are moved off it).

## Chat templates

| file                    | used by                                          |
| ----------------------- | ------------------------------------------------ |
| `qwen38-27.jinja`       | all `qwen-*` and `unsloth-*` scripts             |
| `qwen38-27-turbo.jinja` | `davidau-qwen38-27-turbo-6k.bat`                 |
| `ornith15-35.jinja`     | `ornith-ornith15-35-8k.bat`                      |
| `agentworld-35.jinja`   | nothing — no launch script references it (yet)   |

`qwen38-27.jinja` is a **patched** Qwen3.8 template; `qwen38-27-turbo.jinja` is
the DavidAU remix's own (stock) template with the same two message-shape patches
applied, so both accept the same client payloads. The patches:

- merge every leading `system`/`developer` message into one system block instead
  of looking only at `messages[0].role == 'system'`, and render later
  `system`/`developer` messages as system turns;
- remove the guards that an agent client trips: `System message must be at the
  beginning.` (turbo only — it raised on any `system` past index 0) and
  `No user query found in messages.` (turbo only — it raised when every `user`
  turn looked like a `<tool_response>`). Turbo's backward scan that picks the
  last real (non-`<tool_response>`) user turn is kept; without a match it leaves
  the index at the last message, which merely keeps `<think>` in every assistant
  turn.

What still differs between them: `qwen38-27.jinja` validates tool-call names and
rejects arguments passed as a JSON string, while turbo serialises whatever it is
given; and turbo picks the last user turn by skipping `<tool_response>`-shaped
ones, where `qwen38-27.jinja` just takes the last `user` message. The
`xhigh`/`medium`/`low` set and the three instruction strings are identical in
both.

Agent clients that send a `developer` role or several system messages need the
patched variant — which now means both Qwen3.8 templates. Note that the git index still holds the Ornith template as
`Ornith15-35.jinja` while the working tree has `ornith15-35.jinja` — a case-only
rename Windows git does not notice; keep passing the lowercase name.

**External paths hard-coded in every script** (not in this repo):

- Binaries: `c:\Llamacpp\cuda13\` (`llama-server.exe` + CUDA/GGML DLLs).
- Models: `c:\Users\viktor\.lmstudio\models\...` (LM Studio's model cache).
- Log: `c:\Llamacpp\cuda13\llama-server.log` — every script writes to the same
  file, so it only ever holds the last run.

Each script does `cd /d "%~dp0.."` so it runs from the repo root, which is why
`--chat-template-file ".\qwen38-27.jinja"` resolves.

## Running

```bat
cuda13\unsloth-qwen38-27-4km.bat
```

Server comes up at `http://127.0.0.1:1234` (Web UI, `/v1/chat/completions`,
`/health`). Only one script can run at a time — they all bind port 1234 and all
expect the whole GPU set to be free. `pause` at the end keeps the window open on
exit.

## Editing conventions

- The model is a **hybrid Transformer + SSM**: only every 4th layer has a KV
  cache; SSM layers hold a fixed-size state that does not grow with context.
  Native context limit is 262144. Before raising `-c` or loosening KV quant,
  work through `CALCULATE.md` §3 and verify against `llama-server.log` — the
  failure signatures (`retrying without pipeline parallelism`,
  `cudaMalloc failed`, `CPU model buffer` on `blk.*`) and the tightening order
  (`-c` ↓ → `-ctv` coarser → `-ctk` coarser → `-ub` ↓ → `-ngl` ↓ last) are in §4.
- On every three-card config `-ctk` must stay `q8_0`: `f16` K has no CUDA kernel
  and dumps the graph onto the CPU (35 graph splits, all 16 cores pegged, prefill
  down to ~219 t/s instead of ~898).
- `-ts` is deliberately skewed — `17,13` on two cards because KV / SSM / pipeline
  compute buffers land on the higher card under `-sm layer`, and away from GPU2
  on three cards because it sits on a Gen4 x4 link while the others are Gen5 x8.
  Re-check card occupancy in `nvidia-smi` after any `-ts`/`-c` change.
- Target bench: Ryzen 9 9950X (16c/32t), 64 GB DDR5, 3× RTX 5060 Ti 16 GB (two on
  Gen5 x8, one on Gen4 x4), no NVLink/P2P, Windows 11 x64. `-t 16` /
  `--threads-batch 16` and the split values assume this box.
- `README.md` describes an older bundled layout (`configs/`, in-repo `llamacpp/`
  and `models/` dirs, a `cuda12/` set) that no longer matches the actual tree —
  trust the scripts and `CALCULATE.md` over the README's path examples.
- Prose docs (`README.md`, `CALCULATE.md`) are written in Russian; keep new
  content in the same language as the file you are editing.
