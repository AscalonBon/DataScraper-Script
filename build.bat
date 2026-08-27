@echo off
echo Building Petdentity Data Scraper with geckodriver
echo =====================================================
echo.

echo Step 1: Installing required packages...
pip install -r requirements.txt

echo.
echo Step 2: Downloading geckodriver...
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/mozilla/geckodriver/releases/download/v0.35.0/geckodriver-v0.35.0-win64.zip' -OutFile 'geckodriver.zip'"
powershell -Command "Expand-Archive -Path 'geckodriver.zip' -DestinationPath '.'"
del geckodriver.zip

echo.
echo Step 3: Building executable with geckodriver...
pyinstaller --onefile --windowed --name PetdentityScraper --icon=assets\icon.ico --add-data "assets;assets" --add-data "data;data" --add-binary "geckodriver.exe;." --hidden-import=selenium --hidden-import=webdriver_manager --hidden-import=beautifulsoup4 --hidden-import=lxml --hidden-import=PIL --hidden-import=PIL.Image --hidden-import=PIL.ImageTk src\main.py

echo.
echo ✅ Build complete!
echo 📁 Executable: dist\PetdentityScraper.exe
echo.

pause