@echo off
title LLaMA Server - Ornith 1.5 35B A3B Q6_K (Coding, 2x16GB)
set CUDA_DEVICE_ORDER=PCI_BUS_ID
set CUDA_VISIBLE_DEVICES=0,1

cd /d "%~dp0.."

"c:\Llamacpp\cuda13\llama-server.exe" ^
  -m "c:\Users\viktor\.lmstudio\models\ornith-ai\Ornith-1.5-35B-A3B-GGUF\Ornith-1.5-35B-Q6_K.gguf" ^
  -ngl 99 ^
  --host 127.0.0.1 ^
  --port 1234 ^
  -sm layer ^
  -ts 14,13 ^
  -c 98304 ^
  -np 1 ^
  -kvu ^
  -n -1 ^
  -b 2048 ^
  -ub 256 ^
  -ctk q8_0 ^
  -ctv q4_0 ^
  -fa on ^
  --no-mmproj ^
  --cache-reuse 256 ^
  --jinja ^
  --chat-template-file ".\qwen-general.jinja" ^
  --reasoning-effort xhigh ^
  --spec-type draft-mtp ^
  --spec-draft-n-max 2 ^
  --spec-draft-p-min 0.5 ^
  -t 16 ^
  --threads-batch 16 ^
  --temp 0.6 ^
  --top-k 20 ^
  --top-p 0.95 ^
  --min-p 0.0
pause
