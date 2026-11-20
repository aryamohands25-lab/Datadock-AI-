# 🚀 DataDock AI – Intelligent Data Validation & Analytics Platform

**DataDock AI** is a web-based data management and analytics platform designed to simplify CSV data validation, quality checking, comparison, and analysis through an intuitive interface.

The platform enables users to upload datasets, validate data against predefined rules, compare CSV files, and manage their dataset history through a centralized application.

## 🌐 Live Demo

**Application:** https://datadock-ai-1.onrender.com

**Backend API:** https://datadock-ai.onrender.com

**API Documentation:** https://datadock-ai.onrender.com/docs

## ✨ Key Features

- **User Authentication:** User registration and login functionality.
- **CSV Upload:** Upload and manage CSV datasets.
- **Data Validation:** Validate uploaded datasets using predefined validation rules.
- **Dataset Comparison:** Compare CSV files and identify differences.
- **Data History:** View and manage previously uploaded datasets.
- **CSV Download:** Download processed datasets.
- **Sample Datasets:** Access sample datasets for testing and exploration.
- **REST API:** Backend functionality exposed through FastAPI endpoints.

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python, FastAPI |
| Relational Database | SQLite |
| Data Analytics | DuckDB |
| API Documentation | Swagger UI (OpenAPI) |
| Deployment | Render |
| Version Control | Git & GitHub |

## 🏗️ System Architecture

```text
              USER
                |
                ▼
       FRONTEND APPLICATION
        HTML / CSS / JavaScript
                |
                ▼
          FASTAPI BACKEND
                |
       ┌────────┼─────────┐
       ▼        ▼         ▼
    SQLite   DuckDB    CSV Storage
       |        |         |
       └────────┼─────────┘
                |
                ▼
       DATA VALIDATION &
          ANALYTICS
```

## 📌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api-status` | Check backend status |
| POST | `/register` | Register a user |
| POST | `/login` | User login |
| POST | `/auth/google` | Google authentication |
| POST | `/upload-csv` | Upload CSV files |
| GET | `/history` | Retrieve dataset history |
| GET | `/download-csv/{file_id}` | Download a dataset |
| DELETE | `/history/{file_id}` | Delete a dataset |
| POST | `/validate-csv` | Validate CSV data |
| POST | `/compare-csv` | Compare CSV files |
| POST | `/compare-csv-ids` | Compare uploaded datasets |
| GET | `/api/rules` | Retrieve validation rules |

Explore all available endpoints through the interactive API documentation:

https://datadock-ai.onrender.com/docs

## ⚙️ Local Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/aryamohands25-lab/Datadock-AI-.git
cd Datadock-AI-
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it:

**Windows:**
```bash
.venv\Scripts\activate
```

**Linux / macOS:**
```bash
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r backend/requirements.txt
```

### 4. Configure Environment Variables

Configure the database and storage paths according to your local environment and backend configuration.

Example:

```env
DATA_DIR=./data
SQLITE_DB_PATH=./data/app.db
DUCKDB_DIR=./data/duckdb
UPLOAD_DIR=./data/uploads
```

### 5. Start the Backend

```bash
cd backend
uvicorn main:app --reload
```

Backend runs at:

http://127.0.0.1:8000

API documentation:

http://127.0.0.1:8000/docs

### 6. Run the Frontend

Open the frontend application using a local development server or configure it through your preferred static file server.

Ensure the frontend API configuration points to:

```javascript
window.DATADOCK_API_URL = "http://127.0.0.1:8000";
```

## ☁️ Deployment

DataDock AI is deployed using **Render**.

- Frontend: Render Static Site
- Backend: Render Web Service
- Backend framework: FastAPI
- API communication: HTTP requests between frontend and backend

The production frontend communicates with the deployed backend through its configured API URL.

## 🎯 Project Objective

The primary objective of DataDock AI is to make dataset management and validation easier, faster, and more accessible by bringing CSV upload, data quality validation, dataset comparison, and history management into one unified platform.

## 🔮 Future Enhancements

- Advanced data profiling and visualization.
- Automated data quality reports.
- Additional validation rules and customizable checks.
- Support for more file formats.
- Enhanced analytics and reporting.
- Improved authentication and access management.

## 👩‍💻 Author

**Arya Mohan G.**

MSc Data Science & Bio-AI

GitHub: https://github.com/aryamohands25-lab

---

⭐ If you find this project useful, consider giving the repository a star!
