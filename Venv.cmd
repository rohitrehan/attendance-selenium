@echo off

rm -rf .venv
py -3.10 -m venv .venv

IF %ERRORLEVEL% NEQ 0 EXIT /B

call .venv\Scripts\activate.bat

python --version
PipCompileRequirements.cmd

python -m pip install -r requirements.txt

