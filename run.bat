@echo off
REM 1. Navigate to your project directory
cd /d "C:\Users\xh421\.star\project-office\depend-player"

REM 2. Initialize Conda (Change the path if your Anaconda/Miniconda is installed elsewhere)
call %USERPROFILE%\anaconda3\Scripts\activate.bat

REM 3. Activate the base environment (or your specific env)
call conda activate base

REM 4. Run the python script
python src/ue_controller.py

pause