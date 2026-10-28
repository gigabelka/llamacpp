@echo off
title vLLM Server - Qwen3.8-27B NVFP4 RTX5090 @0cc2795 no-reasoning CODE FAST (gittensor, FULL cudagraph, MTP k=4, 2x16GB, WSL2)

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
