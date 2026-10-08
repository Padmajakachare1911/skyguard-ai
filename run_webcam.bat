@echo off
title SkyGuard AI - Live Webcam PPE Detection
color 0A
cls
echo ===================================================================
echo      SKYGUARD AI - REAL-TIME LIVE WEBCAM PPE DETECTOR
echo ===================================================================
echo.
echo  * The camera window will open in FRONT of your screen.
echo  * Hold your phone or construction photo up to your laptop camera.
echo.
echo  HOTKEYS ON CAMERA WINDOW:
echo    [m]       : Switch Model (10-class / 4-class / 6-class)
echo    [+] / [-] : Adjust Detection Sensitivity
echo    [s]       : Capture & Save Snapshot Photo
echo    [q]       : Exit cleanly
echo ===================================================================
echo.
echo Starting Python detector...
echo.
python cv-model\inference\webcam_demo.py
echo.
echo ===================================================================
echo  Webcam detector session finished cleanly.
echo ===================================================================
echo.
pause
