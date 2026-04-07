@echo off
REM Build Big Homie executable for Windows

echo Building Big Homie...

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Convert logo to .ico if pillow is available
echo Converting logo...
python -c "from PIL import Image; img = Image.open('logo.png'); img.save('logo.ico', sizes=[(256, 256)])"

REM Build executable
echo Building executable...
pyinstaller big_homie.spec --clean --noconfirm

echo.
echo Build complete!
echo.
echo Executable location: dist\BigHomie.exe
echo.
echo To run: dist\BigHomie.exe
pause
