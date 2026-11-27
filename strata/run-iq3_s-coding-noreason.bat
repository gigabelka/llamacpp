@echo off
title Strata Qwen3.8-Flash-Next IQ3_S coding no-reasoning
cd /d "C:\MyProjecs\llamacpp\strata"
call "C:\Users\viktor\AppData\Local\Strata\terminal\current\bin\strata.cmd" serve --profile "C:\MyProjecs\llamacpp\strata\qwen3.8-flash-next-iq3_s.coding-noreason.json" --host 127.0.0.1 --port 8080
if errorlevel 1 pause
