@echo off
echo Starting Frontend, Backend


:: Start Backend
cd backend
start cmd /k "call venv\Scripts\activate && cd prepee-be && python manage.py runserver"

cd ..

:: Start Frontend
cd frontend/prepee-fe/
start cmd /k "npm run dev"
cd ../../

start http://localhost:5173

echo All Servers started
pause
