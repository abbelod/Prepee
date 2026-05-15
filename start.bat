@echo off
echo Starting Frontend, Backend, and Matchmaker

:: Start Backend
cd backend
start cmd /k "call venv\Scripts\activate && cd prepee-be && python manage.py runserver"

:: Start Matchmaker Worker
start cmd /k "call venv\Scripts\activate && cd prepee-be && python manage.py run_matchmaker"

cd ..

:: Start Frontend
cd frontend/prepee-fe/
start cmd /k "npm run dev"
cd ../../


:: Start matchmaker worker
cd backend
start cmd /k "call venv\Scripts\activate && cd prepee-be && python manage.py run_matchmaker"
cd ..


start http://localhost:5173

echo All Servers started
pause
