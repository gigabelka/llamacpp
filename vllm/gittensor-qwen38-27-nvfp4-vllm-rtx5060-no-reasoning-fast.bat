@echo off
title vLLM Server - Qwen3.8-27B NVFP4 RTX5090 @0cc2795 no-reasoning CODE FAST (gittensor, FULL cudagraph, MTP k=4, 2x16GB, WSL2)

REM Tuned variant of gittensor-qwen38-27-nvfp4-vllm-rtx5060-no-reasoning.bat. The context half is
REM   untouched on purpose (--max-model-len 262144, fp8 KV, FlashInfer, --revision 0cc2795, k=4), so
REM   the pool still covers a full 262144-token request. Two lines differ from the base script, both
REM   measured 2026-10-28 on free cards (--host 0.0.0.0 was used for the bench only, not here).
REM
REM 1) NO --compilation-config: the base script forces cudagraph_mode=PIECEWISE (from the reference
REM    recipe), which throws away full-graph decode for nothing. FlashInfer reports UNIFORM_BATCH on
REM    SM120 (xqa, head_dim 256, GQA 24/4) and so do the GDN/mamba backends, so the default
REM    FULL_AND_PIECEWISE survives the spec-decode check and captures FULL graphs at
REM    uniform_decode_query_len = k+1 = 5. That matters here because the log says "Fused multi-step
REM    draft decode is not supported by FLASHINFER; falling back to rebuilding attention metadata
REM    between draft steps" - 4 draft steps per token, so per-launch overhead is what full graphs cut.
REM    Measured (code prompt, 1000 tokens, greedy): 83.9 / 83.2 t/s against 75.2 / 77.5 on PIECEWISE;
REM    4000 tokens at temp 0.7: 84.7 against 74.7 t/s. Prefill unchanged (2712 vs 2752 t/s at 44.5k).
REM    Cost: graph capture takes 3196 tokens of the pool (283,722 -> 280,526) and ~45 s of startup.
REM 2) NO --mamba-cache-dtype / --mamba-ssm-cache-dtype bfloat16: config.json declares
REM    mamba_ssm_dtype float32 and nothing in this repo or the reference has quality data for bf16
REM    (NVIDIA report accuracy loss from quantising the mamba cache), so this is the one accuracy
REM    lever that costs no context. Measured: pool 266,488 tokens, "Maximum concurrency for 262,144
REM    tokens per request: 1.02x", nvidia-smi 15587 / 15568 MiB, decode unchanged (4000 tokens at
REM    temp 0.7: 87.4 t/s). It eats the headroom, so --max-num-batched-tokens can NOT be raised any
REM    more (see below) and needle was re-run because of it: found at ~120k and ~245k tokens.
REM --override-generation-config: temperature 0.3 / top_p 0.95 instead of the card's general
REM   non-thinking 0.7 / 0.80 - for code a low temperature is both more accurate and faster (MTP
REM   acceptance was 78-90 % on code prompts here). This is only a DEFAULT: /v1/messages forwards a
REM   client's temperature / top_p / top_k (entrypoints/anthropic/serving.py:477-491) and Claude Code
REM   sends temperature 1.0, which overrides it. vLLM has no server-side clamp.
REM presence_penalty 0.0, not the card's 1.5: in code the repeated tokens it attacks (indentation,
REM   identifiers, boilerplate) are normal. repetition_penalty 1.0 as in the base script.
REM
REM Measured and REJECTED (do not re-add):
REM   --max-num-seqs 1          decode 66.9-69.4 t/s greedy against 78.7-83.9 with 2. Worse.
REM   --max-num-batched-tokens 8192  engine refuses to start: activations eat the KV pool,
REM                             "estimated maximum model length is 256096" < 262144. 4096 stays.
REM   MTP k=3                   greedy 79.4 t/s mean against 81.9 at k=4; 4000 tokens 75.4 vs 84.7.
REM   flashinfer autotune on    within noise (greedy 82.9-84.9 vs 83.2-83.9) for +80 s of startup
REM                             (init engine 147 s against 65 s). --no-enable-flashinfer-autotune stays.
REM Closed by the build / the checkpoint, not worth re-opening:
REM   fp8 KV runs on UNIT scales here (kv_cache_scheme is static fp8 but the checkpoint ships no
REM   k_scale/v_scale -> "Using KV cache scaling factor 1.0", "uncalibrated q_scale"). There is no
REM   --calculate-kv-scales in vLLM 0.30.0, fp8_per_token_head (dynamic scales) is declared only by
REM   TRITON_ATTN (triton_attn.py; FlashInfer's list is auto/float16/bfloat16/fp8/fp8_e4m3/fp8_e5m2/
REM   nvfp4/nvfp4_4over6, flashinfer.py:414-423) and Triton costs 3.7x of prefill, and bf16 KV halves
REM   the pool to ~142k, i.e. it breaks 262144. Weights: this checkpoint has attention AND lm_head in
REM   NVFP4 (lm_head.weight_scale_2 in the index; quantization_config.ignore covers only embed_tokens,
REM   the linear_attn conv1d/in_proj, model.visual* and mtp*), so weight precision is a property of
REM   the checkpoint - only a different one (unsloth/ukisai: FP8 attention + lm_head) would change it,
REM   and those need int4 KV at 262144.
REM VLLM_ALLOW_LONG_MAX_MODEL_LEN is NOT passed: max_position_embeddings is 262144, so it allows
REM   nothing and only silences a real check.
REM Everything else is the base script's and documented there: the 0cc2795 pin (later commits have no
REM   MTP head), fp8 KV instead of nvfp4 (gated on SM120 in 0.30.0), --gpu-memory-utilization 0.905
REM   (WSL ceiling), the four WSL variables, the patched chat template, and
REM   --default-chat-template-kwargs enable_thinking:false as the single no-reasoning lever (the same
REM   merged dict also feeds --reasoning-parser qwen3, so the parser starts in CONTENT state; a client
REM   sending chat_template_kwargs {"enable_thinking": true} wins the merge and gets thinking back).
REM For maximum accuracy use the thinking script instead: gittensor-qwen38-27-nvfp4-vllm-rtx5060.bat.

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
  --override-generation-config "{\"temperature\":0.3,\"top_p\":0.95,\"top_k\":20,\"min_p\":0.0,\"presence_penalty\":0.0,\"repetition_penalty\":1.0}" ^
  --language-model-only
pause
