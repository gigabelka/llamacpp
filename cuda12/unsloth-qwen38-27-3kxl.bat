@echo off
title LLaMA Server - Qwen 3.8 27B (Coding Config)
set CUDA_DEVICE_ORDER=PCI_BUS_ID
set CUDA_VISIBLE_DEVICES=0,1

cd /d "%~dp0.."

"c:\Llamacpp\cuda12\llama-server.exe" ^
  -m "c:\Users\viktor\.lmstudio\models\unsloth\Qwen3.8-27B-GGUF\Qwen3.8-27B-UD-Q3_K_XL.gguf" ^
  -ngl 99 ^
  --host 127.0.0.1 ^
  --port 1234 ^
  -sm layer ^
  -ts 17,13 ^
  -c 229376 ^
  -np 1 ^
  -kvu ^
  -n -1 ^
  -b 1024 ^
  -ub 256 ^
  -ctk f16 ^
  -ctv f16 ^
  -fa on ^
  --no-mmproj ^
  --cache-reuse 256 ^
  --chat-template-file ".\qwen38.jinja" ^
  --spec-type draft-mtp ^
  --spec-draft-n-max 6 ^
  --spec-draft-p-min 0.5 ^
  -t 16 ^
  --threads-batch 16 ^
  --temp 0.15 ^
  --top-k 20 ^
  --top-p 0.9 ^
  --min-p 0.05 ^
  --repeat-penalty 1.0 ^
  --repeat-last-n 256 ^
  --dry-multiplier 0.5 ^
  --dry-base 1.75 ^
  --dry-allowed-length 4 ^
  --dry-penalty-last-n 2048 ^
  --log-file "c:\Llamacpp\cuda12\llama-server.log"

pause