# **Prepee – Quiz App**

A full-stack competitive quiz application built using:

* **React + Vite** (Frontend)
* **Django + Django REST Framework** (Backend)
* **Redis** (Caching, matchmaking queue, and real-time operations)

This document explains how to set up and run the full system.

---

# **Getting Started**

## **Requirements**

Make sure you have these installed:

* **Node.js** (>= 18)
* **npm**
* **Python** (>= 3.10)
* **pip**
* **virtualenv** (optional)
* **Git**
* **Redis** (running locally or on Docker)

---

# **Project Structure**

```
.
├── frontend/
│   └── prepee-fe/      # Vite + React frontend
└── backend/
    ├── venv/           # Python virtual environment (ignored in Git)
    └── prepee-be/      # Django backend project
```

---

# **Backend Setup (Django + Redis)**

### 1️⃣ Navigate to the backend folder

```bash
cd backend
```

### 2️⃣ Create a virtual environment (if not created)

```bash
python -m venv venv
```

### 3️⃣ Activate the virtual environment

#### Windows:

```bash
venv\Scripts\activate
```

#### macOS / Linux:

```bash
source venv/bin/activate
```

### 4️⃣ Install backend dependencies

```bash
pip install -r prepee-be/requirements.txt
```

### 5️⃣ Start Redis

If installed locally:

```bash
redis-server
```

Or using Docker:

```bash
docker run -p 6379:6379 redis
```

### 6️⃣ Apply migrations

```bash
cd prepee-be
python manage.py migrate
```

### 7️⃣ Start the Django server

```bash
python manage.py runserver
```

Backend runs at:
👉 **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

---

# **Running the Matchmaker Job**

Your app includes a matchmaking background job that MUST run separately.

Open a new terminal, activate the virtualenv, then run:

```bash
python manage.py run_matchmaker
```

This process continuously:

* Reads players waiting in the queue (stored in Redis)
* Matches them based on ELO
* Creates a Match object
* Triggers automatic quiz generation

⚠️ **Keep this terminal running during development.**

---

# **Frontend Setup (React + Vite)**

### 1️⃣ Go to the frontend directory

```bash
cd frontend/prepee-fe
```

### 2️⃣ Install npm dependencies

```bash
npm install
```

### 3️⃣ Start the development server

```bash
npm run dev
```

Frontend runs at:
👉 **[http://127.0.0.1:5173/](http://127.0.0.1:5173/)**

---

# **Connecting Frontend & Backend**

Create a `.env` file inside `frontend/prepee-fe`:

```
VITE_API_URL=http://127.0.0.1:8000/api
```

Example usage in React:

```js
fetch(`${import.meta.env.VITE_API_URL}/endpoint/`);
```

---

# **Running All Services Together**

Open **three terminals**:

### **Terminal 1 — Redis**

```
redis-server
```

### **Terminal 2 — Django Backend**

```
cd backend/prepee-be
python manage.py runserver
```

### **Terminal 3 — Matchmaker Job**

```
python manage.py run_matchmaker
```

### **Terminal 4 — Frontend**

```
cd frontend/prepee-fe
npm run dev
```

---

# **Building for Production**

### **Frontend**

```bash
cd frontend/prepee-fe
npm run build
```

### **Backend**

Collect static files:

```bash
python manage.py collectstatic
```

Make sure Redis is running in production too.

---

# **Contributing**

1. Fork the repository
2. Create a new branch
3. Commit your changes
4. Push and open a pull request

---

# **License**

Licensed under the MIT License.

---
