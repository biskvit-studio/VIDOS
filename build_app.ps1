# Build Script for VIDOS

Write-Host "Starting build process for VIDOS..." -ForegroundColor Cyan

# Ensure Flet and PyInstaller are installed and up to date
.\.venv\Scripts\pip install -U flet pyinstaller

# Compile localization files
Write-Host "Compiling localization Po/Mo catalogs..." -ForegroundColor Cyan
.\.venv\Scripts\python.exe tools/compile_locales.py

# Pack the application into a standalone executable
Write-Host "Packing application using Flet (this may take a minute)..." -ForegroundColor Yellow

.\.venv\Scripts\flet pack main.py -y --name "VIDOS" --icon "assets\vidos_icon.ico" --add-data "assets;assets" --add-data "locales;locales" --product-name "VIDOS" --product-version "1.0.0" --file-version "1.0.0.0" --company-name "Biskvit Studio" --copyright "Copyright © 2026 by Biskvit Studio" --file-description "VIDOS Media Downloader"

Write-Host "Build complete! The standalone executable is located in the 'dist' folder." -ForegroundColor Green
