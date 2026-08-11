# IFHE KPI - Institutional KPI Monitoring System

An enterprise-grade full-stack web application for monitoring, analyzing, and managing institutional Key Performance Indicators (KPIs) for IFHE. Built with a modern **Python FastAPI** backend powered by **SQLAlchemy ORM** and **SQLite**, paired with a responsive **React (Vite)** + **Tailwind CSS** frontend.

---

## Tech Stack

- **Backend**: Python 3.14+, FastAPI, Uvicorn, SQLAlchemy ORM, SQLite, Pandas, OpenPyXL, Pydantic, Python-Multipart.
- **Frontend**: React 18, Vite, Tailwind CSS v4, Lucide React Icons, React Router DOM v6.
- **Database**: Local SQLite database stored in `server/ifhe_kpi.db`.

---

## Project Structure

```text
IFHE-KPI-FullStack/
├── client/                      # React (Vite) + Tailwind CSS Frontend
│   ├── public/                  # Static assets & public resources
│   ├── src/                     # React application source
│   │   ├── components/          # Reusable UI components (Navbar, DashboardCard, StudentTable, etc.)
│   │   ├── pages/               # Application pages (HomePage, KPIDashboardPage, StudentUploadPage, LoginPage)
│   │   ├── App.jsx              # Main App component & React Router routes
│   │   └── index.css            # Tailwind CSS styling & custom utility definitions
│   ├── package.json             # Frontend dependencies & scripts
│   └── vite.config.js           # Vite server configuration
├── server/                      # Python FastAPI Backend
│   ├── database.py              # SQLAlchemy database engine & SQLite session configuration (ifhe_kpi.db)
│   ├── models.py                # SQLAlchemy ORM models (StudentUpload, LaboratoryUtilization)
│   ├── schemas.py               # Pydantic schemas for data validation and response models
│   ├── services.py              # Excel parser, data normalizer, and CRUD service helpers
│   ├── main.py                  # FastAPI application entry point, CORS middleware, & route handlers
│   ├── requirements.txt         # Python backend dependencies
│   ├── sample-students.xlsx     # Sample Excel sheet for testing student upload
│   └── ifhe_kpi.db              # Local SQLite database file
└── README.md                    # Project documentation
```

---

## Getting Started

### 1. Prerequisites

- **Python**: Version 3.10 or higher installed.
- **Node.js**: Version 18 or higher installed.

---

### 2. Backend Setup (FastAPI + SQLite)

1. Open a terminal and navigate to the `server` directory:
   ```bash
   cd server
   ```

2. Create a Python virtual environment (`venv`):
   - **Windows (PowerShell / CMD)**:
     ```cmd
     python -m venv venv
     ```
   - **Linux / macOS**:
     ```bash
     python3 -m venv venv
     ```

3. Activate the virtual environment:
   - **Windows (PowerShell)**:
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - **Windows (CMD)**:
     ```cmd
     venv\Scripts\activate.bat
     ```
   - **Linux / macOS**:
     ```bash
     source venv/bin/activate
     ```

4. Install the Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Start the FastAPI backend server using Uvicorn:
   ```bash
   uvicorn main:app --reload --port 5000
   ```
   - Server running at: `http://localhost:5000`
   - Interactive API Docs (Swagger UI): `http://localhost:5000/docs`
   - SQLite Database created automatically at `server/ifhe_kpi.db`.

---

### 3. Frontend Setup (React + Vite + Tailwind CSS)

1. Open a new terminal window and navigate to the `client` directory:
   ```bash
   cd client
   ```

2. Install Node dependencies:
   ```bash
   npm install
   ```

3. Start the React development server:
   ```bash
   npm run dev
   ```
   - Frontend running at: `http://localhost:5173`

---

## Features & API Endpoints

### API Endpoints (`http://localhost:5000`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Health check route returning backend API status string. |
| `GET` | `/api/stats` | Fetches live database counts for Total Students, Total Faculty, Departments, and Active KPIs. |
| `POST` | `/api/upload-students` | Accepts Excel (`.xlsx`) upload, normalizes Student ID, Student Name, Total Marks & Percentage, and saves records into `ifhe_kpi.db`. |
| `GET` | `/api/students` | Retrieves all uploaded student records ordered by latest entry. |

---

## Database Information

- **Database Engine**: SQLite using SQLAlchemy ORM.
- **Database File**: `server/ifhe_kpi.db`.
- **Tables**:
  - `student_uploads`: Stores `studentId`, `studentName`, `totalMarks`, `percentage`, `createdAt`.
  - `laboratory_utilization`: Stores lab sessions, capacity, attendance, and department statistics.
