@echo off
setlocal
cd /d %~dp0
python apps\chatgpt_desktop_companion.py
if errorlevel 1 (
  echo.
  echo Could not start ChatGPT Desktop Work Recorder.
  echo Make sure Python 3.10+ is installed and this repository is set up.
  pause
)
