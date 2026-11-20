import bcrypt
import io
import json
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Union

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, text
from sqlalchemy.orm import declarative_base, sessionmaker

from auth import create_access_token
from profiler import compare_csv_files, profile_dataframe, read_dataset
from validation import evaluate_validation_rules
from domains import get_rules_for_domain
from classifier import classify_dataset_regressions
from explainer import generate_audit_explanation
from dataset_generator import (
    generate_bank_transactions_preset,
    generate_loan_portfolio_preset,
    generate_patient_diagnostics_preset,
    generate_clinical_vitals_preset,
    generate_student_academics_preset,
    generate_course_enrollment_preset,
    generate_system_metrics_preset,
    generate_microservices_api_preset
)
from sql_engine import DuckDBQueryEngine, sanitize_table_name, SQLSecurityError, validate_query_safety
from ai_query import generate_sql_query, explain_query_results
from external_discovery import search_external_catalogue, import_external_dataset, EXTERNAL_CATALOGUE


# =========================================================
# APP & DIRECTORIES
# =========================================================

app = FastAPI(title="DataDock AI API (Finance, Healthcare, Academics & IT Software Systems)")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "").strip()

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
SUPPORTED_DATASET_EXTENSIONS = {".csv", ".xlsx"}


def is_supported_dataset(filename: str) -> bool:
    return Path(filename or "").suffix.lower() in SUPPORTED_DATASET_EXTENSIONS


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # For local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# DATABASE
# =========================================================

DATABASE_URL = f"sqlite:///{BASE_DIR / 'datadock.db'}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


# =========================================================
# DATABASE TABLES
# =========================================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)


class CSVFile(Base):
    __tablename__ = "csv_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    user_id = Column(Integer, nullable=False, default=1)
    user_email = Column(String, nullable=False, default="user@example.com")
    upload_date = Column(String, nullable=False)
    row_count = Column(Integer, default=0)
    file_size = Column(String, nullable=False)
    domain = Column(String, default="finance", nullable=True)
    version = Column(Integer, default=1, nullable=True)
    parent_id = Column(Integer, nullable=True)
    source_type = Column(String, default="upload", nullable=True)
    source_url = Column(String, nullable=True)
    license = Column(String, nullable=True)


class SavedQuery(Base):
    __tablename__ = "saved_queries"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, nullable=False, index=True)
    dataset_id = Column(Integer, nullable=True)
    dataset_name = Column(String, nullable=True)
    dataset_version = Column(String, nullable=True)
    query_name = Column(String, nullable=False)
    query_sql = Column(Text, nullable=False)
    query_type = Column(String, default="sql")
    domain = Column(String, default="finance")
    gemini_prompt = Column(Text, nullable=True)
    parameters_json = Column(Text, nullable=True)
    result_summary_json = Column(Text, nullable=True)
    created_at = Column(String, nullable=False)
    last_run_at = Column(String, nullable=True)


class AnalysisLineage(Base):
    __tablename__ = "analysis_lineage"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, nullable=False, index=True)
    saved_query_id = Column(Integer, nullable=True)
    query_name = Column(String, nullable=False)
    query_sql = Column(Text, nullable=False)
    dataset_id = Column(Integer, nullable=False)
    dataset_name = Column(String, nullable=False)
    dataset_version = Column(String, default="1")
    row_count = Column(Integer, default=0)
    column_count = Column(Integer, default=0)
    execution_time_ms = Column(Float, default=0.0)
    result_preview_json = Column(Text, nullable=True)
    quality_score = Column(Float, nullable=True)
    executed_at = Column(String, nullable=False)


# Create database/tables automatically
Base.metadata.create_all(bind=engine)

# Auto-migrate existing sqlite tables if columns were added
def auto_migrate_schema():
    with engine.connect() as conn:
        for col_name, col_type in [
            ("domain", "TEXT DEFAULT 'finance'"),
            ("version", "INTEGER DEFAULT 1"),
            ("parent_id", "INTEGER"),
            ("source_type", "TEXT DEFAULT 'upload'"),
            ("source_url", "TEXT"),
            ("license", "TEXT")
        ]:
            try:
                conn.execute(text(f"ALTER TABLE csv_files ADD COLUMN {col_name} {col_type}"))
                conn.commit()
            except Exception:
                pass

auto_migrate_schema()

# Initialize analytical SQL execution engine
sql_engine = DuckDBQueryEngine(upload_dir=UPLOAD_DIR)


# =========================================================
# PASSWORD HASHING
# =========================================================

def hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


# =========================================================
# REQUEST MODELS
# =========================================================

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class GoogleAuthRequest(BaseModel):
    credential: str


class ExecuteQueryRequest(BaseModel):
    query: str
    dataset_id: Optional[int] = None
    additional_dataset_ids: Optional[List[int]] = None
    page: int = 1
    page_size: int = 50


class GenerateQueryRequest(BaseModel):
    prompt: str
    dataset_id: int
    domain: str = "finance"


class ExplainQueryRequest(BaseModel):
    query: str
    columns: List[str]
    rows: List[list]
    total_rows: int
    execution_time_ms: float
    domain: str = "finance"


class SaveQueryRequest(BaseModel):
    user_email: str
    query_name: str
    query_sql: str
    dataset_id: Optional[int] = None
    dataset_name: Optional[str] = None
    dataset_version: Optional[str] = "1"
    query_type: Optional[str] = "sql"
    domain: Optional[str] = "finance"
    gemini_prompt: Optional[str] = None


class RerunQueryRequest(BaseModel):
    user_email: str
    target_dataset_id: Optional[int] = None


class ImportExternalRequest(BaseModel):
    dataset_id: str
    user_email: Optional[str] = "user@example.com"


# =========================================================
# ROOT & STATUS
# =========================================================

@app.get("/api-status")
def api_status():
    return {
        "message": "DataDock AI backend is running"
    }


# =========================================================
# REGISTER & LOGIN
# =========================================================

@app.post("/register")
def register(request: RegisterRequest):
    db = SessionLocal()
    try:
        existing_user = db.query(User).filter(User.email == request.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed_pwd = hash_password(request.password)
        new_user = User(
            name=request.name,
            email=request.email,
            password_hash=hashed_pwd
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        token = create_access_token(new_user.id)
        return {
            "success": True,
            "message": "Registration successful",
            "access_token": token,
            "user": {
                "id": new_user.id,
                "name": new_user.name,
                "email": new_user.email
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print("REGISTER ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Registration failed")
    finally:
        db.close()


@app.post("/login")
def login(request: LoginRequest):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if not verify_password(request.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        token = create_access_token(user.id)
        return {
            "success": True,
            "message": "Login successful",
            "access_token": token,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print("LOGIN ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Login failed")
    finally:
        db.close()


@app.post("/auth/google")
def google_auth(request: GoogleAuthRequest):
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=503, detail="Google sign-in is not configured on the server")

    try:
        google_user = google_id_token.verify_oauth2_token(
            request.credential,
            google_requests.Request(),
            GOOGLE_CLIENT_ID
        )
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google credential")
    except Exception as e:
        print("GOOGLE TOKEN VERIFICATION ERROR:", repr(e))
        raise HTTPException(status_code=503, detail="Could not verify Google credential")

    email = google_user.get("email")
    if not email or google_user.get("email_verified") is not True:
        raise HTTPException(status_code=401, detail="Google account email is not verified")

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            random_pass = hash_password(str(uuid.uuid4()))
            user = User(
                name=google_user.get("name") or email.split("@", 1)[0],
                email=email,
                password_hash=random_pass
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        token = create_access_token(user.id)
        return {
            "success": True,
            "message": "Google authentication successful",
            "access_token": token,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email
            }
        }
    except Exception as e:
        db.rollback()
        print("GOOGLE AUTH ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Google authentication failed")
    finally:
        db.close()


# =========================================================
# DATASET UPLOAD & HISTORY
# =========================================================

def format_file_size(size_in_bytes: int) -> str:
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    elif size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes / 1024:.1f} KB"
    else:
        return f"{size_in_bytes / (1024 * 1024):.1f} MB"


@app.post("/upload-csv")
async def upload_csv(
    file: UploadFile = File(...),
    user_email: str = Form("user@example.com"),
    domain: str = Form("finance"),
    version: int = Form(1)
):
    if not is_supported_dataset(file.filename):
        raise HTTPException(status_code=400, detail="Only .csv and .xlsx files are supported.")

    db = SessionLocal()
    try:
        # Find user ID if exists
        user = db.query(User).filter(User.email == user_email).first()
        user_id = user.id if user else 1

        content = await file.read()
        file_size_bytes = len(content)

        try:
            row_count = len(read_dataset(io.BytesIO(content), file.filename))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Could not read dataset: {str(e)}")

        # Unique filename
        unique_name = f"{uuid.uuid4().hex}_{file.filename}"
        target_path = UPLOAD_DIR / unique_name

        with open(target_path, "wb") as f:
            f.write(content)

        upload_record = CSVFile(
            filename=unique_name,
            original_filename=file.filename,
            user_id=user_id,
            user_email=user_email,
            upload_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            row_count=row_count,
            file_size=format_file_size(file_size_bytes),
            domain=domain,
            version=version,
            source_type="upload"
        )

        db.add(upload_record)
        db.commit()
        db.refresh(upload_record)

        return {
            "success": True,
            "message": "Dataset uploaded successfully",
            "file": {
                "id": upload_record.id,
                "filename": upload_record.original_filename,
                "table_name": sanitize_table_name(upload_record.original_filename),
                "row_count": upload_record.row_count,
                "file_size": upload_record.file_size,
                "domain": upload_record.domain,
                "version": upload_record.version,
                "upload_date": upload_record.upload_date
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print("UPLOAD ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Failed to upload dataset.")
    finally:
        db.close()


@app.get("/history")
def get_history(user_email: str = Query(None), domain: str = Query(None)):
    db = SessionLocal()
    try:
        query = db.query(CSVFile)
        if user_email:
            query = query.filter(CSVFile.user_email == user_email)
        if domain and domain not in ("all", "*"):
            query = query.filter(CSVFile.domain == domain)

        files = query.order_by(CSVFile.id.desc()).all()

        results = [
            {
                "id": f.id,
                "filename": f.original_filename,
                "table_name": sanitize_table_name(f.original_filename),
                "upload_date": f.upload_date,
                "file_size": f.file_size,
                "row_count": f.row_count,
                "domain": f.domain or "finance",
                "version": f.version or 1,
                "source_type": f.source_type or "upload",
                "status": "Processed"
            }
            for f in files
        ]

        return {
            "success": True,
            "count": len(results),
            "history": results
        }
    except Exception as e:
        print("HISTORY ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Failed to fetch upload history.")
    finally:
        db.close()


@app.get("/download-csv/{file_id}")
def download_csv(file_id: int):
    db = SessionLocal()
    try:
        record = db.query(CSVFile).filter(CSVFile.id == file_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="File not found")

        file_path = UPLOAD_DIR / record.filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File on disk not found")

        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if file_path.suffix.lower() == ".xlsx" else "text/csv"
        return FileResponse(
            path=file_path,
            filename=record.original_filename,
            media_type=media_type
        )
    finally:
        db.close()


@app.delete("/history/{file_id}")
def delete_dataset(file_id: int):
    db = SessionLocal()
    try:
        record = db.query(CSVFile).filter(CSVFile.id == file_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="Dataset not found")

        file_path = UPLOAD_DIR / record.filename
        if file_path.exists():
            file_path.unlink()

        db.delete(record)
        db.commit()

        return {
            "success": True,
            "message": "Dataset deleted successfully",
            "file_id": file_id
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print("DELETE DATASET ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Failed to delete dataset.")
    finally:
        db.close()


# =========================================================
# DATASET COMPARISON, VALIDATION & REGRESSION ENDPOINTS
# =========================================================

class CompareIDsRequest(BaseModel):
    file_id_a: int
    file_id_b: int
    key_column: str = None
    domain: str = "finance"


@app.post("/validate-csv")
async def validate_csv_endpoint(file: UploadFile = File(...), domain: str = Form("finance")):
    """Evaluate domain validation rules for a CSV or XLSX file."""
    if not is_supported_dataset(file.filename):
        raise HTTPException(status_code=400, detail="Only .csv and .xlsx files are supported.")
    try:
        content = await file.read()
        df = read_dataset(io.BytesIO(content), file.filename)
        val_result = evaluate_validation_rules(df, domain=domain)
        return {
            "success": True,
            "filename": file.filename,
            "domain": domain,
            "row_count": len(df),
            "validation": val_result
        }
    except Exception as e:
        print("VALIDATE DATASET ERROR:", repr(e))
        raise HTTPException(status_code=400, detail=f"Validation failed: {str(e)}")


def process_full_comparison(path_a: str, path_b: str, name_a: str, name_b: str, key_column: str = None, domain: str = "finance") -> dict:
    """Helper to run comparison, validation, regression classification, and AI explainer."""
    # Base profiling comparison
    result = compare_csv_files(
        file_a_path=path_a,
        file_b_path=path_b,
        name_a=name_a,
        name_b=name_b,
        key_column=key_column
    )

    # Load DataFrames for validation rules
    df_a = read_dataset(path_a, name_a)
    df_b = read_dataset(path_b, name_b)

    val_a = evaluate_validation_rules(df_a, domain=domain)
    val_b = evaluate_validation_rules(df_b, domain=domain)

    # Classify regressions (Improvement, Regression, Neutral, Human Review)
    classification = classify_dataset_regressions(result, val_a, val_b)

    # Grounded AI audit explanation
    explanation = generate_audit_explanation(result, classification, val_a, val_b, domain=domain)

    result["domain"] = domain
    result["validation_a"] = val_a
    result["validation_b"] = val_b
    result["classification"] = classification
    result["explanation"] = explanation

    return result


@app.post("/compare-csv")
async def compare_csv_files_endpoint(
    file_a: UploadFile = File(...),
    file_b: UploadFile = File(...),
    key_column: str = Form(None),
    domain: str = Form("finance")
):
    """Compare two directly uploaded CSV or XLSX files."""
    if not is_supported_dataset(file_a.filename) or not is_supported_dataset(file_b.filename):
        raise HTTPException(status_code=400, detail="Both files must be .csv or .xlsx format.")

    try:
        temp_a = UPLOAD_DIR / f"temp_{uuid.uuid4().hex}_{file_a.filename}"
        temp_b = UPLOAD_DIR / f"temp_{uuid.uuid4().hex}_{file_b.filename}"

        content_a = await file_a.read()
        content_b = await file_b.read()

        with open(temp_a, "wb") as f:
            f.write(content_a)
        with open(temp_b, "wb") as f:
            f.write(content_b)

        result = process_full_comparison(
            path_a=str(temp_a),
            path_b=str(temp_b),
            name_a=file_a.filename,
            name_b=file_b.filename,
            key_column=key_column,
            domain=domain
        )

        # Cleanup temp files
        if temp_a.exists():
            temp_a.unlink()
        if temp_b.exists():
            temp_b.unlink()

        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        print("COMPARE DATASET ERROR:", repr(e))
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")


@app.post("/compare-csv-ids")
def compare_csv_ids_endpoint(request: CompareIDsRequest):
    """Compare two stored dataset files from history database."""
    db = SessionLocal()
    try:
        rec_a = db.query(CSVFile).filter(CSVFile.id == request.file_id_a).first()
        rec_b = db.query(CSVFile).filter(CSVFile.id == request.file_id_b).first()

        if not rec_a or not rec_b:
            raise HTTPException(status_code=404, detail="One or both selected dataset files not found.")

        path_a = UPLOAD_DIR / rec_a.filename
        path_b = UPLOAD_DIR / rec_b.filename

        if not path_a.exists() or not path_b.exists():
            raise HTTPException(status_code=404, detail="One or both dataset files are missing on disk.")

        result = process_full_comparison(
            path_a=str(path_a),
            path_b=str(path_b),
            name_a=rec_a.original_filename,
            name_b=rec_b.original_filename,
            key_column=request.key_column,
            domain=request.domain
        )

        return {
            "success": True,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        print("COMPARE IDS ERROR:", repr(e))
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")
    finally:
        db.close()


@app.get("/api/rules")
def get_validation_rules(domain: str = Query("finance")):
    """Retrieve active domain validation rules (finance or healthcare)."""
    rules = get_rules_for_domain(domain)
    return {
        "success": True,
        "domain": domain,
        "count": len(rules),
        "rules": rules
    }


@app.post("/api/sample-datasets/{preset_key}")
def run_sample_preset_endpoint(preset_key: str):
    """
    Generate and analyze preset V1 vs V2 dataset pairs across Finance, Healthcare, Academics & IT Systems:
    - 'bank-transactions': Bank Transactions V1 (10,000) vs V2 (12,000) [Finance]
    - 'loan-portfolio': Loan Portfolio V1 (5,000) vs V2 (5,500) [Finance]
    - 'patient-diagnostics': Patient Diagnostics V1 (5,000) vs V2 (6,000) [Healthcare]
    - 'student-academics': Student Academic Records V1 (5,000) vs V2 (6,000) [Academics & Education]
    - 'software-systems': IT & Software Telemetry V1 (5,000) vs V2 (6,200) [IT & Software Systems]
    """
    try:
        if preset_key == "bank-transactions":
            path_a, path_b = generate_bank_transactions_preset()
            name_a = "Bank_Transactions_v1.csv"
            name_b = "Bank_Transactions_v2.csv"
            key_col = "Transaction_ID"
            preset_domain = "finance"
        elif preset_key == "loan-portfolio":
            path_a, path_b = generate_loan_portfolio_preset()
            name_a = "Loan_Portfolio_v1.csv"
            name_b = "Loan_Portfolio_v2.csv"
            key_col = "Loan_ID"
            preset_domain = "finance"
        elif preset_key in ("patient-diagnostics", "patient"):
            path_a, path_b = generate_patient_diagnostics_preset()
            name_a = "Patient_Diagnostics_v1.csv"
            name_b = "Patient_Diagnostics_v2.csv"
            key_col = "Patient_ID"
            preset_domain = "healthcare"
        elif preset_key in ("clinical-vitals", "hospital-vitals", "ehr-vitals"):
            path_a, path_b = generate_clinical_vitals_preset()
            name_a = "Clinical_Vitals_v1.csv"
            name_b = "Clinical_Vitals_v2.csv"
            key_col = "Record_ID"
            preset_domain = "healthcare"
        elif preset_key in ("student-academics", "academic-records", "academics", "education"):
            path_a, path_b = generate_student_academics_preset()
            name_a = "Student_Academics_v1.csv"
            name_b = "Student_Academics_v2.csv"
            key_col = "Student_ID"
            preset_domain = "academics"
        elif preset_key in ("course-enrollment", "course-grades", "enrollment"):
            path_a, path_b = generate_course_enrollment_preset()
            name_a = "Course_Enrollment_v1.csv"
            name_b = "Course_Enrollment_v2.csv"
            key_col = "Enrollment_ID"
            preset_domain = "academics"
        elif preset_key in ("software-systems", "system-metrics", "it-telemetry", "it-systems", "software"):
            path_a, path_b = generate_system_metrics_preset()
            name_a = "System_Metrics_v1.csv"
            name_b = "System_Metrics_v2.csv"
            key_col = "Incident_ID"
            preset_domain = "software_systems"
        elif preset_key in ("microservices-api", "cloud-api", "service-sla"):
            path_a, path_b = generate_microservices_api_preset()
            name_a = "Microservices_API_v1.csv"
            name_b = "Microservices_API_v2.csv"
            key_col = "Request_ID"
            preset_domain = "software_systems"
        else:
            raise HTTPException(status_code=400, detail=f"Unknown sample preset key '{preset_key}'.")

        result = process_full_comparison(
            path_a=path_a,
            path_b=path_b,
            name_a=name_a,
            name_b=name_b,
            key_column=key_col,
            domain=preset_domain
        )

        return {
            "success": True,
            "preset": preset_key,
            "domain": preset_domain,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        print("PRESET RUN ERROR:", repr(e))
        raise HTTPException(status_code=500, detail=f"Preset execution failed: {str(e)}")



# =========================================================
# SQL WORKBENCH, VISUAL EXPLORER & ENGINE ENDPOINTS
# =========================================================

def resolve_dataset_path(dataset_id: Any, db) -> tuple:
    """Helper to resolve a dataset ID or preset name to (table_name, Path)."""
    dataset_str = str(dataset_id).strip()
    if dataset_str.startswith("preset:"):
        preset_key = dataset_str.split(":", 1)[1]
        if preset_key == "bank-transactions":
            p_a, _ = generate_bank_transactions_preset()
            return "bank_transactions", Path(p_a)
        elif preset_key == "loan-portfolio":
            p_a, _ = generate_loan_portfolio_preset()
            return "loan_portfolio", Path(p_a)
        elif preset_key in ("patient-diagnostics", "patient"):
            p_a, _ = generate_patient_diagnostics_preset()
            return "patient_diagnostics", Path(p_a)
        elif preset_key in ("clinical-vitals", "hospital-vitals"):
            p_a, _ = generate_clinical_vitals_preset()
            return "clinical_vitals", Path(p_a)
        elif preset_key in ("student-academics", "academics"):
            p_a, _ = generate_student_academics_preset()
            return "student_academics", Path(p_a)
        elif preset_key in ("course-enrollment", "enrollment"):
            p_a, _ = generate_course_enrollment_preset()
            return "course_enrollment", Path(p_a)
        elif preset_key in ("software-systems", "system-metrics"):
            p_a, _ = generate_system_metrics_preset()
            return "system_metrics", Path(p_a)
        elif preset_key in ("microservices-api", "service-sla"):
            p_a, _ = generate_microservices_api_preset()
            return "microservices_api", Path(p_a)
        else:
            p_a, _ = generate_bank_transactions_preset()
            return "bank_transactions", Path(p_a)

    try:
        rec_id = int(dataset_str)
        rec = db.query(CSVFile).filter(CSVFile.id == rec_id).first()
        if not rec:
            raise HTTPException(status_code=404, detail=f"Dataset with ID {rec_id} not found.")
        file_path = UPLOAD_DIR / rec.filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Dataset file missing on disk: {rec.filename}")
        return sanitize_table_name(rec.original_filename), file_path
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid dataset reference: {dataset_id}")


@app.get("/api/datasets")
def list_workspace_datasets(user_email: str = Query(None), domain: str = Query(None)):
    """List all workspace datasets, including uploaded, imported, and preset datasets."""
    db = SessionLocal()
    try:
        query = db.query(CSVFile)
        if user_email:
            query = query.filter(CSVFile.user_email == user_email)
        if domain and domain not in ("all", "*"):
            query = query.filter(CSVFile.domain == domain)

        records = query.order_by(CSVFile.id.desc()).all()
        datasets = [
            {
                "id": str(r.id),
                "is_preset": False,
                "name": r.original_filename,
                "table_name": sanitize_table_name(r.original_filename),
                "domain": r.domain or "finance",
                "version": r.version or 1,
                "row_count": r.row_count,
                "file_size": r.file_size,
                "upload_date": r.upload_date,
                "source_type": r.source_type or "upload"
            }
            for r in records
        ]

        # Add domain benchmark presets for instant SQL exploration
        presets = [
            {"id": "preset:bank-transactions", "name": "Bank Transactions V1 (Preset)", "table_name": "bank_transactions", "domain": "finance", "version": 1, "row_count": 10000, "file_size": "1.2 MB", "source_type": "preset"},
            {"id": "preset:loan-portfolio", "name": "Loan Portfolio V1 (Preset)", "table_name": "loan_portfolio", "domain": "finance", "version": 1, "row_count": 5000, "file_size": "650 KB", "source_type": "preset"},
            {"id": "preset:patient-diagnostics", "name": "Patient Diagnostics V1 (Preset)", "table_name": "patient_diagnostics", "domain": "healthcare", "version": 1, "row_count": 5000, "file_size": "580 KB", "source_type": "preset"},
            {"id": "preset:clinical-vitals", "name": "Clinical Vitals V1 (Preset)", "table_name": "clinical_vitals", "domain": "healthcare", "version": 1, "row_count": 4500, "file_size": "520 KB", "source_type": "preset"},
            {"id": "preset:student-academics", "name": "Student Academics V1 (Preset)", "table_name": "student_academics", "domain": "academics", "version": 1, "row_count": 5000, "file_size": "540 KB", "source_type": "preset"},
            {"id": "preset:course-enrollment", "name": "Course Enrollment V1 (Preset)", "table_name": "course_enrollment", "domain": "academics", "version": 1, "row_count": 4000, "file_size": "480 KB", "source_type": "preset"},
            {"id": "preset:software-systems", "name": "System Metrics Telemetry V1 (Preset)", "table_name": "system_metrics", "domain": "software_systems", "version": 1, "row_count": 5000, "file_size": "610 KB", "source_type": "preset"},
            {"id": "preset:microservices-api", "name": "Microservices API SLA V1 (Preset)", "table_name": "microservices_api", "domain": "software_systems", "version": 1, "row_count": 4200, "file_size": "530 KB", "source_type": "preset"},
        ]

        if domain and domain not in ("all", "*"):
            presets = [p for p in presets if p["domain"] == domain]

        return {
            "success": True,
            "count": len(datasets) + len(presets),
            "datasets": datasets + presets
        }
    finally:
        db.close()


@app.get("/api/datasets/{dataset_id}/schema")
def get_dataset_schema_endpoint(dataset_id: str):
    """Inspect schema, column types, and sample preview rows via DuckDB."""
    db = SessionLocal()
    try:
        table_name, file_path = resolve_dataset_path(dataset_id, db)
        schema_info = sql_engine.get_dataset_schema(file_path, table_name)
        return {
            "success": True,
            "dataset_id": dataset_id,
            "schema": schema_info
        }
    except HTTPException:
        raise
    except Exception as e:
        print("SCHEMA EXTRACT ERROR:", repr(e))
        raise HTTPException(status_code=500, detail=f"Failed to inspect schema: {str(e)}")
    finally:
        db.close()


@app.get("/api/datasets/{dataset_id}/profile")
def get_dataset_profile_endpoint(dataset_id: str):
    """Run full statistical profiler on a single dataset."""
    db = SessionLocal()
    try:
        table_name, file_path = resolve_dataset_path(dataset_id, db)
        df = read_dataset(file_path, file_path.name)
        profile = profile_dataframe(df)
        return {
            "success": True,
            "dataset_id": dataset_id,
            "table_name": table_name,
            "profile": profile
        }
    except HTTPException:
        raise
    except Exception as e:
        print("PROFILE SINGLE ERROR:", repr(e))
        raise HTTPException(status_code=500, detail=f"Failed to profile dataset: {str(e)}")
    finally:
        db.close()


@app.post("/api/query/execute")
def execute_sql_query_endpoint(request: ExecuteQueryRequest):
    """
    Execute a safe analytical SQL query using DuckDB.
    Supports SELECT, GROUP BY, aggregations, JOINs, CTEs, filters.
    """
    db = SessionLocal()
    try:
        mappings = {}

        # Register primary dataset
        if request.dataset_id is not None:
            tbl_name, p = resolve_dataset_path(request.dataset_id, db)
            mappings[tbl_name] = p
            mappings["dataset"] = p
            mappings["t1"] = p

        # Register any additional datasets for JOINs
        if request.additional_dataset_ids:
            for idx, add_id in enumerate(request.additional_dataset_ids, start=2):
                tbl_name, p = resolve_dataset_path(add_id, db)
                mappings[tbl_name] = p
                mappings[f"t{idx}"] = p

        # If no explicit dataset provided, register all recent uploaded CSV files
        if not mappings:
            recent_files = db.query(CSVFile).order_by(CSVFile.id.desc()).limit(15).all()
            for r in recent_files:
                p = UPLOAD_DIR / r.filename
                if p.exists():
                    tbl = sanitize_table_name(r.original_filename)
                    mappings[tbl] = p

        if not mappings:
            # Fallback to bank transactions preset
            p_a, _ = generate_bank_transactions_preset()
            mappings["transactions"] = Path(p_a)
            mappings["bank_transactions"] = Path(p_a)
            mappings["dataset"] = Path(p_a)

        result = sql_engine.execute_query(
            query=request.query,
            dataset_mappings=mappings,
            page=request.page,
            page_size=request.page_size
        )

        return result

    except SQLSecurityError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        print("QUERY EXEC ERROR:", repr(e))
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")
    finally:
        db.close()


@app.post("/api/query/generate")
def generate_sql_nl_endpoint(request: GenerateQueryRequest):
    """
    Convert a natural language instruction into safe DuckDB SQL via Gemini
    (or offline heuristic fallback).
    """
    db = SessionLocal()
    try:
        tbl_name, p = resolve_dataset_path(request.dataset_id, db)
        schema_info = sql_engine.get_dataset_schema(p, tbl_name)
        result = generate_sql_query(
            prompt=request.prompt,
            schema=schema_info,
            domain=request.domain
        )
        return {
            "success": True,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        print("GENERATE SQL ERROR:", repr(e))
        raise HTTPException(status_code=500, detail=f"Natural language translation failed: {str(e)}")
    finally:
        db.close()


@app.post("/api/query/explain")
def explain_sql_results_endpoint(request: ExplainQueryRequest):
    """
    Produce a plain-language explanation of verified query results.
    """
    try:
        explanation = explain_query_results(
            query=request.query,
            columns=request.columns,
            rows=request.rows,
            total_rows=request.total_rows,
            execution_time_ms=request.execution_time_ms,
            domain=request.domain
        )
        return {
            "success": True,
            "explanation": explanation
        }
    except Exception as e:
        print("EXPLAIN SQL ERROR:", repr(e))
        raise HTTPException(status_code=500, detail=f"Explanation generation failed: {str(e)}")


# =========================================================
# SAVED QUERIES & ANALYSIS LINEAGE ENDPOINTS
# =========================================================

@app.post("/api/queries/save")
def save_query_endpoint(request: SaveQueryRequest):
    """Save an analytical query for future runs and reproducible tracking."""
    db = SessionLocal()
    try:
        validate_query_safety(request.query_sql)
        saved = SavedQuery(
            user_email=request.user_email,
            dataset_id=request.dataset_id,
            dataset_name=request.dataset_name,
            dataset_version=request.dataset_version or "1",
            query_name=request.query_name,
            query_sql=request.query_sql,
            query_type=request.query_type or "sql",
            domain=request.domain or "finance",
            gemini_prompt=request.gemini_prompt,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        db.add(saved)
        db.commit()
        db.refresh(saved)

        return {
            "success": True,
            "message": "Query saved successfully",
            "query": {
                "id": saved.id,
                "name": saved.query_name,
                "sql": saved.query_sql,
                "domain": saved.domain,
                "created_at": saved.created_at
            }
        }
    except SQLSecurityError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        print("SAVE QUERY ERROR:", repr(e))
        raise HTTPException(status_code=500, detail="Failed to save query.")
    finally:
        db.close()


@app.get("/api/queries")
def list_saved_queries(user_email: str = Query(None), domain: str = Query(None)):
    """List saved queries for a user and domain."""
    db = SessionLocal()
    try:
        query = db.query(SavedQuery)
        if user_email:
            query = query.filter(SavedQuery.user_email == user_email)
        if domain and domain not in ("all", "*"):
            query = query.filter(SavedQuery.domain == domain)

        queries = query.order_by(SavedQuery.id.desc()).all()
        return {
            "success": True,
            "count": len(queries),
            "queries": [
                {
                    "id": q.id,
                    "query_name": q.query_name,
                    "query_sql": q.query_sql,
                    "dataset_id": q.dataset_id,
                    "dataset_name": q.dataset_name,
                    "dataset_version": q.dataset_version,
                    "query_type": q.query_type,
                    "domain": q.domain,
                    "gemini_prompt": q.gemini_prompt,
                    "created_at": q.created_at,
                    "last_run_at": q.last_run_at
                }
                for q in queries
            ]
        }
    finally:
        db.close()


@app.post("/api/queries/{query_id}/rerun")
def rerun_saved_query_endpoint(query_id: int, request: RerunQueryRequest):
    """
    Rerun a saved query against either original dataset or a newer dataset version.
    Tracks analysis lineage and detects result count / performance changes.
    """
    db = SessionLocal()
    try:
        saved = db.query(SavedQuery).filter(SavedQuery.id == query_id).first()
        if not saved:
            raise HTTPException(status_code=404, detail="Saved query not found.")

        target_ds_id = request.target_dataset_id or saved.dataset_id or 1
        tbl_name, p = resolve_dataset_path(target_ds_id, db)
        mappings = {tbl_name: p, "dataset": p, "t1": p}

        # Execute query
        exec_res = sql_engine.execute_query(saved.query_sql, mappings, page=1, page_size=100)

        # Retrieve previous lineage run if exists
        prev_lineage = db.query(AnalysisLineage).filter(
            AnalysisLineage.saved_query_id == query_id
        ).order_by(AnalysisLineage.id.desc()).first()

        row_delta = exec_res["total_rows"] - (prev_lineage.row_count if prev_lineage else exec_res["total_rows"])

        # Record new lineage run
        target_name = tbl_name
        try:
            target_rec = db.query(CSVFile).filter(CSVFile.id == int(target_ds_id)).first()
            if target_rec:
                target_name = target_rec.original_filename
        except Exception:
            pass

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lineage = AnalysisLineage(
            user_email=request.user_email,
            saved_query_id=saved.id,
            query_name=saved.query_name,
            query_sql=saved.query_sql,
            dataset_id=int(target_ds_id) if str(target_ds_id).isdigit() else 0,
            dataset_name=target_name,
            dataset_version=str(saved.dataset_version or "1"),
            row_count=exec_res["total_rows"],
            column_count=len(exec_res["columns"]),
            execution_time_ms=exec_res["execution_time_ms"],
            result_preview_json=json.dumps(exec_res["rows"][:5]),
            executed_at=now_str
        )
        db.add(lineage)

        saved.last_run_at = now_str
        db.commit()
        db.refresh(lineage)

        return {
            "success": True,
            "query_name": saved.query_name,
            "target_dataset": target_name,
            "execution": exec_res,
            "lineage": {
                "id": lineage.id,
                "executed_at": lineage.executed_at,
                "row_delta_vs_previous": row_delta,
                "has_diverged": (prev_lineage is not None and row_delta != 0)
            }
        }
    finally:
        db.close()


@app.get("/api/analysis/history")
def get_analysis_history_endpoint(user_email: str = Query(None)):
    """Fetch analysis lineage and reproduction logs."""
    db = SessionLocal()
    try:
        q = db.query(AnalysisLineage)
        if user_email:
            q = q.filter(AnalysisLineage.user_email == user_email)
        records = q.order_by(AnalysisLineage.id.desc()).limit(50).all()
        return {
            "success": True,
            "count": len(records),
            "history": [
                {
                    "id": r.id,
                    "saved_query_id": r.saved_query_id,
                    "query_name": r.query_name,
                    "query_sql": r.query_sql,
                    "dataset_name": r.dataset_name,
                    "dataset_version": r.dataset_version,
                    "row_count": r.row_count,
                    "column_count": r.column_count,
                    "execution_time_ms": r.execution_time_ms,
                    "executed_at": r.executed_at
                }
                for r in records
            ]
        }
    finally:
        db.close()


# =========================================================
# EXTERNAL DATASET DISCOVERY ENDPOINTS
# =========================================================

@app.get("/api/external-sources/search")
def search_external_sources_endpoint(query: str = Query(""), domain: str = Query("")):
    """Search authentic public dataset catalogues (World Bank, Open Health/Edu/IT)."""
    results = search_external_catalogue(query=query, domain=domain)
    return {
        "success": True,
        "count": len(results),
        "results": results
    }


@app.post("/api/external-sources/import")
def import_external_dataset_endpoint(request: ImportExternalRequest):
    """
    Live download and ingest an external public dataset into DataDock AI workspace.
    """
    db = SessionLocal()
    try:
        import_info = import_external_dataset(request.dataset_id, UPLOAD_DIR)

        # Register in CSVFile table
        user = db.query(User).filter(User.email == request.user_email).first()
        user_id = user.id if user else 1

        upload_record = CSVFile(
            filename=import_info["filename"],
            original_filename=import_info["original_filename"],
            user_id=user_id,
            user_email=request.user_email,
            upload_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            row_count=import_info["row_count"],
            file_size=import_info["file_size"],
            domain=import_info["domain"],
            version=1,
            source_type="discovered_world_bank",
            source_url=import_info.get("source_url"),
            license=import_info.get("license")
        )
        db.add(upload_record)
        db.commit()
        db.refresh(upload_record)

        return {
            "success": True,
            "message": f"Dataset '{import_info['original_filename']}' imported successfully into your workspace.",
            "dataset": {
                "id": upload_record.id,
                "name": upload_record.original_filename,
                "table_name": sanitize_table_name(upload_record.original_filename),
                "domain": upload_record.domain,
                "row_count": upload_record.row_count,
                "file_size": upload_record.file_size,
                "source": import_info["source"],
                "license": import_info["license"],
                "columns": import_info["columns"]
            }
        }
    except Exception as e:
        db.rollback()
        print("IMPORT EXTERNAL ERROR:", repr(e))
        raise HTTPException(status_code=500, detail=f"Failed to import external dataset: {str(e)}")
    finally:
        db.close()


# Mount frontend static directory if exists

FRONTEND_DIR = BASE_DIR.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")



