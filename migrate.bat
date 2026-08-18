@echo off
chcp 65001 >nul
cd /d %~dp0
echo ==============================================
echo  LearnQuest - Updating database (migrate)...
echo ==============================================
python manage.py migrate
echo.
echo Done! If you see "Applying ... OK" lines above, everything is fine.
pause
