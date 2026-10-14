@echo off
title LLaMA Server - Qwen 3.8 27B pi Q4_K_M (Coding Config, MTP head)
set CUDA_DEVICE_ORDER=PCI_BUS_ID
set CUDA_VISIBLE_DEVICES=0,1

cd /d "%~dp0.."

"c:\Llamacpp\cuda13\llama-server.exe" ^
  -m "c:\Users\viktor\.lmstudio\models\bytkim\Qwen3.8-27B-pi-GGUF\Qwen3.8-27B-pi-Q4_K_M.gguf" ^
  -md "c:\Users\viktor\.lmstudio\models\bytkim\Qwen3.8-27B-pi-GGUF\mtp\mtp-Qwen3.8-27B-pi-Q4_0.gguf" ^
  -ngl 99 ^
  -ngld 99 ^
  --host 127.0.0.1 ^
  --port 1234 ^
  -sm layer ^
  -ts 17,13 ^
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
  --spec-type draft-mtp ^
  --spec-draft-n-max 2 ^
  --spec-draft-p-min 0.5 ^
  -t 16 ^
  --threads-batch 16 ^
  --temp 1.0 ^
  --top-k 20 ^
  --top-p 0.95 ^
  --min-p 0.0
pause
