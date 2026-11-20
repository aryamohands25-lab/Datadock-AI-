"""
Domain-Specific Validation Rules Registry for DataDock AI (Finance & Healthcare)
"""

FINANCIAL_RULES = [
    {
        "id": "transaction_id_unique",
        "name": "Transaction / Loan ID Uniqueness",
        "description": "Primary identifier columns (Transaction ID, Loan ID, Account ID, Trade ID) must be strictly unique with zero duplicate records.",
        "type": "unique_key",
        "severity": "CRITICAL",
        "target_keywords": ["transaction_id", "loan_id", "account_id", "trade_id", "tx_id"]
    },
    {
        "id": "amount_non_null",
        "name": "Financial Amount Cannot Be Null",
        "description": "Monetary amount columns (Amount, Balance, Loan_Amount, Price, Revenue) must not contain missing or NULL values.",
        "type": "non_null_key",
        "severity": "CRITICAL",
        "target_keywords": ["amount", "balance", "price", "loan_amount", "revenue", "fee"]
    },
    {
        "id": "non_negative_amounts",
        "name": "Financial Amounts Permitted Range Check",
        "description": "Financial amount columns should not be negative unexpectedly.",
        "type": "non_negative",
        "severity": "HIGH",
        "target_keywords": ["amount", "balance", "price", "loan_amount", "revenue", "fee", "tax", "profit", "total"]
    },
    {
        "id": "credit_score_range",
        "name": "Credit Score Valid Range (300–900)",
        "description": "Credit score values must fall strictly within the standard financial scoring scale of 300 to 900.",
        "type": "range_check",
        "severity": "HIGH",
        "target_keywords": ["credit_score", "score", "cibil", "fico"],
        "min_val": 300,
        "max_val": 900
    },
    {
        "id": "positive_loan_amount",
        "name": "Positive Loan Amount Check",
        "description": "Loan principal amount must be strictly greater than 0.",
        "type": "range_check",
        "severity": "HIGH",
        "target_keywords": ["loan_amount", "disbursed_amount", "principal"],
        "min_val": 0.01,
        "max_val": None
    },
    {
        "id": "interest_rate_range",
        "name": "Interest Rate Range (0%–50%)",
        "description": "Interest rate percentage values should fall between 0% and 50%.",
        "type": "range_check",
        "severity": "MEDIUM",
        "target_keywords": ["interest_rate", "rate_pct", "apr", "roi"],
        "min_val": 0,
        "max_val": 50
    },
    {
        "id": "valid_transaction_type",
        "name": "Transaction Type Enumeration",
        "description": "Transaction type columns must strictly match expected categories (Credit, Debit, Transfer, Adjustment).",
        "type": "allowed_values",
        "severity": "MEDIUM",
        "target_keywords": ["transaction_type", "tx_type"],
        "allowed_values": ["CREDIT", "DEBIT", "TRANSFER", "ADJUSTMENT"]
    },
    {
        "id": "valid_financial_status",
        "name": "Financial Operational Status Check",
        "description": "Status columns should match expected operational states (Completed, Pending, Failed, Approved, Rejected, Under_Review).",
        "type": "allowed_values",
        "severity": "MEDIUM",
        "target_keywords": ["status", "state", "loan_status"],
        "allowed_values": ["COMPLETED", "PENDING", "FAILED", "APPROVED", "REJECTED", "UNDER_REVIEW", "ACTIVE", "SETTLED", "CANCELLED"]
    }
]


HEALTHCARE_RULES = [
    {
        "id": "patient_id_unique",
        "name": "Patient Identifier Uniqueness Check",
        "description": "Patient identifier columns (Patient_ID, EHR_ID, Record_ID) must be strictly unique across dataset records.",
        "type": "unique_key",
        "severity": "CRITICAL",
        "target_keywords": ["patient_id", "patient_no", "ehr_id", "record_id", "subject_id"]
    },
    {
        "id": "patient_id_non_null",
        "name": "Patient Identifier Non-Null Validation",
        "description": "Primary patient identifier cannot be NULL or empty.",
        "type": "non_null_key",
        "severity": "CRITICAL",
        "target_keywords": ["patient_id", "patient_no", "ehr_id", "record_id"]
    },
    {
        "id": "valid_age_range",
        "name": "Patient Age Valid Range Check (0–120 Years)",
        "description": "Patient age values must fall within human physiological limits of 0 to 120 years.",
        "type": "range_check",
        "severity": "HIGH",
        "target_keywords": ["age", "patient_age"],
        "min_val": 0,
        "max_val": 120
    },
    {
        "id": "glucose_valid_range",
        "name": "Blood Glucose Clinical Range (50–500 mg/dL)",
        "description": "Blood glucose laboratory measurements must fall within clinical physiological thresholds of 50 to 500 mg/dL.",
        "type": "range_check",
        "severity": "HIGH",
        "target_keywords": ["glucose", "blood_glucose", "sugar", "fasting_glucose"],
        "min_val": 50,
        "max_val": 500
    },
    {
        "id": "bmi_valid_range",
        "name": "Body Mass Index (BMI) Clinical Scale (10–70)",
        "description": "BMI values must fall within standard clinical index bounds of 10.0 to 70.0 kg/m².",
        "type": "range_check",
        "severity": "HIGH",
        "target_keywords": ["bmi", "body_mass_index"],
        "min_val": 10.0,
        "max_val": 70.0
    },
    {
        "id": "valid_gender_enum",
        "name": "Patient Gender Categorical Standard",
        "description": "Gender fields should match standardized categories (Male, Female, Other, Unknown).",
        "type": "allowed_values",
        "severity": "MEDIUM",
        "target_keywords": ["gender", "sex"],
        "allowed_values": ["MALE", "FEMALE", "OTHER", "UNKNOWN", "M", "F"]
    },
    {
        "id": "valid_diagnosis_enum",
        "name": "Clinical Diagnosis Categorical Check",
        "description": "Clinical diagnosis codes or labels must conform to standardized medical terminology.",
        "type": "allowed_values",
        "severity": "MEDIUM",
        "target_keywords": ["diagnosis", "condition", "disease"],
        "allowed_values": ["DIABETES", "HYPERTENSION", "HEALTHY", "HEART_DISEASE", "COVID-19", "PNEUMONIA", "ASTHMA", "NORMAL", "UNDER_OBSERVATION"]
    }
]


ACADEMICS_RULES = [
    {
        "id": "student_id_unique",
        "name": "Student / Enrollment ID Uniqueness",
        "description": "Primary academic identification columns (Student_ID, Enrollment_ID, Roll_No, Candidate_ID) must be strictly unique across all student records.",
        "type": "unique_key",
        "severity": "CRITICAL",
        "target_keywords": ["student_id", "enrollment_id", "roll_no", "candidate_id", "reg_no", "student_no"]
    },
    {
        "id": "student_id_non_null",
        "name": "Student Identifier Cannot Be Null",
        "description": "Primary student identifier must not contain missing, blank, or NULL values.",
        "type": "non_null_key",
        "severity": "CRITICAL",
        "target_keywords": ["student_id", "enrollment_id", "roll_no", "reg_no", "student_no"]
    },
    {
        "id": "gpa_valid_range",
        "name": "Standard GPA Scale Validation (0.0–4.0)",
        "description": "Grade Point Average values must strictly fall within the academic 4.0 grading scale (0.0 to 4.0).",
        "type": "range_check",
        "severity": "HIGH",
        "target_keywords": ["gpa", "grade_point_avg", "gpa_score"],
        "min_val": 0.0,
        "max_val": 4.0
    },
    {
        "id": "cgpa_valid_range",
        "name": "Cumulative GPA Scale Validation (0.0–10.0)",
        "description": "Cumulative Grade Point Average (CGPA / SGPA) values must fall within the 10.0 academic scale (0.0 to 10.0).",
        "type": "range_check",
        "severity": "HIGH",
        "target_keywords": ["cgpa", "sgpa"],
        "min_val": 0.0,
        "max_val": 10.0
    },
    {
        "id": "attendance_pct_range",
        "name": "Student Attendance Percentage (0%–100%)",
        "description": "Course attendance rate must be a valid percentage between 0% and 100%.",
        "type": "range_check",
        "severity": "HIGH",
        "target_keywords": ["attendance", "attendance_pct", "attendance_rate", "presence_pct"],
        "min_val": 0.0,
        "max_val": 100.0
    },
    {
        "id": "exam_marks_range",
        "name": "Academic Marks & Exam Scores (0–100)",
        "description": "Examination marks, assessment scores, and subject percentages must fall between 0 and 100.",
        "type": "range_check",
        "severity": "HIGH",
        "target_keywords": ["marks", "exam_score", "test_score", "percentage", "final_score", "quiz_score"],
        "min_val": 0.0,
        "max_val": 100.0
    },
    {
        "id": "credits_earned_range",
        "name": "Academic Credit Hours Range (0–200)",
        "description": "Completed academic credits must not be negative and should not exceed reasonable program totals (0 to 200 credits).",
        "type": "range_check",
        "severity": "MEDIUM",
        "target_keywords": ["credit", "credits_earned", "credit_hours", "total_credits"],
        "min_val": 0.0,
        "max_val": 200.0
    },
    {
        "id": "valid_letter_grade",
        "name": "Standard Letter Grade Evaluation",
        "description": "Reported letter grades must match standard academic grade scales (A+, A, B, C, D, F, Pass, Fail, etc.).",
        "type": "allowed_values",
        "severity": "MEDIUM",
        "target_keywords": ["grade", "letter_grade", "final_grade"],
        "allowed_values": ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "F", "PASS", "FAIL", "INCOMPLETE", "W", "P", "AUDIT"]
    },
    {
        "id": "valid_academic_status",
        "name": "Academic Standing & Enrollment Status",
        "description": "Student enrollment and standing status must conform to official registrar states (Enrolled, Active, Graduated, Probation, Suspended, Dropped, On_Leave).",
        "type": "allowed_values",
        "severity": "MEDIUM",
        "target_keywords": ["academic_status", "enrollment_status", "student_status", "standing"],
        "allowed_values": ["ENROLLED", "ACTIVE", "GRADUATED", "PROBATION", "SUSPENDED", "DROPPED", "ON_LEAVE", "WITHDRAWN", "ALUMNI", "TRANSFERRED"]
    },
    {
        "id": "student_age_range",
        "name": "Student Age Verification (3–100 Years)",
        "description": "Student age values must fall within reasonable educational enrollment ranges of 3 to 100 years.",
        "type": "range_check",
        "severity": "HIGH",
        "target_keywords": ["student_age", "age"],
        "min_val": 3,
        "max_val": 100
    }
]


IT_SOFTWARE_RULES = [
    {
        "id": "ticket_id_unique",
        "name": "Incident / Log / Trace ID Uniqueness",
        "description": "System record identifiers (Incident_ID, Log_ID, Ticket_ID, Trace_ID, Request_ID, Server_ID) must be strictly unique with zero duplicate entries.",
        "type": "unique_key",
        "severity": "CRITICAL",
        "target_keywords": ["ticket_id", "incident_id", "log_id", "trace_id", "request_id", "server_id", "job_id", "build_id", "session_id"]
    },
    {
        "id": "ticket_id_non_null",
        "name": "System Identifier Non-Null Validation",
        "description": "Primary system log, server, or incident identifier must not be empty or NULL.",
        "type": "non_null_key",
        "severity": "CRITICAL",
        "target_keywords": ["ticket_id", "incident_id", "log_id", "trace_id", "request_id", "server_id"]
    },
    {
        "id": "resource_utilization_range",
        "name": "Server Resource Utilization Percentage (0%–100%)",
        "description": "CPU, memory, disk, and GPU utilization metrics must fall within standard physical operational limits of 0% to 100%.",
        "type": "range_check",
        "severity": "HIGH",
        "target_keywords": ["cpu_usage", "memory_usage", "disk_usage", "cpu_pct", "memory_pct", "gpu_usage", "utilization"],
        "min_val": 0.0,
        "max_val": 100.0
    },
    {
        "id": "latency_non_negative",
        "name": "API / Query Latency Non-Negative Check",
        "description": "Response time and network latency measurements cannot be negative.",
        "type": "non_negative",
        "severity": "HIGH",
        "target_keywords": ["latency", "response_time", "duration_ms", "rtt_ms", "execution_time"]
    },
    {
        "id": "http_status_code_range",
        "name": "HTTP Status Code Protocol Range (100–599)",
        "description": "Web and API response status codes must be valid standard RFC HTTP status codes between 100 and 599.",
        "type": "range_check",
        "severity": "HIGH",
        "target_keywords": ["status_code", "http_status", "response_code", "http_code"],
        "min_val": 100,
        "max_val": 599
    },
    {
        "id": "error_rate_pct_range",
        "name": "Service Error Rate & Packet Loss (0%–100%)",
        "description": "System error rates, packet loss ratios, and timeout percentages must fall between 0% and 100%.",
        "type": "range_check",
        "severity": "HIGH",
        "target_keywords": ["error_rate", "failure_rate", "packet_loss", "drop_rate"],
        "min_val": 0.0,
        "max_val": 100.0
    },
    {
        "id": "uptime_availability_range",
        "name": "System Availability & Uptime (0%–100%)",
        "description": "System uptime and SLA compliance percentages must fall between 0% and 100%.",
        "type": "range_check",
        "severity": "HIGH",
        "target_keywords": ["uptime", "availability", "sla_pct", "uptime_pct"],
        "min_val": 0.0,
        "max_val": 100.0
    },
    {
        "id": "valid_incident_severity",
        "name": "Incident Severity & Log Level Standards",
        "description": "Incident severity and logging levels must conform to standard infrastructure taxonomies (CRITICAL, HIGH, MEDIUM, LOW, P1-P4, INFO, ERROR, WARN).",
        "type": "allowed_values",
        "severity": "MEDIUM",
        "target_keywords": ["severity", "priority", "log_level", "incident_level", "alert_level"],
        "allowed_values": ["CRITICAL", "HIGH", "MEDIUM", "LOW", "P1", "P2", "P3", "P4", "INFO", "WARN", "WARNING", "ERROR", "FATAL", "DEBUG", "TRACE"]
    },
    {
        "id": "valid_system_status",
        "name": "Service Health & Operational Lifecycle Status",
        "description": "System states and ticket statuses must match operational standards (HEALTHY, DEGRADED, DOWN, ACTIVE, RESOLVED, OPEN, CLOSED, IN_PROGRESS).",
        "type": "allowed_values",
        "severity": "MEDIUM",
        "target_keywords": ["system_status", "service_status", "health", "state", "ticket_status"],
        "allowed_values": ["HEALTHY", "DEGRADED", "DOWN", "ACTIVE", "RESOLVED", "OPEN", "CLOSED", "IN_PROGRESS", "ONLINE", "OFFLINE", "STANDBY", "DEPLOYED", "FAILED", "MAINTENANCE"]
    }
]


def get_rules_for_domain(domain: str) -> list:
    """Returns rule set based on selected domain ('finance', 'healthcare', 'academics', 'software_systems')."""
    domain_clean = str(domain).lower().strip()
    if domain_clean in ("healthcare", "health"):
        return list(HEALTHCARE_RULES)
    elif domain_clean in ("academics", "education", "academic"):
        return list(ACADEMICS_RULES)
    elif domain_clean in ("software_systems", "it", "software", "it_software", "it_systems"):
        return list(IT_SOFTWARE_RULES)
    return list(FINANCIAL_RULES)
