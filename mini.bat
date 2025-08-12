@echo off
title SkySheet Minifier (Preserves Original Encoding)

echo Starting SkySheet minification with encoding preservation...
python "%~dp0minify_files.py" %*

if %errorlevel% equ 0 (
    echo Minification completed successfully!
) else (
    echo Minification completed with errors. Check output for details.
)

echo Press any key to exit...
pause >nul