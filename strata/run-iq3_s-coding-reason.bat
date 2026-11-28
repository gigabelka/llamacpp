@echo off
title Strata Qwen3.8-Flash-Next IQ3_S coding reason
set STRATA_ALLOW_THINKING=1
cd /d "C:\MyProjecs\llamacpp\strata"
if not exist "C:\MyProjecs\llamacpp\logs" mkdir "C:\MyProjecs\llamacpp\logs"
if not exist "%APPDATA%\Strata\profiles\iq3_s-coding-reason.json" call "C:\Users\viktor\AppData\Local\Strata\terminal\current\bin\strata.cmd" profile create iq3_s-coding-reason --from-config "C:\MyProjecs\llamacpp\strata\qwen3.8-flash-next-iq3_s.coding-reason.json" --quiet
call "C:\Users\viktor\AppData\Local\Strata\terminal\current\bin\strata.cmd" runtime status --profile iq3_s-coding-reason | findstr /b /c:"iq3_s-coding-reason: ready" /c:"iq3_s-coding-reason: starting" >nul
if not errorlevel 1 goto dashboard
echo Starting the model; the dashboard opens when it is ready ...
call "C:\Users\viktor\AppData\Local\Strata\terminal\current\bin\strata.cmd" runtime start --profile iq3_s-coding-reason --wait 900
if errorlevel 1 (
  call "C:\Users\viktor\AppData\Local\Strata\terminal\current\bin\strata.cmd" status --url http://127.0.0.1:8080 --quiet --json >nul 2>&1
  if not errorlevel 1 echo Another Strata server already serves http://127.0.0.1:8080; stop it to start the reason instance.
  echo Server log: "%LOCALAPPDATA%\Strata\runtime\iq3_s-coding-reason.server.log"
  pause
  exit /b 1
)
:dashboard
call "C:\Users\viktor\AppData\Local\Strata\terminal\current\bin\strata.cmd" monitor --url http://127.0.0.1:8080
if errorlevel 1 pause
