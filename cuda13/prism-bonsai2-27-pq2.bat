@echo off
title LLaMA Server - Ternary Bonsai 2 27B (PQ2_0)
set CUDA_DEVICE_ORDER=PCI_BUS_ID
set CUDA_VISIBLE_DEVICES=0,1

rem PQ2_0 (ggml type 141/142, prism.hadamard.* keys) is NOT supported by upstream
rem llama.cpp builds - they only accept tensor types in [0, 43). A prism-ml fork
rem build is required; point LLAMA at the directory holding its llama-server.exe
rem (upstream build lives in c:\Llamacpp\cuda13).
set LLAMA=c:\Llamacpp\prism

if not exist "%LLAMA%\llama-server.exe" (
  echo [ERROR] "%LLAMA%\llama-server.exe" not found.
  echo A prism-ml capable llama.cpp build is required - upstream fails with:
  echo   tensor 'output.weight' has invalid ggml type 142 ^(must be below 43^)
  pause
  exit /b 1
)

cd /d "%~dp0.."

"%LLAMA%\llama-server.exe" ^
  -m "c:\Users\viktor\.lmstudio\models\prism-ml\Ternary-Bonsai-2-27B-gguf\Ternary-Bonsai-2-27B-PQ2_0.gguf" ^
  -ngl 99 ^
  --host 127.0.0.1 ^
  --port 1234 ^
  -sm layer ^
  -ts 17,13 ^
  -c 262144 ^
  -np 1 ^
  -kvu ^
  -n -1 ^
  -b 2048 ^
  -ub 512 ^
  -ctk q8_0 ^
  -ctv q8_0 ^
  -fa on ^
  --no-mmproj ^
  --cache-reuse 256 ^
  --jinja ^
  --chat-template-file ".\bonsai2-27.jinja" ^
  --reasoning-effort medium ^
  -t 16 ^
  --threads-batch 16 ^
  --temp 1.0 ^
  --top-k 20 ^
  --top-p 0.95 ^
  --min-p 0.0 ^
  --log-file "%LLAMA%\llama-server.log"

pause
