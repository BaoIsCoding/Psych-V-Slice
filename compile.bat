@echo off
cd %USERPROFILE%/Desktop/py
pyinstaller --onefile --windowed --icon=fnf.ico chart_convert.py
pyinstaller --onefile --windowed --icon=fnf.ico character_convert.py

