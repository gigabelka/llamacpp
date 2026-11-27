@echo off
title Strata Qwen3.8-Flash-Next IQ3_S coding no-reasoning
cd /d "C:\MyProjecs\llamacpp\strata"
call "C:\Users\viktor\AppData\Local\Strata\terminal\current\bin\strata.cmd" launch --preset "IQ3_S 200K"
if errorlevel 1 pause
