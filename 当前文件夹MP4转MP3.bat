@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

:: Search for MP4 files in current directory
echo Searching for MP4 files in current directory...

:: Check if FFmpeg is available
set "ffmpeg_cmd=ffmpeg"
%ffmpeg_cmd% -version >nul 2>&1
if errorlevel 1 (
    echo Error: FFmpeg not found. Please ensure it's installed and in system PATH, or placed in the same directory as this script.
    pause
    exit /b 1
)

:: Count MP4 files
set "file_count=0"
for %%I in (*.mp4) do set /a "file_count+=1"

:: Check if any MP4 files found
if !file_count! equ 0 (
    echo No MP4 files found in current directory.
    pause
    exit /b 1
)

echo Found !file_count! MP4 file(s), starting conversion to 96kbps MP3...

:: Convert each MP4 file to MP3
for %%I in (*.mp4) do (
    set "output_file=%%~nI.mp3"
    echo Converting: %%I
    :: Main conversion command: -vn (no video), libmp3lame encoder, 96kbps bitrate
    %ffmpeg_cmd% -i "%%I" -vn -c:a libmp3lame -b:a 96k -y "!output_file!" >nul 2>&1
    if !errorlevel! equ 0 (
        echo Success: !output_file!
    ) else (
        echo Failed: %%I
    )
)

echo All files processed.
pause

