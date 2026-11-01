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

### 4. Shared Team Data (Deployment)

The default SQLite database is local to the backend machine. To share data between teammates, deploy one FastAPI backend and connect it to a persistent PostgreSQL database. Set the backend's `DATABASE_URL` environment variable using the format in `server/.env.example`. Do not commit real credentials.

Deploy the frontend and set `VITE_API_URL` to the public URL of that backend (see `client/.env.example`), then rebuild/redeploy the frontend. All screens use this setting. Every teammate must open the same deployed frontend; their changes will then be saved to the shared database and visible to everyone.

For local development, keep `VITE_API_URL=http://localhost:5000` and omit `DATABASE_URL` to use the local SQLite database. Existing records in local SQLite files must be migrated or imported into the shared PostgreSQL database; deploying the app does not merge local files automatically.

---

## Features & API Endpoints

### API Endpoints (`http://localhost:5000`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Health check route returning backend API status string. |
| `GET` | `/api/stats` | Fetches live database counts for Total Students, Total Faculty, Departments, and Active KPIs. |
| `POST` | `/api/upload-students` | Accepts Excel (`.xlsx`) upload, normalizes Student ID, Student Name, Total Marks & Percentage, and saves records into `ifhe_kpi.db`. |
| `GET` | `/api/students` | Retrieves all uploaded student records ordered by latest entry. |
| `POST` | `/api/feedback` | Public single-use-code redemption; saves anonymous ratings/comments without the code or student identifier. |
| `POST` | `/api/feedback/validate-code` | Publicly validates an unused code and returns its faculty/year scope. |
| `GET` | `/api/public/feedback/departments` | Lists department IDs, codes, and names for the public form. |
| `GET` | `/api/public/feedback/faculty/?department_id=<id>` | Lists minimal faculty details for the selected department. |
| `GET` | `/api/public/feedback/academic-year` | Returns the configured active year (`ACTIVE_ACADEMIC_YEAR`, otherwise the newest supported year). |
| `POST` | `/api/public/feedback/validate-token` | Validates a code against its faculty, department, and academic year without returning its hash. |
| `POST` | `/api/public/feedback/submit` | Atomically consumes a scoped code and stores anonymous ratings and comments. |
| `POST` | `/api/feedback/tokens/issue` | Admin-authenticated CSV export of a requested batch of single-use codes for one faculty member and academic year. |
| `POST` | `/api/admin/feedback/tokens` | Admin-authenticated alias for generating a new one-time CSV token export. |
| `GET` | `/api/feedback/faculty` | Admin-authenticated, read-only faculty feedback, rating aggregates, comments, and academic-year/department filters. |
| `GET` | `/api/feedback/summary` | Admin-authenticated aggregate feedback summary used by the Student Feedback Improvement KPI. |
| `GET` | `/api/admin/feedback/faculty` | Admin-authenticated alias for faculty-wise feedback. |
| `GET` | `/api/admin/feedback/summary` | Admin-authenticated alias for the feedback summary. |
| `GET` | `/api/admin/feedback/departments` | Admin-authenticated department-wise average ratings and response counts. |
| `GET` | `/api/admin/feedback/ratings` | Admin-authenticated rating average, valid-rating count, and 0–10 distribution. |

The public student portal is available at `/feedback`; the administrator feedback view is `/feedback/view`. From the Student Feedback Improvement KPI, an administrator selects a faculty member and academic year, specifies a batch size, and downloads a CSV containing unique single-use codes for private distribution. The plaintext codes are generated with a cryptographically secure random generator, returned only in that download, and never stored in the database. Only SHA-256 token hashes are persisted. Do not retain or publicly share the downloaded CSV.

The existing `student_feedback` table is migrated in place to include faculty and department foreign keys, academic year, subject, ratings (0–10), comments, a unique token reference, and submission time. Legacy feedback columns and values are retained for existing KPI compatibility. The `anonymous_feedback_tokens` table stores a unique token hash, faculty/year scope, used state, and timestamps; a unique feedback token reference and transactional one-time redemption prevent a code from submitting multiple responses. Feedback records do not contain student identifiers or plaintext codes. Existing legacy code-issuance hashes are migrated into the token table before the old issuance table is removed. Initialization is repeatable and does not create another database.

All `/api/admin/feedback/*` routes require the existing bearer-token administrator authentication. Public feedback reads are limited to 120 requests per IP per minute, token validation to 10, and submission to 5; these limits are per running API process. The public submission body accepts `feedback_code`, `faculty_id`, `department_id`, `academic_year`, `subject`, the four rating fields, `overall_rating`, and optional `comments`; each rating is validated in the 0–10 range. For example:

```json
{
  "feedback_code": "one-time-code-from-the-private-export",
  "faculty_id": "FACULTY_ID",
  "department_id": 1,
  "academic_year": "2025-2026",
  "subject": "Course name",
  "teaching_quality": 8,
  "subject_knowledge": 9,
  "communication_skills": 8,
  "student_interaction": 9,
  "overall_rating": 9,
  "comments": "Optional anonymous feedback"
}
```

Legacy feedback without an academic year or a valid faculty association is reported separately and excluded from faculty rating calculations. Faculty and department averages use valid 0–10 overall ratings only. The administrator feedback endpoint is read-only and exposes no edit/delete operations.

---

## Database Information

- **Database Engine**: SQLite using SQLAlchemy ORM.
- **Database File**: `server/ifhe_kpi.db`.
- **Tables**:
  - `student_uploads`: Stores `studentId`, `studentName`, `totalMarks`, `percentage`, `createdAt`.
  - `laboratory_utilization`: Stores lab sessions, capacity, attendance, and department statistics.
