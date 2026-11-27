@echo off
title Strata Qwen3.8-Flash-Next IQ3_S coding reason
set STRATA_ALLOW_THINKING=1
cd /d "C:\MyProjecs\llamacpp\strata"
start "Strata engine IQ3_S reason" cmd /k call "C:\Users\viktor\AppData\Local\Strata\terminal\current\bin\strata.cmd" serve --profile "C:\MyProjecs\llamacpp\strata\qwen3.8-flash-next-iq3_s.coding-reason.json"
call "C:\Users\viktor\AppData\Local\Strata\terminal\current\bin\strata.cmd" monitor --url http://127.0.0.1:8080
if errorlevel 1 pause
