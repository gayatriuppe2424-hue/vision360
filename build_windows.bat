@echo off
REM Builds dist\Vision360\Vision360.exe  (run from the project folder on Windows)
python -m pip install -r requirements-build.txt || goto :err
python -m PyInstaller --noconfirm --clean --onedir --windowed --name Vision360 ^
  --add-data "face_landmarker.task;." ^
  --add-data "assets\posture_wireframe.png;assets" ^
  --add-data "cat_gatekeeper.gif;." ^
  --add-data "vision360_logo.png;." ^
  --collect-all customtkinter --collect-all mediapipe ^
  vision360_ui.py || goto :err
echo.
echo Done. Run dist\Vision360\Vision360.exe  -- then zip the dist\Vision360 folder to share it.
exit /b 0
:err
echo Build failed.
exit /b 1
