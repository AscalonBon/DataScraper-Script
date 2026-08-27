@echo off
echo 🐾 Building Petdentity Data Scraper
echo ====================================
echo.

echo Step 1: Installing required packages...
pip install -r requirements.txt

echo.
echo Step 2: Installing PyInstaller...
pip install pyinstaller

echo.
echo Step 3: Building executable...
pyinstaller --onefile --windowed --name PetdentityScraper --icon=assets/icon.ico --add-data "assets;assets" --add-data "data;data" --hidden-import=selenium --hidden-import=webdriver_manager --hidden-import=beautifulsoup4 --hidden-import=lxml --hidden-import=PIL --hidden-import=PIL.Image --hidden-import=PIL.ImageTk --hidden-import=bs4.builder._htmlparser --hidden-import=bs4.builder._lxml src/main.py

echo.
echo ✅ Build complete!
echo 📁 Executable: dist\PetdentityScraper.exe
echo.

pause