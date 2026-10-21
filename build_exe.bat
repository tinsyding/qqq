@echo off
chcp 65001 >nul
echo ======================================================
echo 正在将项目打包为独立的 Windows EXE 程序 (含现代 UI 资源)...
echo ======================================================

REM 使用 PyInstaller 打包为单文件、无黑框的独立可执行程序
pyinstaller --noconsole --onefile --clean --name="错题快速转换助手" --collect-all customtkinter --hidden-import="keyboard" --hidden-import="mouse" --hidden-import="pyperclip" --hidden-import="darkdetect" main.py

echo.
echo ======================================================
echo 打包完成！生成的可执行文件位于 dist\错题快速转换助手.exe
echo ======================================================
pause
