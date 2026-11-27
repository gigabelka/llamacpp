@echo off
title Strata Qwen3.8-Flash-Next IQ3_S coding reason
set STRATA_ALLOW_THINKING=1
cd /d "C:\MyProjecs\llamacpp\strata"
call "C:\Users\viktor\AppData\Local\Strata\terminal\current\bin\strata.cmd" serve --profile "C:\MyProjecs\llamacpp\strata\qwen3.8-flash-next-iq3_s.coding-reason.json"
if errorlevel 1 pause
