@echo off
title LLaMA Server - Qwen 3.8 27B (Coding Config)
set CUDA_DEVICE_ORDER=PCI_BUS_ID
set CUDA_VISIBLE_DEVICES=0,1,2

cd /d "%~dp0.."

"c:\Llamacpp\cuda13\llama-server.exe" ^
  -m "c:\Users\viktor\.lmstudio\models\unsloth\Qwen3.8-27B-GGUF\Qwen3.8-27B-UD-Q6_K_M.gguf" ^
  -ngl 99 ^
  --host 127.0.0.1 ^
  --port 1234 ^
  -sm layer ^
  -ts 11,10,9 ^
  -c 229376 ^
  -np 1 ^
  -kvu ^
  -n -1 ^
  -b 2048 ^
  -ub 256 ^
  -ctk f16 ^
  -ctv q8_0 ^
  -fa on ^
  --no-mmproj ^
  --cache-reuse 256 ^
  --jinja ^
  --chat-template-file ".\qwen38.jinja" ^
  --reasoning-effort medium ^
  --spec-type draft-mtp ^
  --spec-draft-n-max 2 ^
  --spec-draft-p-min 0.5 ^
  -t 16 ^
  --threads-batch 16 ^
  --temp 1.0 ^
  --top-k 20 ^
  --top-p 0.95 ^
  --min-p 0.0 ^
  --log-file "c:\Llamacpp\cuda13\llama-server.log"

pause