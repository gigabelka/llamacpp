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

**Two exceptions to everything below.** First, the bench now has **two** RTX 5060 Ti,
not three: `nvidia-smi` and `Win32_VideoController` list `01:00.0` and `03:00.0` only.
Every three-card config here (`qwen-qwen38-27-6k.bat`, `ornith-ornith15-35-8k.bat`,
`davidau-qwen38-27-turbo-6k.bat`, `venastine-xing4-29-a4b-5km.bat`) therefore passes a
three-field `-ts` the hardware no longer matches, and every three-card measurement in
this file and in `CALCULATE.md` describes a machine that is gone. Nothing has been
retuned for two cards yet. Second, `cuda13/unsloth-qwen38-27-nvfp4-vllm.bat` is **not** a
llama.cpp script at all — it runs vLLM inside WSL2 against a safetensors model, so the
knob table below (`-c`, `-ts`, `-ctk`/`-ctv`, `-b`/`-ub`, `-ngl`) does not apply to it,
and neither does anything in `CALCULATE.md`. See its own entry under “Per-model notes”.

Scripts differ by model file, card count, and the VRAM-sensitive knobs:

| script                             | model (GGUF)                              | GPUs  | `-c`   | `-ts`    | `-ctk`/`-ctv` | `-b`/`-ub` |
| ---------------------------------- | ----------------------------------------- | ----- | ------ | -------- | ------------- | ---------- |
| `daslab-qwen38-27-iq3_s.bat`       | ISTA-DASLab GSQ-RCO IQ3_S (MTP)           | 0,1   | 262144 | 17,13    | q8_0 / q8_0   | 1024 / 256 |
| `ukisai-swift15-qwen38-27-iq3_s.bat` | ukisai Swift-1.5 GSQ-RCO IQ3_S (MTP)    | 0,1   | 262144 | 17,13    | q8_0 / q8_0   | 1024 / 256 |
| `qwen-qwen38-27-4km.bat`           | lmstudio-community Q4_K_M (main code config) | 0,1   | 262144 | 17,13    | q8_0 / q8_0   | 1024 / 256 |
| `qwen-qwen38-27-6k.bat`            | lmstudio-community Q6_K                   | 0,1,2 | 262144 | 11,10,9  | q8_0 / q8_0   | 2048 / 512 |
| `unsloth-qwen38-27-3kxl.bat`       | unsloth UD-Q3_K_XL                        | 0,1   | 229376 | 17,13    | f16 / f16     | 1024 / 256 |
| `unsloth-qwen38-27-4km.bat`        | unsloth UD-Q4_K_M                         | 0,1   | 180224 | 17,13    | f16 / f16     | 1024 / 256 |
| `unsloth-qwen38-27-5km.bat`        | unsloth UD-Q5_K_M                         | 0,1   | 262144 | 16,14    | q8_0 / q4_0   | 1024 / 256 |
| `unsloth-qwen38-27-6km.bat`        | unsloth UD-Q6_K_M                         | 0,1   | 65336  | 17,13    | f16 / f16     | 1024 / 256 |
| `ornith-ornith15-35-8k.bat`        | ornith-ai Ornith-1.5-35B Q8_0             | 0,1,2 | 262144 | 14,13,13 | q8_0 / q8_0   | 2048 / 256 |
| `ornith-ornith15-35-6k.bat`        | ornith-ai Ornith-1.5-35B Q6_K             | 0,1   | 98304  | 14,13    | q8_0 / q4_0   | 2048 / 256 |
| `ornith-ornith15-35-5km.bat`       | ornith-ai Ornith-1.5-35B Q5_K_M           | 0,1   | 262144 | 14,13    | q8_0 / q8_0   | 2048 / 256 |
| `davidau-qwen38-27-turbo-6k.bat`   | DavidAU TurboFCF NEO-CODER-MAX-MTP Q6_K   | 0,1,2 | 262144 | 12,11,7  | q8_0 / q8_0   | 2048 / 256 |
| `davidau-qwen38-27-turbo-4k_m.bat` | DavidAU TurboFCF NEO-CODER-MAX-MTP Q4_K_M | 0,1   | 262144 | 17,13    | q8_0 / q8_0   | 2048 / 128 |
| `bytkim-qwen38-27-pi-4km.bat`      | bytkim Qwen3.8-27B-pi Q4_K_M (MTP head in a separate `-md` file) | 0,1 | 262144 | 17,13 | q8_0 / q8_0 | 2048 / 128 |
| `unsloth-agentworld-35-5km.bat`    | unsloth Qwen-AgentWorld-35B-A3B UD-Q5_K_M (no MTP head) | 0,1 | 262144 | 1,1 | q8_0 / q8_0 | 2048 / 128 |
| `venastine-xing4-29-a4b-5km.bat`   | Venastine Xing4.0-29B-A4B Q5_K_M (MLA + mHC MoE; own template; **arch not supported by this build**) | 0,1,2 | 262144 | 16,15,10 | q8_0 / q8_0 | 2048 / 256 |

Card count is set per script via `CUDA_VISIBLE_DEVICES` (with
`CUDA_DEVICE_ORDER=PCI_BUS_ID`), so the number of `-ts` fields must match it.
Everything else — `-ngl 99`, `-sm layer`, `-fa on`, `-kvu`, `-np 1`, `-n -1`,
`--no-mmproj`, `--spec-type draft-mtp`, `-t 16`, `--threads-batch 16`, port 1234
— is identical across scripts, with two exceptions: `bytkim-qwen38-27-pi-4km.bat` takes its
MTP head from a separate file (`-md`, `-ngld 99`) instead of from the main GGUF, and
`unsloth-agentworld-35-5km.bat` has no MTP head at all, so it passes no `--spec-*` flags. The prompt-cache
flag is **not** identical either: eight scripts (`qwen-qwen38-27-4km.bat`,
`daslab-qwen38-27-iq3_s.bat`, `ukisai-swift15-qwen38-27-iq3_s.bat`, `bytkim-qwen38-27-pi-4km.bat`
both `davidau-*`, `unsloth-agentworld-35-5km.bat` and `venastine-xing4-29-a4b-5km.bat`) pass `-cram 24576`, the other eight pass `--cache-reuse 256` — which this build logs as
unsupported on a hybrid recurrent context and disables, so it is dead weight
everywhere in this repo. See the `davidau-qwen38-27-turbo-6k.bat` notes for why
24 GiB.

### Two sampling/template profiles

The scripts fall into two groups, and this is the main thing to keep straight
when copying one to make another:

- **current profile** (`qwen-*`, `davidau-*`, `daslab-*`, `ukisai-*`, `ornith-*`, `bytkim-*`, `unsloth-agentworld-*`):
  `--jinja` + `--chat-template-file`, model-author sampling defaults
  (`--temp 1.0 --top-k 20 --top-p 0.95 --min-p 0.0`), no repeat/DRY penalties,
  `--spec-draft-n-max 2–3`. **No script passes `--reasoning-effort` any more**:
  the flag was a complete no-op (the template never read it) and was removed from
  all twelve scripts that carried it on 2026-10-07. Do not re-add it as
  documentation — the effort level is stated once, in the preamble text inside
  `qwen-general.jinja`, and cannot be changed from outside, see “Chat templates”.
  No script turns thinking off either: the `--reasoning off` variant
  (`qwen-qwen38-27-4km_no_res.bat`, instruct samplers, closed `<think></think>`)
  existed on 2026-10-07 and was **deleted** the same day, together with
  `qwen-qwen38-27-4km_xhigh.bat`; the two were collapsed into the single
  `qwen-qwen38-27-4km.bat` described below. `--reasoning off` remains the one
  working lever if that fast lane is ever wanted back, see “Chat templates”.
  `davidau-*` is the current profile tuned for code and deviates on purpose:
  `--temp 0.6` (the model card's “Thinking Mode (Precise Coding)” set), with
  `--repeat-penalty 1.0 --presence-penalty 0.0 --frequency-penalty 0.0` spelled
  out because the author insists penalties stay off on MTP builds. Do not
  “normalise” it back to `--temp 1.0`.
  `ornith-ornith15-35-{5km,6k}.bat` are tuned for code the same way and deviate
  too: `--temp 0.6`. Only `ornith-ornith15-35-8k.bat` keeps `--temp 1.0`.
  `unsloth-agentworld-35-5km.bat` is `--temp 0.6` as well: that is the card's own sampler set
  (`temp 0.6 / top_p 0.95 / top_k 20`, also baked into the GGUF metadata), and there is no
  thinking-mode instruction to contradict. It passes no `--spec-*` flags (no MTP head).
  `qwen-qwen38-27-4km.bat` is **the main config for hard coding work**
  (algorithms, debugging, state tracing, multi-file refactoring, type inference,
  edge cases), and it is the one script running the card's *thinking-mode*
  samplers instead of this repo's `0.6` code profile:
  `--temp 1.0 --top-k 20 --top-p 0.95 --min-p 0.0`. It sat at `0.6` until
  2026-10-07 and was moved on purpose — the official Qwen3.8-27B card gives `1.0`
  for thinking mode and warns that lowering the temperature *in that mode* sends
  the model into loops inside `<think>`, which is exactly the failure this config
  must not have. Do not “normalise” it back to `0.6`. That change is scoped to
  this script: `davidau-*` and `ornith-ornith15-35-6k.bat` keep their `0.6`. It
  also spells out `--reasoning-budget -1` (“think without a limit” — already the
  default) and uses `-cram 24576` in place of the no-op `--cache-reuse 256`.
  Its VRAM point is `CALCULATE.md` §6: `-c 262144 -ts 17,13` at `q8_0/q8_0`,
  measured. The script was called `qwen-qwen38-27-4km_xhigh.bat` until
  2026-10-07; the `_xhigh` suffix went away with the `--reasoning-effort` flag,
  because nothing in the script sets an effort level any more.
- **older unsloth profile** (`unsloth-qwen38-27-{3kxl,4km,5km,6km}.bat`):
  low temperature (0.15–0.6), `--min-p 0.05`, DRY penalties
  (`--dry-multiplier`, `--dry-base 1.75`, `--dry-allowed-length`,
  `--dry-penalty-last-n`), `--spec-draft-n-max 4–6`, and no explicit `--jinja`.
  That omission does **not** disable the template: in this build `--jinja`
  defaults to *enabled* (`--help`: “whether to use jinja template engine for
  chat (default: enabled)”), so `--chat-template-file` applies to these four
  exactly as it does everywhere else — verified by starting a config with the
  flag stripped and getting our template's output, not the GGUF's. Only
  `--no-jinja` would turn it off. (An earlier note here claimed the opposite;
  it was true of an older build.)

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
(29.2 GB on disk = 27.2 GiB) on **two** cards, tuned for code. Three Ornith GGUFs
are now in the folder — Q5_K_M (25.3 GB, downloaded 2026-10-06), Q6_K and Q8_0;
Q4_K_M is not.
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
  (the budget said it fits with ~700–1000 MiB to spare; it has since been
  downloaded and `ornith-ornith15-35-5km.bat` runs exactly that — `-c 262144
  -ts 14,13` at `q8_0/q8_0`, unmeasured) or a third card;
- code profile: `--temp 0.6` (the card lists 0.6 for general work and 1.0 only
  for benchmark reproduction). This script was historically the reason the Ornith
  template gained a `reasoning_effort` block at all; nothing is left of that — the
  level is hard-coded in `qwen-general.jinja` and the script passes no effort flag.

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
- it passes `qwen-general.jinja`, like every script (see below); that template
  hard-codes the effort level, prepending the `xhigh` coding instruction
  (see “Chat templates”) to the system block — which is what this coding config
  wants anyway. The script passes no effort flag; there is no way to pass one that
  would do anything;
- the weights are 22 920 MiB — ~1 530 MiB heavier than lmstudio's Q6_K (21 392 MiB),
  so it runs at `-c 262144 -ts 12,11,7 -b 2048 -ub 256`: `12,11,7` + `-ub 256` is
  the geometry measured fastest on this bench (32.2 vs 30.1 t/s for
  `11,10,9` + `-ub 512`), and `-ub 256` halves the compute buffer (≈ 1.6 GiB per
  card, `CALCULATE.md` §6.4) — that is the headroom the heavier weights need.
  Measured at that setting: `nvidia-smi` 13 304 / 14 069 / 12 382 MiB of 16 311
  (GPU1 includes ~1 600 MiB of desktop usage), nothing on CPU, 32.1 t/s generation
  with MTP accepting 83 % of drafts at `mean len 3.24`. If it OOMs, go
  `-ts 11,11,8`, then `-ctv q4_0`, and only then `-c`;
- it is one of eight scripts with `-cram 24576` (the others are
  `davidau-qwen38-27-turbo-4k_m.bat`, `qwen-qwen38-27-4km.bat`,
  `daslab-qwen38-27-iq3_s.bat`, `ukisai-swift15-qwen38-27-iq3_s.bat`,
  `bytkim-qwen38-27-pi-4km.bat`, `unsloth-agentworld-35-5km.bat` and
  `venastine-xing4-29-a4b-5km.bat`): the
  default 8 GiB prompt cache cannot
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
(`--temp 0.6`, penalties spelled out) and the same
`qwen-general.jinja`. It has **not** been measured yet — `-ub 128` halves the
compute buffer relative to `-ub 256`, which is presumably the headroom the
heavier Q4_K_M weights need, but that is inference, not a logged run.

`bytkim-qwen38-27-pi-4km.bat` runs `Qwen3.8-27B-pi-Q4_K_M.gguf`
(`c:\Users\viktor\.lmstudio\models\bytkim\Qwen3.8-27B-pi-GGUF\`), bytkim's "pi" fine-tune of
Qwen3.8-27B (SFT on successful coding-agent sessions, then GRPO with a reasoning-efficiency reward).
Unlike the other Qwen3.8 configs, the main GGUF has **no** MTP head — no `blk.64.*`, no
`nextn_predict_layers` — so it is 64 blocks, not 65. The head ships as a separate file,
`mtp/mtp-Qwen3.8-27B-pi-Q4_0.gguf` (2 008 054 464 B = 1.87 GiB), passed with `-md` and
`--spec-type draft-mtp`. `-ngld 99` keeps the draft fully on GPU: `-ngld` defaults to `auto`,
and `--fit` is on by default, so the head could otherwise fall to CPU without a loud failure.

- Geometry is the Qwen3.8-27B one (`qwen35`, `d 5120`, `n_head_kv 4`, `key/value_length 256`,
  `full_attention_interval 4`, native context 262144), so the body's KV/RS figures in `CALCULATE.md`
  §6 apply. The head adds its own draft KV and compute buffer, as on the other MTP configs.
- Sampling is the card's thinking-mode set `--temp 1.0 --top-k 20 --top-p 0.95 --min-p 0.0`, the same
  as `qwen-qwen38-27-4km.bat`. Do not lower the temperature to 0.6 here either (loops inside `<think>`).
  No penalties: the card sets none for thinking mode.
- `--spec-draft-n-max 2`, not the card's 3: on the DASLab file `n-max 3` lowered MTP acceptance from
  ~76 % to ~71 % and added ~1 GiB of draft compute buffer.
- Two cards, `-ts 17,13 -c 262144`, `q8_0/q8_0`, `-b 2048 -ub 128` (the `davidau-*-4k_m` batch/ubatch
  pair, to halve the compute buffer). **Not measured.** The VRAM budget is an estimate only; CUDA1
  is expected to be the tight card, as on every Qwen3.8 config here.
- Vision is off (`--no-mmproj`); `mmproj-Qwen3.8-27B-pi-BF16.gguf` (931 MB) sits next to the model.
- If it OOMs, in this order: `-ctkd q8_0 -ctvd q8_0` (draft KV f16 → q8_0, −480 MiB measured on the
  DASLab file) → `-devd CUDA0` (move the head off the tight card) → `-c 229376` → `-ngl` last.
  Do not use `-ctv q4_0`: there is no FA kernel for that pair.

`unsloth-agentworld-35-5km.bat` runs `Qwen-AgentWorld-35B-A3B-UD-Q5_K_M.gguf`
(`c:\Users\viktor\.lmstudio\models\unsloth\Qwen-AgentWorld-35B-A3B-GGUF\`), Qwen's AgentWorld 35B-A3B
in Unsloth's Q5_K_M quant. The model card frames it as a *world model*: it thinks, then predicts the
environment's observation for an agent action. It is not a coding-tuned release, so the code profile
here (`--temp 0.6`) is this repo's choice rather than the card's. Arch `qwen35moe`, the same MoE and
hybrid geometry as the Ornith scripts (40 blocks, 256 experts / 8 active + shared, `n_head_kv 2`,
`full_attention_interval 4`, native context 262144; `q8_0/q8_0` is 10 880 B/token). Differences from the
Ornith script it was copied from:

- **No MTP head.** 40 blocks and no `blk.40.nextn.*` (the Ornith GGUF has 41 with the head), so the
  script has no `--spec-*` flags at all;
- GPU-resident weights ≈ 24 704 MiB: `blk.*` 24 189 MiB plus `output.weight` 515 MiB (Q8_0, untied).
  `token_embd` 515 MiB stays host-mapped. The file is 24.64 GiB;
- `-ts 1,1 -ub 128 -c 262144`, from a dry run of `llama-fit-params.exe` with the cards free and
  `--fit-target 0`. Margin is free VRAM after projected use, against the fitter's per-card budget
  (15 138 MiB CUDA0 / 15 142 MiB CUDA1):

  | config | CUDA0 margin | CUDA1 margin |
  | --- | --- | --- |
  | `-ts 14,13 -ub 256` (the Ornith split) | −542 (OOM) | +1189 |
  | `-ts 12,13 -ub 256` | +669 | −22 (OOM) |
  | `-ts 1,1 -ub 256` | +64 | +586 |
  | `-ts 1,1 -ub 160` | +275 | +793 |
  | **`-ts 1,1 -ub 128`** (in the script) | **+346** | **+862** |
  | `-ts 1,1 -ub 128 -c 229376` | +612 | +1128 |

  Blocks are ~600–660 MiB each and cannot be split, so `1,1` is the most even split available. These
  are projections; the one real reading is at the end of this section;
- `-ot "output.weight=CUDA0"` would add ~600 MiB of margin on the tight card, but it changes the graph
  layout (compute buffers shrink, CUDA0 795 → 590 MiB), so it needs a server-log check for pipeline
  parallelism before it is trusted. It is not used;
- `-cram 24576` is kept for consistency with the other hybrid configs. KV per token here is about a
  third of Qwen3.8's, so the default 8 GiB may well be enough. Not tested either way;
- `--reasoning-budget -1` is spelled out (unlimited thinking, already the default). Vision is off
  (`--no-mmproj`); no mmproj is in the model directory;
- if it OOMs: `-c 229376`, then `-c 196608`, then `-ngl` last. `-ctv q4_0` is not an option (no FA
  kernel for that pair).

**Measured once.** Cards free, `-c 262144 -ts 1,1 -ub 128 -cram 24576`, after load and one request of
~2 130 generated tokens (`finish_reason stop`, reasoning in `reasoning_content`, valid code in `content`):
`nvidia-smi` read **15 028 / 14 512 MiB** of 16 311 (about 1 020 / 1 540 MiB free against the 16 050 MiB
base used elsewhere in this file). Generation was ~102 t/s on that one short prompt; this config has no
MTP head, so there is no draft-acceptance figure. One sample is not an A/B. At start the log prints
`failed to fit params … n_gpu_layers already set by user to 99, abort`; that is a warning, and the
server still comes up.

`unsloth-qwen38-27-6km-test.bat` — a three-card experiment for UD-Q6_K_M, the only
script with `-ot "token_embd.weight=CUDA0"` and a skewed `-ts 12,11,7` — **no longer
exists in `cuda13/`**; it was deleted at some point and the docs kept describing it.
The reason for that skew still holds everywhere else: GPU2 sits on a Gen4 x4 link,
so layers are moved off it.

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
- that ~3 GiB of slack is **not** spent. Spending it on a bigger `-ub`, on
  deeper MTP speculation, or on a coarser draft KV was tried by measurement on
  2026-10-06 and reverted — each change is either free of benefit or actively
  worse, see the numbers below. Free VRAM is not scarce on this config;
- **measured 2026-10-06** (cards free, `--verbose`, one ~2 885-token code prompt,
  several repeats per setting):
  - `-ub 384` instead of 256 buys **nothing** on prefill: 1 091–1 095 t/s versus
    1 083–1 089 t/s (+0.7 %, two bands that barely separate) while costing
    +308 MiB of main compute buffer on CUDA0 and +286 on CUDA1. Reverted;
  - `--spec-draft-n-max 3` instead of 2 **lowers** MTP acceptance from ~76 % to
    ~71 % (five samples each, both at `-ub 256`) with generation inside the noise
    band (means 37.6 vs 38.0 t/s). It also costs +1 004 MiB of draft compute
    buffer (613.03 → 1 617.09 MiB) **and** +150 MiB of RS, because `rs_seq` tracks
    `n-max + 1` (RS 448.88 → 598.50 MiB). Reverted;
  - `-ctkd q8_0 -ctvd q8_0` **does work as intended** — the draft KV drops from
    1 024.00 MiB (K/V `f16`, 512 each) to 544.00 MiB (K/V `q8_0`, 272 each),
    against the main context's `q8_0/q8_0` pair whose kernel is known to exist.
    It is **not** applied: its only purpose was to fund the two changes above.
    Keep it in reserve if margin is ever actually needed;
- prefill here is highly reproducible once warm: the first request after load
  reads ~15 % low and must be discarded, after which six repeats spread less than
  1 % and land at **~1 085 t/s** on `-ub 256`. (The `~595 t/s` quoted elsewhere in
  the docs belongs to the heavier DavidAU Q6_K three-card config, not this one);
- generation on that prompt ranges **35–42 t/s** run to run for *identical*
  settings — the spread is stochastic draft acceptance at `temp 0.6`, not the
  config. Never read a single generation sample as an A/B; the earlier
  "44.6 t/s / 78.5 %" figure came from a different code prompt and predates this
  work. Thinking is on and unlimited, so a short `max_tokens` is consumed
  entirely by `reasoning_content` — budget accordingly when testing;
- when measuring, the cards must be **free**: this build has `-fit/--fit` **on by
  default** ("adjust unset arguments to fit in device memory", target 1024
  MiB/device), so a run on cards that are merely *idle* rather than *empty* —
  LM Studio holds ~15 GiB per card without using it — can silently down-adjust
  unset arguments instead of failing loudly, and the numbers would then describe
  a different config than the script names;
- a client-supplied `reasoning_effort` is ignored: `qwen-general.jinja` hard-codes
  the level, and `high` or `max` no longer produce a template error either, they
  simply change nothing. `--reasoning-budget -1` (a different flag — the token
  budget for thinking, **not** a no-op) is the unrestricted default, spelled out
  here and in `qwen-qwen38-27-4km.bat`;
- the GSQ-RCO model's own sampling defaults are baked into the GGUF as
  `temp 1.0 / top-k 20 / top-p 0.95 / min-p 0.0`; the script overrides `temp` to
  `0.6` for the repo's code profile (the model card recommends no sampling values
  at all) and spells out the zero penalties, as on the other MTP configs;
- vision is off (`--no-mmproj`) even though `mmproj-Qwen3.8-27B-BF16.gguf`
  (931 MB) sits next to the model — add `--mmproj` to enable it, the ~910 MiB
  still fits in the slack;
- if it ever OOMs: `-ctkd q8_0 -ctvd q8_0` first (measured lever, −480 MiB on the
  tight card, see above) → `-ub 128` → `-ctv q4_0` →
  `-ot "output.weight=CUDA0"` → `-c 229376` → `-ngl` last.

`ukisai-swift15-qwen38-27-iq3_s.bat` runs `Swift-1.5-Qwen3.8-27B-GSQ-RCO-IQ3_S-mtp.gguf`
(`c:\Users\viktor\.lmstudio\models\ukisai\Swift-1.5-Qwen3.8-27B-GSQ-RCO-GGUF\`) — a post-trained
(agentic / long-horizon / coding) derivative of Qwen3.8-27B, quantised with the same GSQ-RCO recipe
as the DASLab file. The GGUF header has the same geometry (`qwen35`, 65 blocks, `nextn_predict_layers 1`,
`n_head_kv 4`, `key/value_length 256`, `full_attention_interval 4`, 866 tensors), so the `daslab-*`
section above applies unchanged: `-ts 17,13`, `-c 262144`, `q8_0/q8_0`, `-ub 256`, `-cram 24576`,
`--spec-type draft-mtp`. The file is 12 120 016 896 B, +10.5 MiB over the DASLab one, so the VRAM
budget is the same in practice — but the config is **not measured**; every number in the `daslab-*`
section belongs to the DASLab file.

What differs from the DASLab config:

- `--temp 1.0` instead of `0.6`. The GGUF and the Swift 1.5 card both carry
  `temp 1.0 / top-k 20 / top-p 0.95 / min-p 0.0`, and this is the thinking-mode sampler set the
  `qwen-qwen38-27-4km.bat` profile keeps for the same reason: lowering the temperature inside `<think>`
  is the loop failure to avoid. If generation loops or the MTP acceptance is poor, `--temp 0.6` is the
  one-line switch back to the DASLab profile;
- vision is off (`--no-mmproj`): no `mmproj` is published for this release.

`venastine-xing4-29-a4b-5km.bat` runs `Xing4.0-29B-A4B-Q5_K_M.gguf`
(`c:\Users\viktor\.lmstudio\models\Venastine-Research\Xing4.0-29B-A4B-GGUF\`) — China Telecom
AI's Xing4.0-29B-A4B (Apache-2.0; the XingChen/TeleChat line), an agentic MoE, quantised by
Venastine-Research. The folder holds that one file and a `config.json` — no `mmproj`, no separate
MTP file, no template file. **This model does not run on this bench**, and the script exists so the
config is ready the day it does. The agreed route is to **wait for the upstream merge** and update
`c:\Llamacpp\cuda13\` in place — not to build the `xing4_0-port` fork locally (no cmake, CUDA
Toolkit or Visual Studio on this box anyway). So do not propose building a fork again; when a build
with `xing4` in it lands, the script below runs unchanged:

- **`general.architecture` is `xing4_0`, which stock llama.cpp does not implement.** The local
  build in `c:\Llamacpp\cuda13\` (15.10.2026 — it has `deepseek4.cpp`, `qwen35.cpp`,
  `glm5-next.cpp`, `hy-v4.cpp`) has no `xing4` string in any DLL, and neither do the LM Studio
  runtimes up to `llama.cpp-win-x86_64-nvidia-cuda-2.58.1`. Loading it fails in 0.24 s with
  `llama_model_load: error loading model: unknown model architecture: 'xing4_0'`, before any VRAM
  is touched. Support lives only in the unmerged upstream PRs **#29012** and **#29141**
  (branch `xing4_0-port`), which also add the GGML ops the architecture needs
  (`XING4_0_HC_PRE` / `HC_COMB` / `HC_POST`, or the DeepSeek-V4 mHC ops it was rebased onto).
  Check those two PRs for merge status rather than re-diagnosing the failure;
- the architecture is a **pure transformer**, not a hybrid: MLA attention (DeepSeek-V3 style) +
  MoE + Multi-headed Hyper-Connections. 41 blocks, of which `blk.40` is the built-in MTP head
  (`nextn_predict_layers = 1`, tensors `blk.40.nextn.*`), so `--spec-type draft-mtp` applies with
  no `-md` file;
- geometry: `d 3584`, 32 heads, `head_count_kv` **1** (MLA compresses KV), `q_lora_rank 768`,
  `kv_lora_rank 512`, `attention.key_length` **576**, `attention.value_length` **512**;
  MoE with 64 experts / 4 active + 1 shared, `expert_ff 1024`; first 2 blocks dense
  (`leading_dense_block_count 2`); native context 262144 with YaRN (factor 64 from 4096);
  vocab 131072, SPM tokenizer; `tie_word_embeddings` false;
- **its own chat template, not ChatML.** The GGUF carries a Xing template built on
  `<_system>` / `<_user>` / `<_bot>` / `<_end>`, `<tools>` for function signatures and
  `<tool_call>{name}<param_key>…</param_key><param_value>…</param_value></tool_call>` for calls.
  `qwen-general.jinja` is useless here; this script passes `xing4-general.jinja`, see “Chat templates”;
- **why three cards.** GPU-resident weights are 20 869.1 MiB (`blk.*` 20 501.597 + `output.weight`
  367.500 + `output_norm`; `token_embd.weight` 308.0 MiB stays host-mapped) and the MLA KV cache
  costs (576 + 512) elements per token per layer — 46 240 B/token at `q8_0`, i.e. **11 560 MiB** at
  `-c 262144`, plus 289 MiB for the draft layer. 20 869 + 11 560 = 32 429 MiB is already over the
  two cards' 32 100 MiB before any compute buffer, so two cards cannot run the native context.
  Full budget ≈ 33 000–34 000 MiB of 48 150;
- **`-ts 16,15,10`** is the three-card ratio of `davidau-qwen38-27-turbo-6k.bat` (`12,11,7` on
  65 blocks) scaled to 41 blocks — a skew away from GPU2 on its Gen4 x4 link. Because layers are
  indivisible and alternate between 490.191 and 520.406 MiB (`ffn_down_exps` is Q6_K in 19 of the
  39 MoE blocks), it lands as **17 / 16 / 8 blocks** → 8 233.1 / 7 503.9 / 4 764.6 MiB of weights
  plus 4 913 / 4 624 / 2 312 MiB of KV. CUDA0 is the loaded card (~14 750 of 16 050 with a
  ~1 600 MiB compute buffer). The MTP head `blk.40` (1 151.978 MiB) is the last block, so it and
  its draft KV + draft graph sit on GPU2 — use `-devd CUDA0` if that turns out to cost throughput,
  as in `bytkim-qwen38-27-pi-4km.bat`. **Nothing here is measured**; the tensor sizes are exact
  (from the GGUF tensor table), the KV and compute figures are estimates;
- sampling is the model's own thinking-mode set — `--temp 1.0 --top-k 20 --top-p 0.95 --min-p 0.0`
  plus `--repeat-penalty 1.05`, which is what the GGUF carries as `general.sampling.*`. That is the
  `qwen-qwen38-27-4km.bat` / `bytkim-*` choice, not the repo's `0.6` code profile, and for the same
  reason: this model thinks by default and the template's `enable_thinking` is the only lever;
- if it OOMs, in this order: `-devd CUDA0` → `-ts 15,15,11` → `-ub 128` → `-c 229376` → `-ngl`
  last. Do **not** reach for `-ctv q4_0`: besides this repo's findings about the `q8_0`/`q4_0`
  pair, ports of this architecture report that quantised KV is silently ignored on it.

`unsloth-qwen38-27-nvfp4-vllm.bat` is the one script here that does **not** run llama.cpp.
It serves `unsloth/Qwen3.8-27B-NVFP4` — safetensors, not GGUF — through **vLLM 0.30.0 inside
WSL2**, so `-c` / `-ts` / `-ctk` / `-ub` / `-ngl` and all of `CALCULATE.md` are irrelevant to it.
Reference: <https://unsloth.ai/docs/models/qwen3.8> and the model card.

- the quant is `compressed-tensors` **mixed-precision**: MLP in NVFP4 (W4A4, group 16),
  attention + `lm_head` in FP8 W8A8, a static FP8 `kv_cache_scheme`, ViT left in bf16. NVFP4
  needs Blackwell, which these cards are. On sm120 vLLM picked real cutlass paths, not
  fallbacks: `FlashInferCutlassNvFp4LinearKernel`, `CutlassFP8ScaledMMLinearKernel`,
  `FLASHINFER` attention (`arch=sm120`, `kv_cache_dtype=torch.float8_e4m3fn`, decode via `xqa`)
  and `FlashInfer GDN prefill kernel` for the DeltaNet layers;
- geometry is the Qwen3.8-27B one: 64 blocks, `full_attention_interval 4` → 16 attention and
  48 Gated-DeltaNet layers, `n_head_kv 4`, `head_dim 256`, native context 262144. The MTP head
  ships as a separate `model_mtp.safetensors` (bf16, 810 MB) but is listed in
  `model.safetensors.index.json`, so `--speculative-config.method mtp` finds it with no `-md`
  equivalent. `num_speculative_tokens 2` is the guide's own value and matches what this repo
  settled on for llama.cpp;
- **everything lives inside the WSL distro `Unsloth-Engines-6133eb79`** (Ubuntu 24.04), set up by
  Unsloth Desktop. There is no Python, pip, nvcc or docker on the Windows side at all. vLLM is at
  `/opt/unsloth/engines/vllm/env-<hash>/bin/vllm` (the `<hash>` is install-specific — list the
  directory, do not assume it), and the model sits in that distro's own HF cache
  (`HF_HOME=/opt/unsloth/hf`) on ext4 as well as in `C:\Users\viktor\.cache\huggingface`. Prefer
  the in-distro copy: `/mnt/c` goes through drvfs and is far slower for 21 GB;
- **the four environment variables are the whole trick.** Without them the server dies two to
  three minutes in, *after* loading the weights, with a different error each time — this cost four
  runs to work out, so do not strip them:
  - `CUDA_HOME=<env>/cuda` — flashinfer JIT-compiles the prefill kernel and
    `flashinfer/jit/cpp_ext.py:get_cuda_path()` reads this var; the bundled toolkit (nvcc 13.0.88,
    headers, libcudart, nvvm/libdevice) is complete. Otherwise
    `RuntimeError: Could not find nvcc and default cuda_home='/usr/local/cuda' doesn't exist`;
  - `PATH=<env>/bin:<env>/cuda/bin:…` — `ninja` is in the venv's `bin`, and because vllm is
    invoked by absolute path the venv PATH is never activated. Otherwise
    `FileNotFoundError: 'ninja'`;
  - `LIBRARY_PATH=/usr/lib/wsl/lib` — all ten nvcc compiles succeed and only the final link fails
    with `/usr/bin/ld: cannot find -lcuda`. `libcuda.so` is the driver library; in WSL it is in
    `/usr/lib/wsl/lib/` (both `.so` and `.so.1` are there) but `ldconfig` registers only
    `libcuda.so.1` and that directory is in no linker search path. No symlink needed;
  - `MAX_JOBS=4` — ninja otherwise runs all 11 nvcc jobs at once, and *both* TP workers do it
    simultaneously: 22 `cicc` processes at ~2 GB each. That OOM-killed a worker
    (`died unexpectedly (exit code: -9)`) and wedged the whole WSL VM into swap. flashinfer
    honours `MAX_JOBS` and passes it to ninja as `-j`. Related: `C:\Users\viktor\.wslconfig` was
    created with `memory=48GB` / `swap=16GB`, because WSL defaults to half of host RAM (30 GB)
    and the log then read `Available RAM: 24.28 GiB` against a 21.81 GiB checkpoint;
- **`--host 0.0.0.0`, never `127.0.0.1`.** WSL2 is behind NAT and its localhost forwarding only
  reaches a listener bound to all interfaces. This is the one place the script must differ from
  every llama.cpp script here;
- `CUDA_DEVICE_ORDER` / `CUDA_VISIBLE_DEVICES` go **inside the `env` block**, not through `set` as
  in the llama.cpp scripts: the process runs in Linux and never sees Windows variables;
- `-tp 2` is forced, not chosen: tensor parallelism must divide `num_key_value_heads = 4`, so a
  third card would be useless (3 does not divide 4) — it would take a fourth card, or pipeline
  parallelism;
- nothing can quietly land on the CPU: vLLM has no `-ngl` equivalent, `--cpu-offload-gb 0` is
  spelled out, and `--swap-space` no longer exists in 0.30 (V1 preempts by recompute, so there is
  no CPU KV swap at all). The log says `device_config=cuda` and that is the only placement;
- **measured 2026-10-20, cards free, the flags now in the script** (`--max-model-len 139264
  --max-num-seqs 1 --max-num-batched-tokens 1024 --cudagraph-capture-sizes 1 2 4
  --gpu-memory-utilization 0.905 --language-model-only`, fp8 KV, MTP n=2): available KV
  **2.67 GiB/card**, `GPU KV cache size: 142,049 tokens, Maximum concurrency for 139,264 tokens
  per request: 1.02x`, `nvidia-smi` **15 721 / 15 833 MiB** of 16 311 under load, nothing on CPU,
  **~42 t/s** generation (2 605 tokens, of which 2 379 reasoning, in 62 s) with
  `Draft acceptance rate: 72–79 %` across runs, and prefill **~1 600 t/s** (94 067-token prompt in 61 s).
  A 134 016-token prompt runs fine and peaks the pool at `GPU KV cache usage: 89.4%`.
  The previous setting was 122880 at `--max-num-seqs 4 --gpu-memory-utilization 0.90` with the
  two `--limit-mm-per-prompt` flags: available KV 2.41 GiB, 127 022 tokens, 41–48 t/s — i.e. the
  change buys +16 384 tokens of context and costs nothing measurable in speed.
  `init engine` takes ~145 s cold (44 s of torch.compile) and ~50 s once the compile and
  flashinfer caches are warm — the first start after any change to the launch flags is the slow one;
- **how that ceiling was found** (probe = start with `--max-model-len 262144` and read either
  `GPU KV cache size` or `… estimated maximum model length is N`; all runs on free cards):

  | flags | available KV/card | estimated max len |
  | --- | --- | --- |
  | the old config | 2.34 GiB | 124 800 |
  | `--language-model-only --skip-mm-profiling --max-num-seqs 1 --cudagraph-capture-sizes 1 2 4` | 2.52 GiB | 134 400 |
  | + `--max-num-batched-tokens 1024 --gpu-memory-utilization 0.905` | **2.67 GiB** | **142 400** |
  | + `--mamba-ssm-cache-dtype bfloat16` | 2.67 GiB, need 4.57 → 4.42 GiB | ~158 000 (derived, not probed on this path) |

  `--skip-mm-profiling` turned out to be redundant once `--language-model-only` is passed (same
  2.67 GiB with and without), so the script does not carry it. `--prefix-cache-retention-interval 0`
  is the **default** (`config/cache.py:148`) — passing it changes nothing. `--max-num-batched-tokens
  512` buys only 1 600 tokens over 1024 and halves the prefill chunk again, so 1024 it is.
  `--max-num-seqs 1` costs nothing real: concurrency was already 1.03x at 122880;
- **two traps that look like free memory and are not.**
  `VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS=0` (the log suggests it) raises the *reported*
  available KV to 3.43 GiB and the estimate to 190 400, but the pool then does not fit: the
  allocation of 3.22 GiB dies with `CUDA out of memory … 2.35 GiB is free`. The accounting is
  right and the estimate is the mirage. `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` adds
  ~0.14 GiB on paper and breaks startup inside WSL with
  `RuntimeError: CUDA driver error: device not ready` while allocating the KV buffer;
- **Two scripts since 2026-10-21, two incompatible optima.**
  `unsloth-qwen38-27-nvfp4-vllm.bat` is the **long-context** one: `--kv-cache-dtype
  int4_per_token_head --attention-backend TRITON_ATTN`, `--max-model-len 262144`,
  `--max-num-batched-tokens 2048`, `--cudagraph-capture-sizes 1 2 3 4`, MTP `n=3`. int4 is declared
  only by the Triton backend (`triton_attn.py`), 264 B/slot against 512 for fp8. Measured: pool
  301 465 tokens at 262144, decode 44–54 t/s (9 `smoke` runs, mean 47 against 44 at `n=2`, noisy),
  `needle 120000` 3/3, but **prefill only ~476 t/s** (119 940 tokens in 252 s). `n=3` costs ~15k
  pool tokens (316 194 at `n=2`) and lowers the acceptance rate (53 % against 61 % in the same
  kind of log) while still being faster in t/s.
  `unsloth-qwen38-27-nvfp4-vllm-fast.bat` is the **interactive** one: fp8 KV, FlashInfer, 139264,
  `-batched-tokens 1024`, `n=2` (`n=3` drops the estimated maximum to 139 200 and the start fails).
  Measured: pool 146 227, `needle 120000` 3/3 in 89 s — **~1 350 t/s prefill, 2.8× faster**.
  The chunk size is not the lever (1024 → 2048 → 4096 changed nothing on Triton): the backend is.
  The log's `Avg prompt throughput` lies on long requests (the logger stays silent for minutes and
  then books the whole prefill into one 10-second window) — time prefill by the wall clock.
  nvfp4 KV on SM120 is closed by a **gate** (`is_device_capability_family(100)`,
  `flashinfer.py:496` / `interface.py:493`), not only by the bugs listed below. Async scheduling is
  already on with MTP and prefix caching is on; neither needs a flag. Dropping MTP is not a lever;
- (older, written for the 139264 profile) **262144 was out of reach at full speed.** It needs 4.57 GiB/card of KV against the
  2.67 GiB that is actually available, and the startup log spells out why there is no slack left:
  `Free memory on device (14.51/15.9 GiB)` — WSL GPU-PV and the desktop eat ~1.4 GiB before vLLM
  starts — of which 10.99 GiB is weights + non-torch and 0.66 GiB is peak activation. The same
  log suggests `--kv-cache-memory=2903107584` (2.7 GiB) as the "fully utilize" figure, which is
  *below* the 2.74 GiB the current setting already uses, so pinning it would lose context, not
  gain it. Dropping MTP (~0.7 GiB) and `--enforce-eager` (~0.7 GiB, graph capture actually
  measured at 0.00 GiB here, so this one is smaller than it looks) remain the only big levers,
  and both were ruled out on purpose;
- the KV-quant route is **closed by choice**: fp8 is calibrated in the checkpoint
  (`kv_cache_scheme`), while this build also accepts `nvfp4` / `nvfp4_4over6` (FlashInfer
  supports them, `v1/attention/backends/flashinfer.py:411-422`) at ~0.56× the size — enough for
  262144 — plus `fp8_per_token_head`, `int8/int4_per_token_head` and the TurboQuant set on a
  separate Triton backend. NVFP4 KV has no published long-context accuracy data and open bugs on
  exactly this hardware (vLLM #43562: crash on the first request on SM120, workaround fp8;
  #61225: incoherent output on 0.30.0 with the token-major layout; split-KV corruption when a
  short query attends a long cached prefix). Do not switch without a needle-in-a-haystack run.
  On the weight side there is nothing left either: MLP is NVFP4 W4A4, attention / `linear_attn` /
  `lm_head` / layers 56–63 MLP are FP8 W8A8, and the only bf16 masses (the 27-block ViT and the
  810 MB MTP head) are in the quantizer's `ignore` list — the ViT is removed instead, see below;
- `--mamba-ssm-cache-dtype bfloat16` is the one untaken lever: the GDN state is `float32`
  (`mamba_ssm_dtype` in `config.json`, 48 v-heads × 128 × 128 ≈ 3 MiB per layer per sequence) and
  bf16 drops the per-request need from 4.57 to 4.42 GiB, worth about +10 000 tokens. Left off
  until someone A/Bs output quality — NVIDIA's Nemotron 3 paper reports accuracy loss from
  quantizing the mamba cache;
- if it fails to start: `--gpu-memory-utilization` down (0.905 is near the ceiling — 0.95 fails
  immediately with `Free memory on device cuda:0 (14.51/15.9 GiB) … less than desired`) →
  `--max-model-len` down → drop the two `--speculative-config.*` lines → `--enforce-eager` last.
  `--attention-backend TRITON_ATTN` sidesteps the flashinfer JIT entirely if it ever breaks again;
- **vLLM checks the request's `model` field; `llama-server` does not.** Clients configured for the
  llama.cpp scripts send `"model": "Llamacpp"` and got `404 The model 'Llamacpp' does not exist`, so
  `--served-model-name` lists `Llamacpp` as an alias after the real name (the first name is what
  `/v1/models` and responses report). Add any other name a client sends to the same list.
  The `HEAD /api/hello 404` lines in the log are a client's Ollama probe and are harmless;
- **the OpenAI field is `reasoning`, not `reasoning_content`** in vLLM 0.30, and
  `usage.completion_tokens_details.reasoning_tokens` counts it. Do not conclude the reasoning
  parser is broken from an empty `reasoning_content`;
- thinking is on, so a short `max_tokens` is spent entirely inside `<think>` and the reply comes
  back with **both** `reasoning` and `content` empty at `finish_reason: length`. 1200 tokens was
  not enough for a one-line Rust question; budget four figures at minimum;
- **this script uses `chat_template.jinja` in the repo root, not `qwen-general.jinja`** — see
  "Chat templates". That is a deliberate choice and it has a cost: the model's own template
  *does* read `reasoning_effort` and raises on anything outside `xhigh`/`medium`/`low`, so a
  client sending `max`, `minimal` or `none` gets a 500 — the exact trap `qwen-general.jinja` was
  built to remove. It also carries only the plain `xhigh` instruction, not this repo's
  code-oriented preamble. `--default-chat-template-kwargs` is the lever if a fixed effort level
  is ever wanted (`vllm/entrypoints/launchers/cli_args.py:174`);
- vision is off through `--language-model-only`, which is the same as setting every
  `--limit-mm-per-prompt` to 0 but also keeps the ViT out of memory profiling; the two
  `--limit-mm-per-prompt.*` flags it replaced left the ViT weights loaded anyway;
- sampling is **not** passed on the command line: the model's `generation_config.json` already
  carries the card's thinking-mode set (`temperature 1.0`, `top_p 0.95`, `top_k 20`) and vLLM uses
  it as the server default. The guide says the same — `vllm serve` sets no samplers;
- two harmless warnings worth not re-diagnosing. `Add 3 padding layers, may waste at most 6.25%
  KV cache memory`: the hybrid allocator sizes its groups by the smallest bucket — 17 layers
  (16 full-attention + the MTP one) — and pads the 48 GDN layers up to 51, so the 6.25 % is
  `3/48` of the **mamba state**, not an 18.75 % surcharge on the KV cache as an earlier note here
  claimed (`v1/core/kv_cache_utils.py:1538-1560`). And `Speculative
  decoding (method=mtp) is enabled but no KV cache group could be identified as the draft
  model's`. The flashinfer autotuner also logs `OOM detected, falling back to default tactic`
  while probing tactics for `fp4_gemm` — that is by design;
- only one server at a time, as with the llama.cpp scripts: it binds the same port 1234 and wants
  both cards. Orphaned TP workers hold ~11 GiB each after a crash —
  `wsl -d Unsloth-Engines-6133eb79 -- pkill -9 -f vllm`; `pkill -f 'vllm serve'` alone is not
  always enough.

## Chat templates

| file                  | used by                                        |
| --------------------- | ---------------------------------------------- |
| `qwen-general.jinja`  | every llama.cpp script in `cuda13/` except `venastine-xing4-29-a4b-5km.bat` |
| `chat_template.jinja` | only `unsloth-qwen38-27-nvfp4-vllm.bat` (the vLLM one) |
| `xing4-general.jinja` | only `venastine-xing4-29-a4b-5km.bat` |

There are now **three** templates. `qwen-general.jinja` serves every llama.cpp script but one.
`chat_template.jinja` in the repo root is the Qwen3.8-27B template copied verbatim out of the
NVFP4 snapshot (byte-identical to it) and is passed only by `unsloth-qwen38-27-nvfp4-vllm.bat`,
on purpose: that script serves the safetensors model through vLLM. Unlike `qwen-general.jinja`
it reads `reasoning_effort` (default `xhigh`, `high` is mapped to `xhigh`) and raises on
anything else, so a client sending `max`, `minimal` or `none` gets a 500 — the failure mode
the merge into `qwen-general.jinja` was meant to remove. It also lacks this repo’s
code-oriented preamble. Keep the two files in sync only where it matters; they are not
interchangeable by design.
`xing4-general.jinja` serves only `venastine-xing4-29-a4b-5km.bat`, because that model
speaks a different protocol altogether — see the end of this section. `agentworld-35.jinja`
(an unpatched older base for a different family, referenced by no script) was
deleted on 2026-10-07, so docs that still mention it are stale.

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
- **a hard-coded effort level**. The template does **not** read
  `reasoning_effort`: it always prepends the `xhigh` instruction to the system
  block. Since 2026-10-07 that instruction is code-oriented — besides “validate
  assumptions / weigh alternatives / prioritize correctness” it tells the model to
  trace execution with concrete values, derive types and signatures from the code
  given rather than guess them, enumerate every call site a multi-file change
  touches, walk the edge cases explicitly (empty, single element, boundary and
  overflow, negatives, null/missing, concurrency), and re-check its conclusion
  against the source before answering. It is written for
  `qwen-qwen38-27-4km.bat`, but it is in the shared template, so it reaches
  all fifteen scripts that use it — including `ornith-*`, `ukisai-*` and the unsloth
  ones. (`venastine-xing4-29-a4b-5km.bat` gets the same text through
  `xing4-general.jinja` instead, see below.) Keep it short:
  it sits at position 0 of the prompt, so editing it invalidates every `-cram`
  prompt-cache prefix and the next run of each script re-prefills. **This is the
  only place the level is stated.** The scripts used to spell out
  `--reasoning-effort xhigh` as a readable declaration of intent; that line was
  removed from all twelve of them on 2026-10-07, because a flag whose value never
  reaches the prompt is a lie in the config rather than documentation. Do not
  re-add it. The reason the template ignores the variable: the server merges the CLI flag and the
  request body's `reasoning_effort` into one template variable, so a client (a
  chat UI's effort selector, an agent's default) could silently change the prompt
  — or kill the request, since the flag accepts `minimal/low/medium/high/xhigh/max`
  while the old block knew only `xhigh/medium/low` and raised on the rest, and an
  agent sending `reasoning_effort: "high"` got a 500. The only remaining lever is
  `enable_thinking` (`--reasoning on|off|auto`, or
  `chat_template_kwargs` in the request), which still gates the instruction off
  entirely — and which does double duty: with `enable_thinking` false the
  generation prompt gets a closed empty `<think></think>` instead of an open tag,
  so the model skips thinking altogether. No script passes it at the moment —
  `qwen-qwen38-27-4km_no_res.bat` did until it was deleted on 2026-10-07;
- `render_content` with image/video branches (and a `raise_exception` if either
  appears in a system message), though every script runs `--no-mmproj`.

Caveats that survive the merge:

- `unsloth-qwen38-27-{3kxl,4km,5km,6km}.bat` do not spell out `--jinja`, but it
  is on by default in this build, so they render through `qwen-general.jinja`
  like every other script — measured, not assumed. Their GGUF carries a stock
  Qwen3.8 template of its own (which, unlike ours, maps `high` → `xhigh` and
  still raises on `max`/`minimal`), but it is not what gets used;
- the effort instruction is a prompt-level string, not a runtime dial: none of
  these models has effort tiers (the Ornith card says thinking is simply on by
  default). `ornith-ornith15-35-8k.bat` and `qwen-qwen38-27-6k.bat` once passed
  `--reasoning-effort medium`, which injected nothing at all; hard-coding the level
  gave them the `xhigh` instruction, and that is the one prompt change the merge
  caused. The flag itself is gone from every script now, so the whole question is
  historical;
- `agentworld-35.jinja` was left out of the merge and has since been deleted. It
  was an unpatched older base (no `reasoning_effort`, only `messages[0]` as
  system) for a different family, with an audio branch (`<|audio_start|>`) the
  Qwen3.8/Ornith vocabularies do not carry.

`xing4-general.jinja` is a different animal and covers one script only
(`venastine-xing4-29-a4b-5km.bat`). It is the template **embedded in the Xing4.0 GGUF,
copied over verbatim**, with exactly one change: a `{%- set coding_instructions = … %}` line
was added next to `default_system` and that constant is prepended to the system block. The
instruction text is the same string `qwen-general.jinja` uses (the `xhigh` coding preamble), so
both templates state one and the same level. Everything else — markers, tool format, thinking
gate — is the model author's.

- it is **not ChatML**: turns are `<_system>` / `<_user>` / `<_bot>` finished with `<_end>`,
  tools arrive as JSON inside `<tools>`, calls render as
  `<tool_call>{name}<param_key>k</param_key><param_value>v</param_value>…</tool_call>`, and tool
  results come back as `<_observation>` + `<tool_response>`. `qwen-general.jinja` would render
  garbage here, and vice versa;
- it does not reference `reasoning_effort` **at all** — not even by accident — so the failure mode
  documented above (a client sending `high` and getting a 500) cannot happen. `enable_thinking` is
  the only lever, same as everywhere else: false renders a closed empty `<think></think>` in the
  generation prompt, so the model skips thinking;
- the default system prompt is a Chinese persona line for 中国电信星辰语义大模型 / "Xing", emitted
  before our instruction and before any client-supplied system message;
- **it drops `<think>` by itself.** For every assistant turn *before* the last user turn the
  template emits a bare `</think>` regardless of `--reasoning-preserve`, so when a new user turn
  arrives the previous assistant turn is rewritten and the prompt cache breaks from that point (the
  tail, not the prefix — `-cram` still pays off). This is the model author's design, not a flag.

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

Two failure modes look like success and waste a lot of time:

- **LM Studio's own server binds 1234 too.** The script then fails to bind while
  `nvidia-smi` shows the cards idle, so it reads as a VRAM problem. Don't kill by
  process name — re-run on a spare port (`--port 1235`) to confirm, then shut LM
  Studio's server down.
- **`-fit/--fit` is ON by default** in this build ("adjust unset arguments to fit
  in device memory", target 1024 MiB/device), so a run on cards that are merely
  *idle* rather than *empty* (LM Studio parks ~15 GiB per card at 0 % util)
  silently down-adjusts unset arguments instead of failing loudly — and the
  numbers then describe a different config than the script name says. Measure
  only with the cards free.

## Editing conventions

- The model is a **hybrid Transformer + SSM**: only every 4th layer has a KV
  cache; SSM layers hold a fixed-size state that does not grow with context.
  Native context limit is 262144. Before raising `-c` or loosening KV quant,
  work through `CALCULATE.md` §3 and verify against `llama-server.log` — the
  failure signatures (`retrying without pipeline parallelism`,
  `cudaMalloc failed`, `CPU model buffer` on `blk.*`) and the tightening order
  (`-c` ↓ → `-ctv` coarser → `-ctk` coarser → `-ub` ↓ → `-ngl` ↓ last) are in §4.
- **KV quant pairs are not free-form — only the pairs with an FA kernel work.**
  `-ctk` must stay `q8_0`: `f16` K has no CUDA kernel and dumps the graph onto the
  CPU (35 graph splits, all 16 cores pegged, prefill down to ~219 t/s instead of
  ~898) — measured on three cards, and the missing kernel is not card-count
  dependent, so the four `unsloth-*` scripts still carrying `-ctk f16` are
  suspect, not a counter-example. `-ctv q4_0` is worse than useless: there is no
  FA vector kernel for the `q8_0`/`q4_0` pair either, so **both** K and V silently
  convert to `f16` and the cache gets bigger, not smaller. That is why
  `ornith-ornith15-35-6k.bat` OOMs on its first request even though its budget
  says it fits, and why `-ctv q4_0` in a tightening list (`unsloth-*-5km`,
  the `davidau-*` / `daslab-*` fallback orders) cannot be trusted as a lever
  without re-measuring. Prefer `-c` — or `-ub` — instead.
- `unsloth-qwen38-27-5km.bat` carries **two** settings the rest of the repo calls
  broken: `-ts 16,14` (known to OOM on this family — the MTP draft KV, the draft
  compute buffer and `output.weight` all land on the last card) and `-ctv q4_0`.
  It has not been re-measured since those findings; treat it as untested rather
  than as precedent.
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
