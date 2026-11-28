@echo off
title Strata Qwen3.8-Flash-Next NVFP4 coding no-reasoning
cd /d "C:\MyProjecs\llamacpp\strata"
call "C:\Users\viktor\AppData\Local\Strata\terminal\current\bin\strata.cmd" launch --preset "NVFP4 256K"
if errorlevel 1 pause
