

# Prepee – Quiz App

A full-stack quiz application built using:

* **React + Vite** (Frontend)
* **Django + Django REST Framework** (Backend)

This document explains how to set up and run both the frontend and backend.

---

#  Getting Started

##  Requirements

Make sure you have these installed:

* **Node.js** (>= 18)
* **npm**
* **Python** (>= 3.10)
* **pip**
* **Virtualenv** (optional but recommended)
* **Git**

---

#  Project Structure

```
.
├── frontend/
│   └── prepee-fe/      # Vite + React frontend
└── backend/
    ├── venv/           # Python virtual environment (ignored from Git)
    └── prepee-be/      # Django backend project
```

---

#  Backend Setup (Django)

###  Navigate to the backend folder

```bash
cd backend
```

###  Create virtual environment (if not already created)

```bash
python -m venv venv
```

###  Activate the virtual environment

#### Windows:

```bash
venv\Scripts\activate
```

#### macOS / Linux:

```bash
source venv/bin/activate
```

###  Install backend dependencies

```bash
pip install -r prepee-be/requirements.txt
```

###  Apply migrations

```bash
cd prepee-be
python manage.py migrate
```

###  Start the Django server

```bash
python manage.py runserver
```

Backend will run at:
 **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

---

#  Frontend Setup (React + Vite)

###  Go to the frontend directory

```bash
cd frontend/prepee-fe
```

###  Install npm dependencies

```bash
npm install
```

###  Start the development server

```bash
npm run dev
```

Frontend will run at:
 **[http://127.0.0.1:5173/](http://127.0.0.1:5173/)** (default Vite port)

---

#  Connecting Frontend & Backend

ignore this for now

Make sure your frontend `.env` contains something like:

```
VITE_API_URL=http://127.0.0.1:8000/api
```

Then in React:

```js
fetch(`${import.meta.env.VITE_API_URL}/endpoint/`)
```

---

#  Running Both Together

Open two terminals:

### Terminal 1 — Django backend

```
cd backend/prepee-be
python manage.py runserver
```

### Terminal 2 — React frontend

```
cd frontend/prepee-fe
npm run dev
```

---

#  Building for Production

### Frontend (React)

```bash
cd frontend/prepee-fe
npm run build
```

### Backend (Django)

Collect static files:

```bash
python manage.py collectstatic
```

---

#  Contributing

1. Fork the repo
2. Create a new branch
3. Commit your changes
4. Push and open a PR

---

#  License

This project is licensed under the MIT License.

---

