@echo off
title vLLM Server - Qwen3.8-27B NVFP4 RTX5090 @0cc2795 no-reasoning CODE (gittensor, MTP k=4, 2x16GB, WSL2)

REM Recipe: https://github.com/skrodahl/qwen38-27B-dual-rtx5060 (fp8 KV + FlashInfer + MTP k=4).
REM Differences from the recipe, on purpose:
REM   --gpu-memory-utilization 0.905, not 0.94: under WSL GPU-PV and the desktop take ~1.4 GiB
REM     before vLLM starts, 0.95 fails immediately.
REM   --kv-cache-dtype fp8, not nvfp4: the recipe's nvfp4 numbers come from vLLM 0.32.0rc1.dev100,
REM     this distro has 0.30.0 where nvfp4 KV is closed on SM120.
REM   no PYTORCH_CUDA_ALLOC_CONF=expandable_segments (breaks startup inside WSL), no --load-format
REM     ipc_cache / --api-key (Docker).
REM --chat-template chat_template-gittensor.jinja = the revision's own template with the reasoning-effort
REM   check patched: the stock one raises on "high"/"max" and Claude Code (high) got HTTP 400.
REM The checkpoint is pinned to 0cc2795: later commits have no MTP head, decode falls to ~42 t/s.
REM --mamba-ssm-cache-dtype bfloat16: neither the recipe nor this repo has quality data for it.
REM No-reasoning variant of gittensor-qwen38-27-nvfp4-vllm-rtx5060.bat. Only two flags differ, and
REM   the KV/backend half is unchanged on purpose, so every measurement in CLAUDE.md for the base
REM   script still applies (pool 283,722 tokens at 262144, prefill 2955 t/s at 33k / 1755 t/s at 111k).
REM --default-chat-template-kwargs is the lever, not an edit to the template: the same merged dict
REM   also feeds the reasoning parser, so with enable_thinking=false the template emits a closed empty
REM   <think></think> (chat_template-gittensor.jinja:300) AND the parser starts in CONTENT state.
REM   Without it the whole answer would land in "reasoning" with an empty "content". The request wins
REM   the merge, so a client sending chat_template_kwargs {"enable_thinking": true} gets thinking back
REM   - which is why --reasoning-parser qwen3 stays. Side effect: the reasoning-effort block is skipped
REM   entirely, so neither the xhigh preamble nor an HTTP 400 on "high"/"max" is reachable here.
REM presence_penalty 0.0, not the card's 1.5: in code the repeated tokens it attacks (indentation,
REM   identifiers, boilerplate) are normal, and 0.7/0.80 already suppress looping. Not measured.

cd /d "%~dp0.."

wsl -d Unsloth-Engines-6133eb79 -- env ^
  CUDA_DEVICE_ORDER=PCI_BUS_ID ^
  CUDA_VISIBLE_DEVICES=0,1 ^
  HF_HOME=/opt/unsloth/hf ^
  HF_HUB_OFFLINE=1 ^
  CUDA_HOME=/opt/unsloth/engines/vllm/env-ea90944493ff410f9c86ea4c67408701/cuda ^
  PATH=/opt/unsloth/engines/vllm/env-ea90944493ff410f9c86ea4c67408701/bin:/opt/unsloth/engines/vllm/env-ea90944493ff410f9c86ea4c67408701/cuda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin ^
  LIBRARY_PATH=/usr/lib/wsl/lib ^
  MAX_JOBS=4 ^
  NCCL_P2P_DISABLE=1 ^
  VLLM_ALLOW_LONG_MAX_MODEL_LEN=1 ^
  VLLM_FLASHINFER_WORKSPACE_BUFFER_SIZE=67108864 ^
  /opt/unsloth/engines/vllm/env-ea90944493ff410f9c86ea4c67408701/bin/vllm serve ^
  gittensor-model-hub/Qwen3.8-27B-NVFP4-RTX5090 ^
  --revision 0cc27958cefbbe231782ec8511de8c4eb5233348 ^
  --served-model-name Qwen3.8-27B-NVFP4 Llamacpp ^
  --host 127.0.0.1 ^
  --port 1234 ^
  --tensor-parallel-size 2 ^
  --trust-remote-code ^
  --max-model-len 262144 ^
  --max-num-seqs 2 ^
  --max-num-batched-tokens 4096 ^
  --gpu-memory-utilization 0.905 ^
  --kv-cache-dtype fp8 ^
  --mamba-cache-dtype bfloat16 ^
  --mamba-ssm-cache-dtype bfloat16 ^
  --compilation-config "{\"cudagraph_mode\":\"PIECEWISE\"}" ^
  --no-enable-flashinfer-autotune ^
  --cpu-offload-gb 0 ^
  --disable-custom-all-reduce ^
  --reasoning-parser qwen3 ^
  --tool-call-parser qwen3_xml ^
  --enable-auto-tool-choice ^
  --chat-template /mnt/c/MyProjecs/llamacpp/chat_template-gittensor.jinja ^
  --default-chat-template-kwargs "{\"enable_thinking\":false}" ^
  --speculative-config.method mtp ^
  --speculative-config.num_speculative_tokens 4 ^
  --override-generation-config "{\"temperature\":0.7,\"top_p\":0.8,\"top_k\":20,\"min_p\":0.0,\"presence_penalty\":0.0,\"repetition_penalty\":1.0}" ^
  --language-model-only
pause
