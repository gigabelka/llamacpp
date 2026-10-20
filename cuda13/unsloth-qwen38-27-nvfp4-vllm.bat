@echo off
title vLLM Server - Qwen3.8-27B NVFP4 (Unsloth, 2x16GB, WSL2)

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
  /opt/unsloth/engines/vllm/env-ea90944493ff410f9c86ea4c67408701/bin/vllm serve ^
  unsloth/Qwen3.8-27B-NVFP4 ^
  --served-model-name Qwen3.8-27B-NVFP4 ^
  --host 0.0.0.0 ^
  --port 1234 ^
  --tensor-parallel-size 2 ^
  --max-model-len 122880 ^
  --max-num-seqs 4 ^
  --gpu-memory-utilization 0.90 ^
  --kv-cache-dtype fp8 ^
  --cpu-offload-gb 0 ^
  --chat-template /mnt/c/MyProjecs/llamacpp/chat_template.jinja ^
  --reasoning-parser qwen3 ^
  --tool-call-parser qwen3_xml ^
  --enable-auto-tool-choice ^
  --speculative-config.method mtp ^
  --speculative-config.num_speculative_tokens 2 ^
  --limit-mm-per-prompt.image 0 ^
  --limit-mm-per-prompt.video 0
pause
