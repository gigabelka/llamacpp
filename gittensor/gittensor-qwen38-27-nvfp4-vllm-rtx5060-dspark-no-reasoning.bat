@echo off
title vLLM Server - Qwen3.8-27B NVFP4 RTX5090 local + DSpark v2 NVFP4 drafter, no-reasoning CODE (gittensor, DSpark k=7, 2x16GB, WSL2)

cd /d "%~dp0.."

wsl -d vllm -- env ^
  CUDA_DEVICE_ORDER=PCI_BUS_ID ^
  CUDA_VISIBLE_DEVICES=0,1 ^
  HF_HOME=/opt/vllm/hf ^
  HF_HUB_OFFLINE=1 ^
  CUDA_HOME=/usr/local/cuda-13.0 ^
  PATH=/opt/vllm/env/bin:/usr/local/cuda-13.0/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin ^
  LIBRARY_PATH=/usr/lib/wsl/lib ^
  MAX_JOBS=4 ^
  NCCL_P2P_DISABLE=1 ^
  VLLM_FLASHINFER_WORKSPACE_BUFFER_SIZE=67108864 ^
  /opt/vllm/env/bin/vllm serve ^
  /mnt/c/Qwen3.8-27B-NVFP4-RTX5090 ^
  --served-model-name Qwen3.8-27B-NVFP4 Llamacpp ^
  --host 127.0.0.1 ^
  --port 1234 ^
  --tensor-parallel-size 2 ^
  --trust-remote-code ^
  --max-model-len 139264 ^
  --max-num-seqs 2 ^
  --max-num-batched-tokens 4096 ^
  --gpu-memory-utilization 0.905 ^
  --kv-cache-dtype fp8 ^
  --compilation-config "{\"cudagraph_mode\":\"PIECEWISE\"}" ^
  --no-enable-flashinfer-autotune ^
  --cpu-offload-gb 0 ^
  --disable-custom-all-reduce ^
  --reasoning-parser qwen3 ^
  --tool-call-parser qwen3_xml ^
  --enable-auto-tool-choice ^
  --chat-template /mnt/c/MyProjecs/llamacpp/gittensor/chat_template-gittensor.jinja ^
  --default-chat-template-kwargs "{\"enable_thinking\":false}" ^
  --speculative-config.method dspark ^
  --speculative-config.model /opt/vllm/models/Qwen3.8-27B-DSpark-NVFP4 ^
  --speculative-config.num_speculative_tokens 7 ^
  --override-generation-config "{\"temperature\":0.7,\"top_p\":0.8,\"top_k\":20,\"min_p\":0.0,\"presence_penalty\":0.0,\"repetition_penalty\":1.0}" ^
  --language-model-only
pause
