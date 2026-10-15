@echo off
set "PATH=C:\Program Files\Git\cmd;C:\Program Files\Git\bin;C:\Program Files\Git\mingw64\bin;%PATH%"
cd /d "%~dp0"
echo ================================================================
echo Pushing Eco-Friendly Routes to GitHub: sovin4391/eco-friendly-routes
echo ================================================================
echo.
git push -u origin main
echo.
echo ================================================================
echo Done!
echo ================================================================
pause

