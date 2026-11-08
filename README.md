# Institutional KPI Monitoring System

An enterprise-grade full-stack web application designed for the **ICFAI Foundation for Higher Education (IFHE)** to systematically monitor, analyze, and manage institutional Key Performance Indicators (KPIs). The system empowers administrators and academic leaders to track student academic outcomes, faculty strength, departmental composition, laboratory utilization, and student academic feedback across academic years and semesters.

---

## Table of Contents

- [Project Title and Overview](#institutional-kpi-monitoring-system)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Project Architecture](#project-architecture)
- [Project Folder Structure](#project-folder-structure)
- [Installation and Setup](#installation-and-setup)
- [Environment Variables](#environment-variables)
- [Database Configuration](#database-configuration)
- [Usage Instructions](#usage-instructions)
- [Team and Project Information](#team-and-project-information)
- [Future Enhancements](#future-enhancements)

---

## Key Features

### 1. Student Management & Data Upload
- **Assessment Marks Upload**: Upload semester-wise student examination and continuous assessment marks via Excel spreadsheets (`.xlsx`).
- **Comprehensive Assessment Tracking**: Processes component marks including **Test 1**, **Lab-1**, **Test 2**, **Lab-2**, and **Comprehensive Examination (Compre)**.
- **Robust Excel Validation & Normalization**:
  - Automatically treats empty or blank assessment marks cells as `0` instead of rejecting the entire upload.
  - Fully supports decimal/fractional marks (e.g., 63.2, 46.75, 57.25) across database storage and API schemas without rounding errors.
  - Multi-sheet workbook preview modal allowing administrators to inspect detected records and validation status before committing to the database.
- **Student Attendance Upload**: Upload and track subject-wise and section-wise student attendance records from Excel spreadsheets.
- **Accurate Unique Student Counts**: Dynamically computes unique enrolled student counts using enrollment numbers (`studentId`), preventing multi-semester record duplication:
  - **All Departments**: 220 unique students
  - **Computer Science & Engineering (CSE)**: 50 unique students
  - **AI & Data Science (AIDS)**: 50 unique students
  - **Bachelor of Computer Applications (BCA)**: 120 unique students

### 2. Faculty Management
- **Centralized Faculty Directory**: Browse faculty profiles, designations, departmental affiliations, academic qualifications, and teaching experience.
- **Departmental Filtering**: Quick filtering between Computer Science & Engineering and AI & Data Science faculties.
- **Institutional Staffing Metrics**: Live synchronization with student-faculty ratio indicators.

### 3. Department Overview
- **Composition Summary**: Displays live enrollment and staffing metrics for each academic department:
  - **Computer Science and Engineering (CSE)**: Student strength, dedicated faculty count, and Head of Department (**Dr. P. Rohini**).
  - **Artificial Intelligence and Data Science (AIDS)**: Student strength, dedicated faculty count, and Head of Department (**Dr. P. Pavan Kumar**).
  - **Bachelor of Computer Applications (BCA)**: Student strength (120) and designated as **Shared Faculty** (supported by inter-departmental faculty).

### 4. Interactive KPI Dashboard
- **Pass Percentage KPI**:
  - Semester-wise and section-wise pass percentage calculations across BCA, CSE, and AIDS.
  - Target vs. achieved pass percentage benchmark tracking with pass/fail candidate distributions.
- **Student Attendance KPI**:
  - Subject-wise and section-wise attendance analytics.
  - Categorization into attendance performance bands:
    - *Excellent* (≥ 85%)
    - *Good* (75% – 84%)
    - *Warning* (65% – 74%)
    - *Critical* (< 65%)
  - Target compliance tracking against the institutional 75% minimum threshold.
- **Student-Faculty Ratio KPI**:
  - Live institutional ratio calculation (e.g., 3.93 : 1) computed dynamically from enrolled students (220) and active faculty members (56).
  - Ratio benchmark evaluation (Good / Optimal) against regulatory standards.
  - Population comparisons and historical trend visualizer across academic sessions.
- **Laboratory Utilization KPI**:
  - Tracks laboratory session scheduling, room capacity, student attendance, and utilization percentages.
  - Identifies under-utilized and heavily utilized laboratory facilities.

### 5. Student Academic Feedback (Google Forms & Sheets Integration)
- **Direct Google Sheets Ingestion**: Seamlessly syncs live student feedback submitted via Google Forms connected to a Google Spreadsheet.
- **Duplicate Prevention**: Computes SHA-256 cryptographic response hashes (`google_sheet_response_hash`) for each row to ensure submissions are only imported once without arbitrary row limits.
- **Feedback Analytics**:
  - Overall Learning Experience ratings (1 to 5 scale) with average score and distribution curves.
  - Ranked improvement areas with vote counts and dynamic percentage bars:
    - *Teaching methods and explanation of concepts*
    - *More practical learning and hands-on activities*
    - *More assignments and practice questions*
    - *More real-world examples and case studies*
    - *More interactive classroom activities*
    - *No improvements needed*
- **Strict Academic Session Isolation**: Multi-dimensional filtering across Academic Year (`2024-2025`, `2025-2026`), Department, and Semester without cross-year data pollution.

---

## Technology Stack

| Layer | Technologies | Description |
|---|---|---|
| **Frontend** | React 19, Vite 7 | Modern Single Page Application (SPA) with fast Hot Module Replacement |
| **Styling & Icons** | Tailwind CSS v4, Lucide React | Utility-first responsive design, modern typography, and clean iconography |
| **Routing** | React Router DOM v7 | Client-side routing with guarded public and protected route wrappers |
| **Backend Framework** | Python 3.10+, FastAPI | High-performance asynchronous REST API framework with automated OpenAPI docs |
| **Web Server** | Uvicorn | Production-ready ASGI server implementation |
| **ORM & Database** | SQLAlchemy 2.0+, Psycopg2 | Database abstraction layer with support for PostgreSQL (Supabase) and SQLite |
| **Data Processing** | Pandas 2.0+, OpenPyXL 3.1+ | High-throughput spreadsheet parsing, data cleansing, and marks normalization |
| **Authentication** | PyJWT, PBKDF2-SHA256 | Secure bearer token JWT authentication with salted password hashing |
| **External Integration** | Google API Client, Google Auth | Service account integration with the Google Sheets API v4 |

---

## Project Architecture

The application follows a decoupled client-server architecture:

```mermaid
flowchart TD
    subgraph Client["Frontend Client (React 19 + Vite + Tailwind CSS)"]
        UI["Administrator Portal UI"]
        AuthGuard["Auth Route Guards (ProtectedRoute)"]
        Pages["Pages (Home, Student Upload, Faculty, Departments, KPI Dashboard)"]
        APIService["API Fetch Service (localStorage JWT Header)"]
        UI --> AuthGuard --> Pages --> APIService
    end

    subgraph Server["Backend Server (FastAPI + Uvicorn)"]
        Router["REST API Endpoints (/api/*)"]
        AuthMiddleware["JWT Bearer Authentication Handler"]
        Services["Business Services (Excel Parser, Normalizer, Ratio Calculator)"]
        GoogleSheets["Google Sheets Integration Service"]
        ORM["SQLAlchemy ORM (Models & Sessions)"]
        
        Router --> AuthMiddleware
        Router --> Services
        Services --> ORM
        GoogleSheets --> ORM
    end

    subgraph DataStore["Data Layer"]
        Postgres[("Supabase PostgreSQL Database")]
        SQLite[("Local SQLite Database (ifhe_kpi.db Fallback)")]
    end

    subgraph External["External Services"]
        GForm["Google Forms (Student Academic Feedback)"]
        GSheet["Google Sheets Responses Spreadsheet"]
        GForm --> GSheet
    end

    APIService -- "HTTPS / JSON (Port 5000)" --> Router
    GSheet -- "Google Sheets API v4" --> GoogleSheets
    ORM --> Postgres
    ORM -. "Fallback" .-> SQLite
```

---

## Project Folder Structure

```text
KPI/
├── client/                              # Frontend React (Vite) Application
│   ├── public/                          # Public static assets
│   ├── src/                             # Source code
│   │   ├── components/                  # Reusable UI Components
│   │   │   ├── AttendanceTable.jsx      # Student attendance record viewer
│   │   │   ├── ComingSoonModal.jsx      # Placeholder modal for upcoming modules
│   │   │   ├── DashboardCard.jsx        # Stat metric display card
│   │   │   ├── Navbar.jsx               # Top navigation header & logout handler
│   │   │   ├── PassPercentageKPI.jsx    # Pass percentage analytics & filters
│   │   │   ├── StudentAttendanceKPI.jsx # Attendance bands & threshold tracker
│   │   │   ├── StudentFeedbackKPI.jsx   # Feedback analytics & Google Sheet sync
│   │   │   └── StudentTable.jsx         # Component marks & subject score viewer
│   │   ├── pages/                       # Application Views
│   │   │   ├── DepartmentOverviewPage.jsx # Department composition & HOD overview
│   │   │   ├── FacultyDataPage.jsx      # Faculty directory & department filter
│   │   │   ├── HomePage.jsx             # Main navigation dashboard
│   │   │   ├── KPIDashboardPage.jsx     # Institutional KPI analytics center
│   │   │   ├── LoginPage.jsx            # Administrator login portal
│   │   │   └── StudentUploadPage.jsx    # Marks & attendance upload interface
│   │   ├── api.js                       # Centralized fetch client & auth token storage
│   │   ├── App.jsx                      # Route configurations & protected routes
│   │   ├── index.css                    # Tailwind CSS v4 styling rules
│   │   └── main.jsx                     # Application bootstrap entry point
│   ├── package.json                     # Frontend dependencies & npm scripts
│   ├── vite.config.js                   # Vite bundler configuration
│   └── .env.example                     # Frontend environment template
├── server/                              # Backend FastAPI Application
│   ├── google_sheets_service.py         # Google Sheets API client & row fetcher
│   ├── database.py                      # SQLAlchemy engine, session maker & migrations
│   ├── models.py                        # SQLAlchemy ORM database models
│   ├── schemas.py                       # Pydantic validation & response schemas
│   ├── services.py                      # Data normalization, calculations & parser
│   ├── main.py                          # FastAPI entry point & API route handlers
│   ├── requirements.txt                 # Backend Python package dependencies
│   ├── test_google_sheets_feedback.py   # Unit tests for feedback integration
│   ├── test_marks_validation.py         # Unit tests for marks upload validation
│   ├── .env.example                     # Backend environment template
│   └── secrets/                         # Google Cloud service credentials (git-ignored)
└── README.md                            # Comprehensive project documentation
```

---

## Installation and Setup

### 1. Prerequisites
- **Python**: Version `3.10` or higher installed
- **Node.js**: Version `18` or higher installed (with `npm`)
- **Git**: Installed for version control

---

### 2. Clone the Repository

```bash
git clone https://github.com/your-repo/KPI.git
cd KPI
```

---

### 3. Backend Setup (FastAPI)

1. Navigate to the backend directory:
   ```bash
   cd server
   ```

2. Create a Python virtual environment:
   - **Windows (PowerShell)**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - **Linux / macOS**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   ```
   *(Update `.env` with your database credentials, JWT secret, and Google Sheets settings as documented below).*

5. Start the backend development server using Uvicorn:
   ```bash
   uvicorn main:app --reload --port 5000
   ```
   - **Backend Base URL**: `http://localhost:5000`
   - **Interactive API Documentation (Swagger UI)**: `http://localhost:5000/docs`
   - **Alternative API Documentation (ReDoc)**: `http://localhost:5000/redoc`

---

### 4. Frontend Setup (React + Vite)

1. Open a new terminal window and navigate to the frontend directory:
   ```bash
   cd client
   ```

2. Install Node dependencies:
   ```bash
   npm install
   ```

3. Configure frontend environment variables:
   ```bash
   cp .env.example .env
   ```
   Ensure `VITE_API_URL` points to your backend instance (default: `http://localhost:5000`).

4. Start the Vite development server:
   ```bash
   npm run dev
   ```
   - **Frontend Application URL**: `http://localhost:5173`

---

## Environment Variables

### Backend Configuration (`server/.env`)

Configure these settings based on `server/.env.example`:

| Variable | Required | Description | Example / Default |
|---|---|---|---|
| `DATABASE_URL` | Optional | Connection URI for the database. When pointing to Supabase PostgreSQL, use the pooled connection string with `sslmode=require`. If omitted, the server defaults to a local SQLite database (`server/ifhe_kpi.db`). | `postgresql://USER:PASSWORD@HOST:5432/DATABASE?sslmode=require` |
| `JWT_SECRET_KEY` | **Required** | Cryptographic secret key used to sign and verify JSON Web Tokens. | A secure random alphanumeric string |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Optional | Duration in minutes before an issued JWT access token expires. | `60` |
| `ADMIN_USERNAME` | **Required** | Initial administrator username automatically provisioned on database startup. | `admin` |
| `ADMIN_PASSWORD` | **Required** | Initial administrator password hashed with PBKDF2-SHA256 upon first run. | A secure administrator password |
| `GOOGLE_SHEETS_SPREADSHEET_ID` | Optional | Google Spreadsheet ID containing submitted student feedback form responses. | Alphanumeric sheet ID from the Google Sheet URL |
| `GOOGLE_SHEETS_CREDENTIALS_FILE` | Optional | Relative path from `server/` to the Google Cloud Service Account JSON credentials file. | `secrets/google-credentials.json` |

> [!CAUTION]
> Never commit active credentials, production passwords, JWT secret keys, or service account JSON files to version control. The `server/secrets/` directory and `.env` files are excluded by `.gitignore`.

### Frontend Configuration (`client/.env`)

| Variable | Required | Description | Default |
|---|---|---|---|
| `VITE_API_URL` | **Required** | Base HTTP URL where the FastAPI backend service is reachable. | `http://localhost:5000` |

---

## Database Configuration

The application uses **SQLAlchemy ORM (v2.0+)** to manage data transactions. It automatically adapts between **PostgreSQL (Supabase)** in multi-user/production environments and a local **SQLite** file for offline development.

### Connection Architecture
- When `DATABASE_URL` is set, `database.py` normalizes legacy `postgres://` prefixes to `postgresql+psycopg2://` and establishes a pooled connection with SSL enabled.
- When `DATABASE_URL` is absent, it creates `server/ifhe_kpi.db` and enforces foreign key constraints via `PRAGMA foreign_keys=ON`.
- Table schemas and database initializations execute automatically on startup via `models.Base.metadata.create_all(bind=engine)`.

### Core Database Models

| Table Name | Model Class | Key Fields & Purpose |
|---|---|---|
| `admin_users` | `AdminUser` | `username`, `password_hash`, `is_active`, `created_at`. Stores administrator credentials with PBKDF2-SHA256 hashing. |
| `departments` | `Department` | `code`, `name`, `head_of_department`, `description`. Department catalog and leadership information. |
| `faculty` | `Faculty` | `faculty_id`, `name`, `department`, `designation`, `qualification`, `experience_years`, `email`. Faculty member profiles and metrics. |
| `student_uploads` | `StudentUpload` | `studentId`, `studentName`, `totalMarks`, `percentage`, `department`, `section`, `semester`, `academic_year`, `subject_marks` (JSON). Summary student records. |
| `student_marks` | `StudentMark` | `enrollment_number`, `student_name`, `test1`, `lab1`, `test2`, `lab2`, `compre`, `total_marks`, `is_pass`, `subject`, `department`, `section`, `semester`, `academic_year`. Detailed assessment component scores. |
| `student_attendance` | `StudentAttendance` | `student_id`, `student_name`, `total_classes`, `attended_classes`, `attendance_percentage`, `status`, `subject`, `department`, `section`, `semester`, `academic_year`. Class attendance records. |
| `student_feedback` | `StudentFeedback` | `academic_year`, `department`, `semester`, `overall_satisfaction` (1–5), `course_difficulty`, `improvement_areas` (JSON array), `suggestions`, `google_sheet_response_hash`. Ingested student feedback. |
| `laboratory_utilization` | `LaboratoryUtilization` | `laboratory_name`, `department`, `capacity`, `attended`, `utilization_percentage`, `academic_year`. Lab utilization metrics. |
| `kpis` | `KPI` | `code`, `name`, `category`, `target_value`, `current_value`, `status`. Benchmark targets and performance status metadata. |

---

## Usage Instructions

### 1. Logging In as an Administrator
1. Open the frontend in a web browser: `http://localhost:5173`.
2. Enter the administrator credentials configured in `server/.env` (`ADMIN_USERNAME` and `ADMIN_PASSWORD`).
3. Upon successful authentication, a JWT access token is stored in the browser's `localStorage` (`ifhe_kpi_token`), and you are redirected to the **Homepage** (`/home`).
4. To sign out, click the **Logout** button in the top navigation bar. The token is cleared immediately, and protected routes are locked.

### 2. Uploading Student Marks & Attendance
1. From the Homepage, click **Open Module** under **Upload Student Data** (`/upload-students`).
2. Select between the **Student Marks** tab or **Attendance Upload** tab.
3. For marks upload:
   - Select the **Academic Year** (e.g., `2024-2025` or `2025-2026`).
   - Select the target **Department** (`Computer Science and Engineering`, `AI & Data Science`, or `BCA`).
   - Specify the **Section** and **Semester**.
   - Choose an Excel spreadsheet (`.xlsx`) containing student marks.
   - Click **Preview File** to review the detected sheets and component marks (Test 1, Lab 1, Test 2, Lab 2, Compre) with zero-fill validation.
   - Click **Confirm & Save to Database** to commit the records.
4. Filter uploaded records dynamically by Semester, Academic Year, Department, and Section. The displayed student counter accurately reflects unique enrolled students.

### 3. Reviewing Faculty Management
1. Click **Open Module** under **Faculty Management** (`/faculty`).
2. Filter faculty by department (e.g., Computer Science & Engineering or AI & Data Science).
3. Review designations, qualifications, teaching experience, and contact details.

### 4. Reviewing Department Overview
1. Click **View Overview** under **Department Overview** (`/departments`).
2. Inspect student strength and faculty staffing for CSE, AIDS, and BCA.
3. Verify Head of Department details (`Dr. P. Rohini` for CSE, `Dr. P. Pavan Kumar` for AIDS) and shared faculty staffing for BCA.

### 5. Analyzing the KPI Dashboard
1. Click **Open Dashboard** under **KPI Dashboard** (`/dashboard`).
2. Select an indicator from the **KPI** dropdown:
   - **Student Attendance**: Examine class attendance percentages across bands and compare with the 75% institutional threshold.
   - **Pass Percentage**: Filter by Year, Department, Semester, and Section to evaluate pass/fail distributions against benchmark targets.
   - **Student-Faculty Ratio**: Review the student-to-faculty population ratio, benchmark status, and historical trends.
   - **Laboratory Utilization**: Analyze room capacity versus attendance to optimize lab scheduling.
   - **Student Academic Feedback**:
     - View satisfaction ratings and percentage rankings for feedback improvement areas.
     - Click **Sync Google Sheets** to pull the latest form responses from the connected Google Sheet.

---

## Team and Project Information

The **Institutional KPI Monitoring System** is an academic project undertaken as part of the academic work at the **ICFAI Foundation for Higher Education (IFHE), Hyderabad**.

The project focuses on developing a centralized web-based application to monitor institutional performance, manage academic data, and analyze Key Performance Indicators (KPIs).

### Project Team

| S. No. | Team Member | Enrolment Number |
|---|---|---|
| 1 | MD Zaheeruddin Mallick | 24STUCHH010034 |
| 2 | Durwasula Aditya Keerthi Vardhan | 24STUCHH010084 |
| 3 | Garela Akshaya | 24STUCHH00651 |
| 4 | V Vivekananda | 24STUCHH010658 |

**Institution:** ICFAI Foundation for Higher Education (IFHE)

**Location:** Hyderabad, Telangana, India

**GitHub Repository:** [Institutional KPI Monitoring System](https://github.com/GarelaAkshaya/KPI)

---

## Future Enhancements

The following enhancements represent potential improvements for future releases:

1. **Automated Scheduled Ingestion**: Implement an automated background cron worker or webhook receiver for Google Sheets synchronization, reducing the need for manual button triggers.
2. **Role-Based Access Control (RBAC)**: Expand user management to support differentiated roles such as Department Heads (read/write departmental data), Faculty Members (view own classes), and Auditors (read-only compliance access).
3. **Accreditation Report Generation**: Add one-click export of KPI benchmark dossiers formatted according to statutory accreditation guidelines (e.g., NAAC SSR or NBA SAR formats) in PDF and Excel.
4. **Early Academic Warning System**: Develop automated predictive flagging for students exhibiting combined risk indicators (e.g., attendance below 75% alongside failing scores in early continuous assessment tests).
