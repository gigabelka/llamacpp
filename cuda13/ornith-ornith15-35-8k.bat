@echo off
title LLaMA Server - Ornith 1.5 35B A3B (Coding Config)
set CUDA_DEVICE_ORDER=PCI_BUS_ID
set CUDA_VISIBLE_DEVICES=0,1,2

cd /d "%~dp0.."

"c:\Llamacpp\cuda13\llama-server.exe" ^
  -m "c:\Users\viktor\.lmstudio\models\ornith-ai\Ornith-1.5-35B-A3B-GGUF\Ornith-1.5-35B-Q8k.gguf" ^
  -ngl 99 ^
  --host 127.0.0.1 ^
  --port 1234 ^
  -sm layer ^
  -ts 14,13,13 ^
  -c 262144 ^
  -np 1 ^
  -kvu ^
  -n -1 ^
  -b 2048 ^
  -ub 256 ^
  -ctk q8_0 ^
  -ctv q8_0 ^
  -fa on ^
  --no-mmproj ^
  --cache-reuse 256 ^
  --jinja ^
  --chat-template-file ".\ornith15-35.jinja" ^
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
