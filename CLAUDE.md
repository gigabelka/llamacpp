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

| script                             | model (GGUF)                              | GPUs  | `-c`   | `-ts`    | `-ctk`/`-ctv` | `-b`/`-ub` |
| ---------------------------------- | ----------------------------------------- | ----- | ------ | -------- | ------------- | ---------- |
| `daslab-qwen38-27-iq3_s.bat`       | ISTA-DASLab GSQ-RCO IQ3_S (MTP)           | 0,1   | 262144 | 17,13    | q8_0 / q8_0   | 1024 / 256 |
| `qwen-qwen38-27-4km.bat`           | lmstudio-community Q4_K_M                 | 0,1   | 262144 | 17,13    | q8_0 / q8_0   | 1024 / 256 |
| `qwen-qwen38-27-6k.bat`            | lmstudio-community Q6_K                   | 0,1,2 | 262144 | 11,10,9  | q8_0 / q8_0   | 2048 / 512 |
| `unsloth-qwen38-27-3kxl.bat`       | unsloth UD-Q3_K_XL                        | 0,1   | 229376 | 17,13    | f16 / f16     | 1024 / 256 |
| `unsloth-qwen38-27-4km.bat`        | unsloth UD-Q4_K_M                         | 0,1   | 180224 | 17,13    | f16 / f16     | 1024 / 256 |
| `unsloth-qwen38-27-5km.bat`        | unsloth UD-Q5_K_M                         | 0,1   | 262144 | 16,14    | q8_0 / q4_0   | 1024 / 256 |
| `unsloth-qwen38-27-6km.bat`        | unsloth UD-Q6_K_M                         | 0,1   | 65336  | 17,13    | f16 / f16     | 1024 / 256 |
| `unsloth-qwen38-27-6km-test.bat`   | unsloth UD-Q6_K_M                         | 0,1,2 | 262144 | 12,11,7  | q8_0 / q8_0   | 2048 / 256 |
| `ornith-ornith15-35-8k.bat`        | ornith-ai Ornith-1.5-35B Q8_0             | 0,1,2 | 262144 | 14,13,13 | q8_0 / q8_0   | 2048 / 256 |
| `ornith-ornith15-35-6k.bat`        | ornith-ai Ornith-1.5-35B Q6_K             | 0,1   | 98304  | 14,13    | q8_0 / q4_0   | 2048 / 256 |
| `davidau-qwen38-27-turbo-6k.bat`   | DavidAU TurboFCF NEO-CODER-MAX-MTP Q6_K   | 0,1,2 | 262144 | 12,11,7  | q8_0 / q8_0   | 2048 / 256 |
| `davidau-qwen38-27-turbo-4k_m.bat` | DavidAU TurboFCF NEO-CODER-MAX-MTP Q4_K_M | 0,1   | 262144 | 17,13    | q8_0 / q8_0   | 2048 / 128 |

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
  `ornith-ornith15-35-6k.bat` is tuned for code the same way and deviates too:
  `--temp 0.6` and `--reasoning-effort xhigh`. Unlike the Qwen scripts, its
  effort flag only does something because `qwen-general.jinja` carries the
  same `xhigh`/`medium`/`low` block — see “Chat templates”.
  `qwen-qwen38-27-4km.bat` is the same code tuning on the two-card Q4_K_M:
  `--temp 0.6` and `--reasoning-effort xhigh`, plus `--reasoning-budget -1`
  spelled out (“think without a limit” — already the default) and `-cram 24576`
  in place of the no-op `--cache-reuse 256`. The official Qwen3.8-27B card gives
  `1.0` for thinking mode, so the `0.6` here is this repo's code profile rather
  than the card's recommendation — deliberate, do not “normalise” it away. Its
  VRAM knobs are untouched: `-c 262144 -ts 17,13` at `q8_0/q8_0` is the measured
  §6 point in `CALCULATE.md`.
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
  next to the model and `qwen-general.jinja` renders image/video blocks — add
  `--mmproj` to enable it (~0.9 GB VRAM);
- `Ornith-1.5-35B-Q6_K.gguf` (27.2 GB) is in the same directory if more headroom
  is needed;
- measured at `-c 262144 -ts 14,13,13 -ub 256`: `nvidia-smi` 14898 / 15214 / 13914
  MiB of 16311, nothing on CPU, ~84 t/s generation with MTP accepting ~78 % of
  drafts. CUDA1 is the tightest card — shift to `14,12,14` if it ever OOMs.
  `--cache-reuse 256` is accepted but logged as unsupported for this context type.

`ornith-ornith15-35-6k.bat` is the same model at `Ornith-1.5-35B-Q6_K.gguf`
(29.2 GB on disk = 27.2 GiB) on **two** cards, tuned for code. The two Q6_K/Q8_0
files are the only Ornith GGUFs downloaded — Q5_K_M/Q4_K_M are not in the folder.
It cannot run the native `-c 262144`: parsing the Q6_K header gives 27 447 MiB of
GPU-resident weights (`token_embd` is CPU-mapped and costs nothing in VRAM, but
`output.weight` is untied and adds 398 MiB to the last card), leaving only ~2.0
GiB of the two cards' ~32.1 GiB for KV + compute + MTP draft. At `-c 262144` the
budget model — calibrated against the three-card Q8_0 measurement above and
accurate to ~270 MiB — puts CUDA1 at ~1142 MiB over. Hence:

- `-c 98304` with `-ctv q4_0`: ≥500 MiB free on each card against the real
  16 050 MiB base. `q8_0/q4_0` KV is 8320 B/token vs 10 880 for `q8_0/q8_0`;
- `-ts 14,13`, copying the first two fields of the three-card script. The split
  lands the boundary after `blk.20` → 21 blocks on CUDA0, 20 on CUDA1; an even
  `13,13` would give only 20 on CUDA0 and push another ~660 MiB block onto CUDA1,
  which already carries `blk.40` (the MTP head), `output.weight` and the whole
  draft KV + compute buffer, so it is always the tight card. Blocks cannot be
  split, so `14,13` is the smallest imbalance reachable;
- `-ctk` stays `q8_0` — the f16 K-cache has no CUDA kernel (see the three-card
  note above); `-ctv q4_0` is the cheap lever instead;
- if it OOMs: `-ot "output.weight=CUDA0"` (moves 398 MiB off the tight card)
  → `-c` ↓ 81920 → 65536 → `-ctk q4_0` → `-ub 128` → `-ngl` last;
- the only routes to a full 262144 on two cards are `Ornith-1.5-35B-Q5_K_M.gguf`
  (25.3 GB, needs downloading — budget says it fits with ~700–1000 MiB to spare)
  or a third card;
- code profile: `--temp 0.6` (the card lists 0.6 for general work and 1.0 only
  for benchmark reproduction) and `--reasoning-effort xhigh`. This script is the
  reason the shared template gained `reasoning_effort` support at all.

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
- it passes `qwen-general.jinja`, like every script (see below); that
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
- it is one of two scripts with `-cram 24576` (the other is
  `qwen-qwen38-27-4km.bat`): the default 8 GiB prompt cache cannot
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

`davidau-qwen38-27-turbo-4k_m.bat` is the same model at the Q4_K_M file
(`…-MTP-Q4_K_M.gguf`), pulled back onto **two** cards: `-ts 17,13 -c 262144` with
`-b 2048 -ub 128`. It runs the same code profile as the three-card script
(`--temp 0.6`, `xhigh`, penalties spelled out) and the same
`qwen-general.jinja`. It has **not** been measured yet — `-ub 128` halves the
compute buffer relative to `-ub 256`, which is presumably the headroom the
heavier Q4_K_M weights need, but that is inference, not a logged run.

`unsloth-qwen38-27-6km-test.bat` is the three-card experiment for UD-Q6_K_M: it
is the only script with `-ot "token_embd.weight=CUDA0"` and a deliberately skewed
`-ts 12,11,7` (GPU2 sits on a Gen4 x4 link, so layers are moved off it).

`daslab-qwen38-27-iq3_s.bat` runs `Qwen3.8-27B-GSQ-RCO-IQ3_S-mtp.gguf`
(`c:\Users\viktor\.lmstudio\models\ISTA-DASLab\Qwen3.8-27B-GSQ-RCO-GGUF\`) — an
ISTA DASLab non-uniform per-tensor quantisation (GSQ-RCO picks a separate quant
type per tensor under a size budget). Geometry is `qwen35`, identical to the
other Qwen3.8-27B configs, so everything in the Qwen3.8 entries above applies:
65 blocks (64 + the MTP head at `blk.64.nextn.*`, `nextn_predict_layers = 1`),
`d 5120`, `n_head_kv 4`, `key_length = value_length = 256`,
`full_attention_interval 4` → 16 attention layers of 64, native context 262144 —
hence `--spec-type draft-mtp` applies unchanged. It is the **lightest** Qwen3.8
config here and the only one with room to spare:

- 12 109 021 184 B = 11.28 GiB total, of which `blk.*` is 10 477.6 MiB and
  `output.weight` 682.0 MiB (untied, lands on the last card); `token_embd.weight`
  is 388.4 MiB and stays host-mapped (`CPU_Mapped`), which is normal;
- so GPU-resident weights are ~11 160 MiB — **3.8 GiB lighter than the Q4_K_M of
  `qwen-qwen38-27-4km.bat`**, the config it was copied from. Measured with
  `--verbose` at `-c 262144 -ts 17,13 -q8_0/q8_0 -ub 256`: weights divide almost
  evenly (`CUDA0 5587.70` + `CUDA1 5571.99`), main KV 8704 MiB
  (`CUDA0 4896.00` / `CUDA1 3808.00`, 16 layers, 34 816 B/token), RS
  271.20 + 177.68 MiB, compute buffers `CUDA0 1642.10` / `CUDA1 1597.09` plus the
  613.03 MiB draft graph. `nvidia-smi` lands at **12 532 / 12 928 MiB** of 16 311
  nominal (~3.5 / ~3.1 GiB free against the real 16 050 base), with
  `pipeline parallelism enabled`, `offloaded 66/66 layers to GPU`,
  `CPU_Mapped 388.38 MiB` (the embedding — normal) and no `CPU model buffer size`
  for `blk.*`. See `CALCULATE.md` §6.9;
- `-ts 17,13` is kept verbatim from the Q4_K_M config and is **not** rebalanced
  despite the lighter weights. Note it skews the *KV/RS/compute* buffers, not the
  weights: CUDA1 is always the tight card because the MTP draft KV (1024 MiB,
  **f16**, 1 layer), the draft compute buffer (+613 MiB) and `output.weight`
  (682 MiB) all land on it, and `-ts 16,14` is known to OOM on this family;
- that ~3 GiB of slack is deliberately **not** spent on a bigger `-ub` or a finer
  KV quant. `-ub 256` is the fastest point measured on this bench in the §6
  calibration (`-ub` has not been re-measured for IQ3_S) and `f16` KV would need
  +7680 MiB; `q8_0/q8_0` is already the near-lossless point. If prefill speed
  ever matters more than margin, `-ub 384` then `-ub 512` are the levers — the
  latter leaves only ~870 MiB on CUDA1;
- measured generation on a code prompt: **44.6 t/s** with MTP accepting 78.5 % of
  drafts. Thinking is on and unlimited, so a short `max_tokens` is consumed
  entirely by `reasoning_content` — budget accordingly when testing;
- `--reasoning-effort xhigh` **is** the maximum, not a middle setting. The flag
  itself accepts `minimal/low/medium/high/xhigh/max`, but
  `qwen-general.jinja` allows only `('xhigh', 'medium', 'low')` and raises on
  anything else, so `high` and `max` produce a template error rather than deeper
  thinking. `--reasoning-budget -1` is the unrestricted default, spelled out;
- the GSQ-RCO model's own sampling defaults are baked into the GGUF as
  `temp 1.0 / top-k 20 / top-p 0.95 / min-p 0.0`; the script overrides `temp` to
  `0.6` for the repo's code profile (the model card recommends no sampling values
  at all) and spells out the zero penalties, as on the other MTP configs;
- vision is off (`--no-mmproj`) even though `mmproj-Qwen3.8-27B-BF16.gguf`
  (931 MB) sits next to the model — add `--mmproj` to enable it, the ~910 MiB
  still fits in the slack;
- if it ever OOMs: `-ub 128` → `-ctv q4_0` → `-ot "output.weight=CUDA0"` →
  `-c 229376` → `-ngl` last.

## Chat templates

| file                  | used by                                        |
| --------------------- | ---------------------------------------------- |
| `qwen-general.jinja`  | every script in `cuda13/`                      |
| `agentworld-35.jinja` | nothing — no launch script references it (yet) |

`qwen-general.jinja` is the single merged template. It replaced four
near-duplicate files (`qwen38-27.jinja`, `qwen38-27-turbo.jinja`,
`qwen38-27-gsq-rco.jinja`, `ornith15-35.jinja`) that were just different stages of
patching the same Qwen chatml template — turbo and gsq-rco were already
byte-identical, and the other two differed by two or three hunks each. The merge
took turbo as the base and is a **superset**: on every payload except the two
cases noted below it renders byte-for-byte what the old file for that script
rendered. It serves both arch families (`qwen35` for the Qwen3.8-27B configs,
`qwen35moe` for Ornith) — the token set, the tool-call format and the
`reasoning_effort` block were identical across all four.

What it contains:

- **merged system block** — every leading `system`/`developer` message is folded
  into one system turn, and later `system`/`developer` messages render as system
  turns. The old `ornith15-35.jinja` merged only the first two and *silently
  dropped* a third; this is the one rendering change on `ornith-*` scripts;
- **no agent-tripping guards** — `System message must be at the beginning.` and
  `No user query found in messages.` are both gone, so clients that send a
  `developer` role, several system messages, or a history whose every `user` turn
  looks like a `<tool_response>` all work;
- **backward scan for the last real user turn** (turbo's version) — skips
  `<tool_response>`-shaped turns; without a match it leaves the index at the last
  message, which merely keeps `<think>` in every assistant turn. Only matters
  together with `--no-reasoning-preserve`, which no script passes;
- **`preserve_thinking` is honoured** (turbo's version). The old Ornith template
  ignored it and always emitted `<think>`; since the default is on and no script
  passes `--no-reasoning-preserve`, the rendering is the same;
- **tool-call validation** (from `qwen38-27.jinja`) — raises on a missing function
  name, and on `arguments` passed as a JSON string or a non-object. The old turbo
  and Ornith files fed a string straight into `|items` and died with a cryptic
  error instead;
- **inline `</think>` fallback** (from `ornith15-35.jinja`) — if an assistant
  message has no `reasoning_content` but its `content` holds
  `<think>…</think>`, the reasoning is lifted into the `<think>` block instead of
  being wrapped in a second empty one. This is the other rendering change, and it
  fixes a real double-`<think>` bug the turbo/gsq-rco and `qwen38-27` files had;
- **`reasoning_effort`**: `xhigh` (default) / `medium` / `low`, anything else is a
  `raise_exception`. So `--reasoning-effort high` and `max`, which the server-side
  flag accepts, produce a template error — there is **no** `high`. `medium`
  injects no instruction at all; `xhigh` prepends “think carefully … prioritize
  correctness” to the system block, which is why the coding configs use it. The
  block is gated on `enable_thinking`;
- `render_content` with image/video branches (and a `raise_exception` if either
  appears in a system message), though every script runs `--no-mmproj`.

Caveats that survive the merge:

- `unsloth-qwen38-27-{3kxl,4km,5km,6km}.bat` have **no `--jinja`**, so
  `--chat-template-file` does nothing there and the GGUF's built-in template is
  used. They point at `qwen-general.jinja` only so no script references a deleted
  file. Adding `--jinja` to them is a separate decision — it would change their
  rendered prompt;
- on the Ornith models `--reasoning-effort` works *only* because of this
  template's `reasoning_effort` block. The model itself has no effort tiers (the
  card says thinking is simply on by default), so this is a prompt-level
  instruction, not a runtime dial. `ornith-ornith15-35-8k.bat` passes `medium`,
  i.e. no injected instruction;
- `agentworld-35.jinja` was deliberately left out of the merge: no script
  references it, and it is an unpatched older base (no `reasoning_effort`, only
  `messages[0]` as system) for a different family — it has an audio branch
  (`<|audio_start|>`) the Qwen3.8/Ornith vocabularies do not carry.

**External paths hard-coded in every script** (not in this repo):

- Binaries: `c:\Llamacpp\cuda13\` (`llama-server.exe` + CUDA/GGML DLLs).
- Models: `c:\Users\viktor\.lmstudio\models\...` (LM Studio's model cache).
- Log: `c:\Llamacpp\cuda13\llama-server.log` — every script writes to the same
  file, so it only ever holds the last run.

Each script does `cd /d "%~dp0.."` so it runs from the repo root, which is why
`--chat-template-file ".\qwen-general.jinja"` resolves.

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
