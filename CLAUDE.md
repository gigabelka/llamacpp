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
  2× RTX 5060 Ti 16 GB. Treat this as the authoritative reference when changing
  any `-c`, `-ts`, `-ub`, `-ctk`, or `-ctv` value.
- `qwen38-27.jinja`, `bonsai2-27.jinja`, `ornith15-35.jinja` — chat templates passed
  to the server via `--chat-template-file` (one per model family).
- `cuda12/*.bat`, `cuda13/*.bat` — the launch scripts.

There is no build, no test suite, no linter. "Running" the project means
executing one of the `.bat` files (see below).

## Layout of the launch scripts

`cuda12/` and `cuda13/` are **parallel sets** — the same six configs pointed at a
CUDA 12.x vs CUDA 13.x build of `llama-server.exe`. Within each set the scripts
differ only by model file and the VRAM-sensitive knobs:

| script                       | model (GGUF)              | `-c`   | `-ts` | `-ctk`/`-ctv` |
| ---------------------------- | ------------------------- | ------ | ----- | ------------- |
| `qwen-qwen38-27-4km.bat`     | lmstudio-community Q4_K_M | 262144 | 17,13 | q8_0 / q8_0   |
| `unsloth-qwen38-27-3kxl.bat` | unsloth UD-Q3_K_XL        | 229376 | 17,13 | f16 / f16     |
| `unsloth-qwen38-27-4km.bat`  | unsloth UD-Q4_K_M         | 180224 | 17,13 | f16 / f16     |
| `unsloth-qwen38-27-5km.bat`  | unsloth UD-Q5_K_M         | 262144 | 16,14 | q8_0 / q4_0   |
| `unsloth-qwen38-27-6km.bat`  | unsloth UD-Q6_K_M         | 65336  | 17,13 | f16 / f16     |
| `prism-bonsai2-27-pq2.bat`   | prism-ml Bonsai-2 PQ2_0   | 262144 | 17,13 | q8_0 / q8_0   |
| `ornith-ornith15-35-8k.bat` | ornith-ai Ornith-1.5 Q8_0 | 262144 | 14,13,13 | q8_0 / q8_0 |

Everything else (sampling params, `--spec-type draft-mtp`, `-fa on`, `-kvu`,
`-np 1`, `-ub 256`, thread counts, DRY penalties) is identical across the Qwen3.8
scripts. `prism-bonsai2-27-pq2.bat` is the odd one out:

- it runs `Ternary-Bonsai-2-27B-PQ2_0.gguf` (`c:\Users\viktor\.lmstudio\models\prism-ml\`),
  same `qwen35` architecture and geometry as Qwen3.8-27B but 64 blocks and **no**
  `nextn_predict_layers` / MTP tensors — so no `--spec-type draft-mtp` block;
- `PQ2_0` is a prism-ml quant (ggml tensor type 141/142, `prism.hadamard.*` keys) that
  upstream llama.cpp rejects: `invalid ggml type 142. should be in [0, 43)`. The script
  therefore takes the binary directory from a `set LLAMA=` line at the top (default
  `c:\Llamacpp\prism`) and bails out with a hint if no `llama-server.exe` is there;
- vision is off (`--no-mmproj`) even though `Ternary-Bonsai-2-27B-mmproj-BF16.gguf`
  (clip / `qwen3vl_merger`) sits next to the model and `bonsai2-27.jinja` renders
  image/video blocks — add `--mmproj` to that file to enable it (~0.9 GB VRAM).

`ornith-ornith15-35-8k.bat` runs a different model family —
`Ornith-1.5-35B-Q8_0.gguf` (`c:\Users\viktor\.lmstudio\models\ornith-ai\Ornith-1.5-35B-A3B-GGUF\`),
arch `qwen35moe`, supported by both the cuda12 and cuda13 `llama.dll`:

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

**External paths hard-coded in every script** (not in this repo):

- Binaries: `c:\Llamacpp\cuda12\` / `c:\Llamacpp\cuda13\` (`llama-server.exe` + CUDA/GGML DLLs).
- Models: `c:\Users\viktor\.lmstudio\models\...` (LM Studio's model cache).
- Log: `c:\Llamacpp\cudaXX\llama-server.log`.

Each script does `cd /d "%~dp0.."` so it runs from the repo root, which is why
`--chat-template-file ".\qwen38-27.jinja"` resolves.

## Running

```bat
cuda13\unsloth-qwen38-27-4km.bat
```

Server comes up at `http://127.0.0.1:1234` (Web UI, `/v1/chat/completions`,
`/health`). Pick `cuda12` vs `cuda13` to match the installed NVIDIA driver /
CUDA runtime. `pause` at the end keeps the window open on exit.

## Editing conventions

- A change to one script almost always applies to its counterpart in the other
  `cudaXX/` directory — keep the pair in sync unless the change is
  CUDA-version-specific.
- The model is a **hybrid Transformer + SSM**: only every 4th layer has a KV
  cache; SSM layers hold a fixed-size state that does not grow with context.
  Native context limit is 262144. Before raising `-c` or loosening KV quant,
  work through `CALCULATE.md` §3 and verify against `llama-server.log` — the
  failure signatures (`retrying without pipeline parallelism`,
  `cudaMalloc failed`, `CPU model buffer` on `blk.*`) and the tightening order
  (`-c` ↓ → `-ctv` coarser → `-ctk` coarser → `-ub` ↓ → `-ngl` ↓ last) are in §4.
- `-ts 17,13` deliberately skews layers onto GPU0 because KV / SSM / pipeline
  compute buffers land on the higher card under `-sm layer`. Re-check card
  occupancy in `nvidia-smi` after any `-ts`/`-c` change.
- Target bench: Ryzen 9 9950X (16c/32t), 64 GB DDR5, 2× RTX 5060 Ti 16 GB, no
  NVLink/P2P, Windows 11 x64. `-t 16` / `--threads-batch 16` and the split
  values assume this box.
- `README.md` describes an older bundled layout (`configs/`, in-repo `llamacpp/`
  and `models/` dirs) that no longer matches the actual tree — trust the scripts
  and `CALCULATE.md` over the README's path examples.
- Prose docs (`README.md`, `CALCULATE.md`) are written in Russian; keep new
  content in the same language as the file you are editing.
