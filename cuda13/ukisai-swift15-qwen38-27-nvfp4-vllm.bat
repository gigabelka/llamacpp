@echo off
title vLLM Server - Swift-1.5 Qwen3.8-27B NVFP4 (ukisai, 2x16GB, WSL2)

REM ModelOpt MIXED_PRECISION checkpoint (NVFP4 + FP8), pinned to the snapshot in the HF cache.
REM KV stays int4_per_token_head + TRITON_ATTN: the checkpoint has no kv_cache_scheme and no KV scales,
REM   and the model card forbids fp8/nvfp4 KV without them. int4 here uses dynamic per-token-head scales.
REM --dtype bfloat16 is from the model card. mamba SSM state stays at the checkpoint's float32 (the default).
REM The model card says full NVFP4 generation was not tested by the authors: not measured on this bench.
REM VLLM_DISABLED_KERNELS: for ModelOpt FP8 layers vLLM picks FlashInferFP8ScaledMMLinearKernel, whose JIT gemm module
REM   links -lcublas -lcublasLt; the venv has only libcublas.so.13 (nvidia/cu13/lib), so ld fails and the engine dies in
REM   profile_run. Disabling it falls back to CutlassFP8ScaledMMLinearKernel, the one the unsloth checkpoint runs on.

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
  VLLM_DISABLED_KERNELS=FlashInferFP8ScaledMMLinearKernel ^
  /opt/unsloth/engines/vllm/env-ea90944493ff410f9c86ea4c67408701/bin/vllm serve ^
  ukisai/Swift-1.5-Qwen3.8-27b-NVFP4 ^
  --revision 25482027debd5485e8108897ba9fed8d3ba16595 ^
  --served-model-name Swift-1.5-Qwen3.8-27B-NVFP4 Llamacpp ^
  --host 127.0.0.1 ^
  --port 1234 ^
  --dtype bfloat16 ^
  --tensor-parallel-size 2 ^
  --max-model-len 262144 ^
  --max-num-seqs 1 ^
  --max-num-batched-tokens 2048 ^
  --cudagraph-capture-sizes 1 2 3 4 ^
  --gpu-memory-utilization 0.905 ^
  --kv-cache-dtype int4_per_token_head ^
  --attention-backend TRITON_ATTN ^
  --cpu-offload-gb 0 ^
  --chat-template /mnt/c/MyProjecs/llamacpp/chat_template.jinja ^
  --reasoning-parser qwen3 ^
  --tool-call-parser qwen3_xml ^
  --enable-auto-tool-choice ^
  --speculative-config.method mtp ^
  --speculative-config.num_speculative_tokens 3 ^
  --override-generation-config "{\"temperature\":1.0,\"top_p\":0.95,\"top_k\":20,\"min_p\":0.0,\"repetition_penalty\":1.0}" ^
  --language-model-only
pause
