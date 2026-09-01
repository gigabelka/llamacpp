@echo off
title LLaMA Server - Qwen 3.8 27B (Coding Config)
set CUDA_DEVICE_ORDER=PCI_BUS_ID
set CUDA_VISIBLE_DEVICES=0,1

cd /d "%~dp0.."

"c:\Llamacpp\cuda12\llama-server.exe" ^
  -m "c:\Users\viktor\.lmstudio\models\unsloth\Qwen3.8-27B-GGUF\Qwen3.8-27B-UD-Q5_K_M.gguf" ^
  -ngl 99 ^
  --host 127.0.0.1 ^
  --port 1234 ^
  -sm layer ^
  -ts 16,14 ^
  -c 262144 ^
  -np 1 ^
  -kvu ^
  -n -1 ^
  -b 1024 ^
  -ub 256 ^
  -ctk q8_0 ^
  -ctv q4_0 ^
  -fa on ^
  --no-mmproj ^
  --cache-reuse 256 ^
  --chat-template-file ".\configs\qwen38.jinja" ^
  --spec-type draft-mtp ^
  --spec-draft-n-max 4 ^
  --spec-draft-p-min 0.6 ^
  -t 16 ^
  --threads-batch 16 ^
  --temp 0.2 ^
  --top-k 20 ^
  --top-p 0.95 ^
  --min-p 0.05 ^
  --repeat-penalty 1.05 ^
  --repeat-last-n 256 ^
  --dry-multiplier 0.8 ^
  --dry-base 1.75 ^
  --dry-allowed-length 2 ^
  --dry-penalty-last-n 4096 ^
  --log-file ".\llamacpp\llama-server.log"

pause