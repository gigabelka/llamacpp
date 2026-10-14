@echo off
title LLaMA Server - Qwen AgentWorld 35B A3B UD-Q5_K_M (Coding, 2x16GB)
set CUDA_DEVICE_ORDER=PCI_BUS_ID
set CUDA_VISIBLE_DEVICES=0,1

cd /d "%~dp0.."

"c:\Llamacpp\cuda13\llama-server.exe" ^
  -m "c:\Users\viktor\.lmstudio\models\unsloth\Qwen-AgentWorld-35B-A3B-GGUF\Qwen-AgentWorld-35B-A3B-UD-Q5_K_M.gguf" ^
  -ngl 99 ^
  --host 127.0.0.1 ^
  --port 1234 ^
  -sm layer ^
  -ts 1,1 ^
  -c 262144 ^
  -np 1 ^
  -kvu ^
  -n -1 ^
  -b 2048 ^
  -ub 128 ^
  -ctk q8_0 ^
  -ctv q8_0 ^
  -fa on ^
  --no-mmproj ^
  -cram 24576 ^
  --jinja ^
  --chat-template-file ".\qwen-general.jinja" ^
  --reasoning-budget -1 ^
  -t 16 ^
  --threads-batch 16 ^
  --temp 0.6 ^
  --top-k 20 ^
  --top-p 0.95 ^
  --min-p 0.0
pause
