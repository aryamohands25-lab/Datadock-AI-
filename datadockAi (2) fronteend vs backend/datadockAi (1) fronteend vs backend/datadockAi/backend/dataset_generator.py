import random
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

def generate_bank_transactions_preset():
    """
    Generates V1 and V2 Bank Transaction datasets matching the problem specification:
    - V1: 10,000 transactions, 1.2% missing amounts, 5 duplicate IDs, 2 invalid amounts, 3 transaction types, avg ~₹4,250
    - V2: 12,000 transactions, 9.8% missing amounts, 127 duplicate IDs, 54 invalid amounts, 4 transaction types, avg ~₹9,850
    """
    random.seed(42)
    np.random.seed(42)

    # --- VERSION 1 ---
    n_rows_1 = 10000
    tx_ids_1 = [f"T{str(i).zfill(5)}" for i in range(1, n_rows_1 + 1)]
    # Inject 5 duplicate IDs
    for i in range(5):
        tx_ids_1[random.randint(100, n_rows_1 - 1)] = tx_ids_1[i]

    cust_ids_1 = [f"C{random.randint(101, 1500)}" for _ in range(n_rows_1)]
    amounts_1 = np.random.exponential(scale=4250.0, size=n_rows_1)
    amounts_1 = np.round(amounts_1, 2)
    
    # 1.2% null amounts
    null_idx_1 = random.sample(range(n_rows_1), int(n_rows_1 * 0.012))
    amounts_list_1 = list(amounts_1)
    for idx in null_idx_1:
        amounts_list_1[idx] = None

    # 2 invalid (negative) amounts
    neg_idx_1 = random.sample([i for i in range(n_rows_1) if i not in null_idx_1], 2)
    for idx in neg_idx_1:
        amounts_list_1[idx] = -round(random.uniform(100, 5000), 2)

    types_1 = random.choices(["Credit", "Debit", "Transfer"], weights=[0.45, 0.45, 0.10], k=n_rows_1)
    statuses_1 = random.choices(["Completed", "Pending", "Failed"], weights=[0.85, 0.10, 0.05], k=n_rows_1)

    df_v1 = pd.DataFrame({
        "Transaction_ID": tx_ids_1,
        "Customer_ID": cust_ids_1,
        "Amount": amounts_list_1,
        "Transaction_Type": types_1,
        "Status": statuses_1
    })

    # --- VERSION 2 ---
    n_rows_2 = 12000
    tx_ids_2 = [f"T{str(i).zfill(5)}" for i in range(1, n_rows_2 + 1)]
    # Inject 127 duplicate IDs
    dup_sources = random.choices(range(500), k=127)
    dup_targets = random.sample(range(500, n_rows_2), 127)
    for s, t in zip(dup_sources, dup_targets):
        tx_ids_2[t] = tx_ids_2[s]

    cust_ids_2 = [f"C{random.randint(101, 1750)}" for _ in range(n_rows_2)]
    
    # Higher average ~₹9,850
    amounts_2 = np.random.exponential(scale=9850.0, size=n_rows_2)
    amounts_2 = np.round(amounts_2, 2)
    
    # 9.8% null amounts (Regression!)
    null_idx_2 = random.sample(range(n_rows_2), int(n_rows_2 * 0.098))
    amounts_list_2 = list(amounts_2)
    for idx in null_idx_2:
        amounts_list_2[idx] = None

    # 54 invalid (negative) amounts (Regression!)
    neg_idx_2 = random.sample([i for i in range(n_rows_2) if i not in null_idx_2], 54)
    for idx in neg_idx_2:
        amounts_list_2[idx] = -round(random.uniform(500, 15000), 2)

    # 4 Transaction types (New category: 'Adjustment')
    types_2 = random.choices(["Credit", "Debit", "Transfer", "Adjustment"], weights=[0.40, 0.40, 0.10, 0.10], k=n_rows_2)
    statuses_2 = random.choices(["Completed", "Pending", "Failed"], weights=[0.80, 0.12, 0.08], k=n_rows_2)

    df_v2 = pd.DataFrame({
        "Transaction_ID": tx_ids_2,
        "Customer_ID": cust_ids_2,
        "Amount": amounts_list_2,
        "Transaction_Type": types_2,
        "Status": statuses_2
    })

    file_v1_path = UPLOADS_DIR / "bank_transactions_v1.csv"
    file_v2_path = UPLOADS_DIR / "bank_transactions_v2.csv"

    df_v1.to_csv(file_v1_path, index=False)
    df_v2.to_csv(file_v2_path, index=False)

    return str(file_v1_path), str(file_v2_path)


def generate_loan_portfolio_preset():
    """
    Generates V1 and V2 Loan Portfolio datasets:
    - V1: Clean loan records with valid credit scores (300-850), positive loan amounts, valid interest rates.
    - V2: Loan records containing rule violations (Credit Score = 950 [max is 900], negative interest rates, missing Loan IDs).
    """
    random.seed(101)
    np.random.seed(101)

    n_rows = 5000

    # V1 Loan Dataset
    loan_ids_1 = [f"LN-{str(i).zfill(6)}" for i in range(10001, 10001 + n_rows)]
    cust_ids_1 = [f"CUST-{random.randint(2000, 9000)}" for _ in range(n_rows)]
    loan_amounts_1 = [round(random.uniform(50000, 1500000), 2) for _ in range(n_rows)]
    interest_rates_1 = [round(random.uniform(6.5, 18.0), 2) for _ in range(n_rows)]
    credit_scores_1 = [random.randint(580, 850) for _ in range(n_rows)]
    loan_statuses_1 = random.choices(["Approved", "Pending", "Rejected"], weights=[0.70, 0.20, 0.10], k=n_rows)

    df_v1 = pd.DataFrame({
        "Loan_ID": loan_ids_1,
        "Customer_ID": cust_ids_1,
        "Loan_Amount": loan_amounts_1,
        "Interest_Rate": interest_rates_1,
        "Credit_Score": credit_scores_1,
        "Loan_Status": loan_statuses_1
    })

    # V2 Loan Dataset (With Violations)
    n_rows_2 = 5500
    loan_ids_2 = [f"LN-{str(i).zfill(6)}" for i in range(10001, 10001 + n_rows_2)]
    cust_ids_2 = [f"CUST-{random.randint(2000, 9500)}" for _ in range(n_rows_2)]
    loan_amounts_2 = [round(random.uniform(50000, 2000000), 2) for _ in range(n_rows_2)]
    interest_rates_2 = [round(random.uniform(6.5, 22.0), 2) for _ in range(n_rows_2)]
    credit_scores_2 = [random.randint(550, 850) for _ in range(n_rows_2)]

    # Inject Credit Score = 950 violations (out of permitted range 300-900)
    invalid_score_rows = random.sample(range(n_rows_2), 38)
    for idx in invalid_score_rows:
        credit_scores_2[idx] = 950

    # Inject negative loan amounts
    invalid_amount_rows = random.sample([i for i in range(n_rows_2) if i not in invalid_score_rows], 15)
    for idx in invalid_amount_rows:
        loan_amounts_2[idx] = -50000.00

    # Inject null Loan IDs
    null_id_rows = random.sample([i for i in range(n_rows_2) if i not in invalid_score_rows and i not in invalid_amount_rows], 12)
    for idx in null_id_rows:
        loan_ids_2[idx] = ""

    loan_statuses_2 = random.choices(["Approved", "Pending", "Rejected", "Under_Review"], weights=[0.65, 0.15, 0.10, 0.10], k=n_rows_2)

    df_v2 = pd.DataFrame({
        "Loan_ID": loan_ids_2,
        "Customer_ID": cust_ids_2,
        "Loan_Amount": loan_amounts_2,
        "Interest_Rate": interest_rates_2,
        "Credit_Score": credit_scores_2,
        "Loan_Status": loan_statuses_2
    })

    file_v1_path = UPLOADS_DIR / "loan_portfolio_v1.csv"
    file_v2_path = UPLOADS_DIR / "loan_portfolio_v2.csv"

    df_v1.to_csv(file_v1_path, index=False)
    df_v2.to_csv(file_v2_path, index=False)

    return str(file_v1_path), str(file_v2_path)


def generate_patient_diagnostics_preset():
    """
    Generates V1 and V2 Healthcare Patient Diagnostics datasets:
    - V1: 5,000 records, 2.0% missing Glucose, 5 duplicate Patient IDs, valid Age (18-85), valid BMI (18-35).
    - V2: 6,000 records, 14.0% missing Glucose (⚠ Regression!), 73 duplicate Patient IDs (⚠ Regression!),
          out-of-range Age = 150 values (⚠ Rule violation), invalid BMI, and new Diagnosis category 'Covid-19'.
    """
    random.seed(77)
    np.random.seed(77)

    # --- VERSION 1 ---
    n_rows_1 = 5000
    p_ids_1 = [f"P-{str(i).zfill(6)}" for i in range(1001, 1001 + n_rows_1)]
    # 5 duplicate patient IDs
    for i in range(5):
        p_ids_1[random.randint(100, n_rows_1 - 1)] = p_ids_1[i]

    ages_1 = [random.randint(18, 85) for _ in range(n_rows_1)]
    genders_1 = random.choices(["Male", "Female"], weights=[0.49, 0.51], k=n_rows_1)
    glucose_1 = [round(random.uniform(70.0, 180.0), 1) for _ in range(n_rows_1)]
    bmi_1 = [round(random.uniform(18.5, 34.0), 1) for _ in range(n_rows_1)]
    bp_sys_1 = [random.randint(110, 140) for _ in range(n_rows_1)]
    bp_dia_1 = [random.randint(70, 90) for _ in range(n_rows_1)]
    bp_1 = [f"{s}/{d}" for s, d in zip(bp_sys_1, bp_dia_1)]
    diagnoses_1 = random.choices(["Healthy", "Diabetes", "Hypertension"], weights=[0.60, 0.25, 0.15], k=n_rows_1)

    # 2.0% null glucose
    null_g_1 = random.sample(range(n_rows_1), int(n_rows_1 * 0.02))
    glucose_list_1 = list(glucose_1)
    for idx in null_g_1:
        glucose_list_1[idx] = None

    df_v1 = pd.DataFrame({
        "Patient_ID": p_ids_1,
        "Age": ages_1,
        "Gender": genders_1,
        "Blood_Pressure": bp_1,
        "Glucose": glucose_list_1,
        "BMI": bmi_1,
        "Diagnosis": diagnoses_1
    })

    # --- VERSION 2 ---
    n_rows_2 = 6000
    p_ids_2 = [f"P-{str(i).zfill(6)}" for i in range(1001, 1001 + n_rows_2)]
    # 73 duplicate patient IDs (Regression!)
    dup_sources = random.choices(range(300), k=73)
    dup_targets = random.sample(range(300, n_rows_2), 73)
    for s, t in zip(dup_sources, dup_targets):
        p_ids_2[t] = p_ids_2[s]

    ages_2 = [random.randint(18, 88) for _ in range(n_rows_2)]
    # Inject out-of-range Age = 150 (Rule violation!)
    invalid_age_idx = random.sample(range(n_rows_2), 24)
    for idx in invalid_age_idx:
        ages_2[idx] = 150

    genders_2 = random.choices(["Male", "Female"], weights=[0.48, 0.52], k=n_rows_2)
    glucose_2 = [round(random.uniform(70.0, 220.0), 1) for _ in range(n_rows_2)]

    # 14.0% null glucose (Regression!)
    null_g_2 = random.sample(range(n_rows_2), int(n_rows_2 * 0.14))
    glucose_list_2 = list(glucose_2)
    for idx in null_g_2:
        glucose_list_2[idx] = None

    bmi_2 = [round(random.uniform(18.5, 38.0), 1) for _ in range(n_rows_2)]
    # Inject invalid BMI = 99.9
    invalid_bmi_idx = random.sample([i for i in range(n_rows_2) if i not in invalid_age_idx], 18)
    for idx in invalid_bmi_idx:
        bmi_2[idx] = 99.9

    bp_sys_2 = [random.randint(110, 150) for _ in range(n_rows_2)]
    bp_dia_2 = [random.randint(70, 95) for _ in range(n_rows_2)]
    bp_2 = [f"{s}/{d}" for s, d in zip(bp_sys_2, bp_dia_2)]

    # 4 Diagnosis categories (New category: 'Covid-19')
    diagnoses_2 = random.choices(["Healthy", "Diabetes", "Hypertension", "Covid-19"], weights=[0.50, 0.25, 0.15, 0.10], k=n_rows_2)

    df_v2 = pd.DataFrame({
        "Patient_ID": p_ids_2,
        "Age": ages_2,
        "Gender": genders_2,
        "Blood_Pressure": bp_2,
        "Glucose": glucose_list_2,
        "BMI": bmi_2,
        "Diagnosis": diagnoses_2
    })

    file_v1_path = UPLOADS_DIR / "patient_diagnostics_v1.csv"
    file_v2_path = UPLOADS_DIR / "patient_diagnostics_v2.csv"

    df_v1.to_csv(file_v1_path, index=False)
    df_v2.to_csv(file_v2_path, index=False)

    return str(file_v1_path), str(file_v2_path)


def generate_student_academics_preset():
    """
    Generates V1 and V2 Academic & Educational student datasets:
    - V1: 5,000 student records, clean GPA (2.1–4.0), attendance (75%–100%), 5 duplicate IDs, 1.2% null GPA, approved statuses.
    - V2: 6,000 student records with regressions: 58 duplicate student IDs, 12.5% null GPA,
          out-of-range GPA = 5.2 (exceeding 4.0 max scale), negative/out-of-range attendance, new status 'Suspended'.
    """
    random.seed(88)
    np.random.seed(88)

    # --- VERSION 1 ---
    n_rows_1 = 5000
    s_ids_1 = [f"STU-{str(i).zfill(5)}" for i in range(1001, 1001 + n_rows_1)]
    # 5 duplicate student IDs
    for i in range(5):
        s_ids_1[random.randint(100, n_rows_1 - 1)] = s_ids_1[i]

    depts = ["Computer Science", "Electrical Engineering", "Data Science", "Business Administration", "Mathematics"]
    dept_1 = random.choices(depts, weights=[0.30, 0.20, 0.20, 0.15, 0.15], k=n_rows_1)
    
    gpa_raw_1 = np.clip(np.random.normal(loc=3.25, scale=0.45, size=n_rows_1), 2.0, 4.0)
    gpa_1 = [round(float(v), 2) for v in gpa_raw_1]
    
    # 1.2% null GPA
    null_gpa_1 = random.sample(range(n_rows_1), int(n_rows_1 * 0.012))
    for idx in null_gpa_1:
        gpa_1[idx] = None

    attendance_1 = [round(random.uniform(75.0, 99.5), 1) for _ in range(n_rows_1)]
    exam_scores_1 = [round(random.uniform(62.0, 98.0), 1) for _ in range(n_rows_1)]
    credits_1 = [random.randint(15, 120) for _ in range(n_rows_1)]
    statuses_1 = random.choices(["Enrolled", "Active", "Graduated"], weights=[0.65, 0.25, 0.10], k=n_rows_1)

    df_v1 = pd.DataFrame({
        "Student_ID": s_ids_1,
        "Department": dept_1,
        "GPA": gpa_1,
        "Attendance_Pct": attendance_1,
        "Exam_Score": exam_scores_1,
        "Credits_Earned": credits_1,
        "Academic_Status": statuses_1
    })

    # --- VERSION 2 ---
    n_rows_2 = 6000
    s_ids_2 = [f"STU-{str(i).zfill(5)}" for i in range(1001, 1001 + n_rows_2)]
    # 58 duplicate student IDs (Regression!)
    dup_sources = random.choices(range(400), k=58)
    dup_targets = random.sample(range(400, n_rows_2), 58)
    for s, t in zip(dup_sources, dup_targets):
        s_ids_2[t] = s_ids_2[s]

    dept_2 = random.choices(depts, weights=[0.28, 0.22, 0.20, 0.15, 0.15], k=n_rows_2)
    
    gpa_raw_2 = np.clip(np.random.normal(loc=3.10, scale=0.55, size=n_rows_2), 1.8, 4.0)
    gpa_2 = [round(float(v), 2) for v in gpa_raw_2]

    # 12.5% null GPA (Regression!)
    null_gpa_2 = random.sample(range(n_rows_2), int(n_rows_2 * 0.125))
    for idx in null_gpa_2:
        gpa_2[idx] = None

    # Inject out-of-scale GPA = 5.2 (Rule violation! Max scale is 4.0)
    invalid_gpa_idx = random.sample([i for i in range(n_rows_2) if i not in null_gpa_2], 28)
    for idx in invalid_gpa_idx:
        gpa_2[idx] = 5.20

    attendance_2 = [round(random.uniform(65.0, 99.0), 1) for _ in range(n_rows_2)]
    # Inject out-of-range attendance (115% and negative attendance)
    invalid_att_idx = random.sample([i for i in range(n_rows_2) if i not in invalid_gpa_idx], 22)
    for i, idx in enumerate(invalid_att_idx):
        attendance_2[idx] = 115.0 if i % 2 == 0 else -10.0

    exam_scores_2 = [round(random.uniform(50.0, 96.0), 1) for _ in range(n_rows_2)]
    credits_2 = [random.randint(15, 130) for _ in range(n_rows_2)]
    
    # 4 Status categories (New category: 'Suspended')
    statuses_2 = random.choices(["Enrolled", "Active", "Graduated", "Suspended"], weights=[0.58, 0.22, 0.10, 0.10], k=n_rows_2)

    df_v2 = pd.DataFrame({
        "Student_ID": s_ids_2,
        "Department": dept_2,
        "GPA": gpa_2,
        "Attendance_Pct": attendance_2,
        "Exam_Score": exam_scores_2,
        "Credits_Earned": credits_2,
        "Academic_Status": statuses_2
    })

    file_v1_path = UPLOADS_DIR / "student_academics_v1.csv"
    file_v2_path = UPLOADS_DIR / "student_academics_v2.csv"

    df_v1.to_csv(file_v1_path, index=False)
    df_v2.to_csv(file_v2_path, index=False)

    return str(file_v1_path), str(file_v2_path)


def generate_system_metrics_preset():
    """
    Generates V1 and V2 IT Infrastructure & Software Systems telemetry datasets:
    - V1: 5,000 incident/request telemetry records, low latency (20-450ms), CPU (15-75%), 4 duplicate IDs, 1.0% nulls, 2xx HTTP codes.
    - V2: 6,200 incident records with regressions: 82 duplicate IDs, 13.0% null response times,
          out-of-range CPU = 145% (>100% max limit), negative response times (-50ms), 500 error spikes, critical alerts.
    """
    random.seed(99)
    np.random.seed(99)

    # --- VERSION 1 ---
    n_rows_1 = 5000
    t_ids_1 = [f"INC-{str(i).zfill(6)}" for i in range(1001, 1001 + n_rows_1)]
    # 4 duplicate incident IDs
    for i in range(4):
        t_ids_1[random.randint(100, n_rows_1 - 1)] = t_ids_1[i]

    services = ["auth-gateway", "payment-api", "user-service", "order-processor", "search-indexer"]
    svc_1 = random.choices(services, weights=[0.25, 0.20, 0.25, 0.15, 0.15], k=n_rows_1)
    
    latency_1 = [round(float(v), 1) for v in np.random.exponential(scale=120.0, size=n_rows_1) + 20.0]
    # 1.0% null latency
    null_lat_1 = random.sample(range(n_rows_1), int(n_rows_1 * 0.01))
    for idx in null_lat_1:
        latency_1[idx] = None

    cpu_1 = [round(random.uniform(15.0, 75.0), 1) for _ in range(n_rows_1)]
    error_rates_1 = [round(random.uniform(0.01, 2.50), 2) for _ in range(n_rows_1)]
    http_codes_1 = random.choices([200, 201, 204, 304], weights=[0.85, 0.08, 0.04, 0.03], k=n_rows_1)
    severities_1 = random.choices(["LOW", "INFO", "MEDIUM"], weights=[0.70, 0.22, 0.08], k=n_rows_1)
    system_statuses_1 = random.choices(["HEALTHY", "ACTIVE"], weights=[0.92, 0.08], k=n_rows_1)

    df_v1 = pd.DataFrame({
        "Incident_ID": t_ids_1,
        "Service_Name": svc_1,
        "Response_Time_ms": latency_1,
        "CPU_Usage_Pct": cpu_1,
        "Error_Rate_Pct": error_rates_1,
        "HTTP_Status": http_codes_1,
        "Severity": severities_1,
        "System_Status": system_statuses_1
    })

    # --- VERSION 2 ---
    n_rows_2 = 6200
    t_ids_2 = [f"INC-{str(i).zfill(6)}" for i in range(1001, 1001 + n_rows_2)]
    # 82 duplicate incident IDs (Regression!)
    dup_sources = random.choices(range(500), k=82)
    dup_targets = random.sample(range(500, n_rows_2), 82)
    for s, t in zip(dup_sources, dup_targets):
        t_ids_2[t] = t_ids_2[s]

    svc_2 = random.choices(services, weights=[0.25, 0.20, 0.25, 0.15, 0.15], k=n_rows_2)
    
    latency_2 = [round(float(v), 1) for v in np.random.exponential(scale=380.0, size=n_rows_2) + 50.0]
    # 13.0% null latency (Regression!)
    null_lat_2 = random.sample(range(n_rows_2), int(n_rows_2 * 0.13))
    for idx in null_lat_2:
        latency_2[idx] = None

    # Inject negative latency (-50ms)
    invalid_lat_idx = random.sample([i for i in range(n_rows_2) if i not in null_lat_2], 18)
    for idx in invalid_lat_idx:
        latency_2[idx] = -50.0

    cpu_2 = [round(random.uniform(25.0, 92.0), 1) for _ in range(n_rows_2)]
    # Inject out-of-scale CPU = 145.0% (>100% max capacity violation!)
    invalid_cpu_idx = random.sample([i for i in range(n_rows_2) if i not in invalid_lat_idx], 35)
    for idx in invalid_cpu_idx:
        cpu_2[idx] = 145.0

    error_rates_2 = [round(random.uniform(0.1, 18.5), 2) for _ in range(n_rows_2)]
    # Spike 500, 503 error codes
    http_codes_2 = random.choices([200, 201, 500, 503], weights=[0.60, 0.08, 0.20, 0.12], k=n_rows_2)
    severities_2 = random.choices(["LOW", "MEDIUM", "HIGH", "CRITICAL"], weights=[0.40, 0.25, 0.20, 0.15], k=n_rows_2)
    system_statuses_2 = random.choices(["HEALTHY", "DEGRADED", "DOWN"], weights=[0.55, 0.30, 0.15], k=n_rows_2)

    df_v2 = pd.DataFrame({
        "Incident_ID": t_ids_2,
        "Service_Name": svc_2,
        "Response_Time_ms": latency_2,
        "CPU_Usage_Pct": cpu_2,
        "Error_Rate_Pct": error_rates_2,
        "HTTP_Status": http_codes_2,
        "Severity": severities_2,
        "System_Status": system_statuses_2
    })

    file_v1_path = UPLOADS_DIR / "system_metrics_v1.csv"
    file_v2_path = UPLOADS_DIR / "system_metrics_v2.csv"

    df_v1.to_csv(file_v1_path, index=False)
    df_v2.to_csv(file_v2_path, index=False)

    return str(file_v1_path), str(file_v2_path)


def generate_clinical_vitals_preset():
    """
    Generates V1 and V2 Clinical Lab & Hospital Vitals datasets [Healthcare]:
    - V1: 4,500 patient EHR records, valid Glucose (70-170 mg/dL), valid BMI (18.5-32.0), clean Record IDs.
    - V2: 5,200 records with regressions: 45 duplicate Patient IDs, Blood Glucose = 550 mg/dL,
          extreme BMI = 88.0, 11.8% null Glucose, unapproved Diagnosis categories.
    """
    random.seed(66)
    np.random.seed(66)

    # --- VERSION 1 ---
    n_rows_1 = 4500
    r_ids_1 = [f"EHR-{str(i).zfill(6)}" for i in range(1001, 1001 + n_rows_1)]
    p_ids_1 = [f"P-{random.randint(1000, 4800)}" for _ in range(n_rows_1)]
    glucose_1 = [round(random.uniform(75.0, 160.0), 1) for _ in range(n_rows_1)]
    bmi_1 = [round(random.uniform(19.0, 31.5), 1) for _ in range(n_rows_1)]
    age_1 = [random.randint(18, 80) for _ in range(n_rows_1)]
    conditions_1 = random.choices(["Normal", "Healthy", "Diabetes", "Hypertension"], weights=[0.45, 0.30, 0.15, 0.10], k=n_rows_1)

    # 1.5% null glucose
    null_g_1 = random.sample(range(n_rows_1), int(n_rows_1 * 0.015))
    for idx in null_g_1:
        glucose_1[idx] = None

    df_v1 = pd.DataFrame({
        "Record_ID": r_ids_1,
        "Patient_ID": p_ids_1,
        "Age": age_1,
        "Glucose": glucose_1,
        "BMI": bmi_1,
        "Diagnosis": conditions_1
    })

    # --- VERSION 2 ---
    n_rows_2 = 5200
    r_ids_2 = [f"EHR-{str(i).zfill(6)}" for i in range(1001, 1001 + n_rows_2)]
    p_ids_2 = [f"P-{random.randint(1000, 4800)}" for _ in range(n_rows_2)]
    # Duplicate Record IDs
    dup_sources = random.choices(range(300), k=45)
    dup_targets = random.sample(range(300, n_rows_2), 45)
    for s, t in zip(dup_sources, dup_targets):
        r_ids_2[t] = r_ids_2[s]

    age_2 = [random.randint(18, 84) for _ in range(n_rows_2)]
    glucose_2 = [round(random.uniform(70.0, 190.0), 1) for _ in range(n_rows_2)]
    # 11.8% null glucose (Regression)
    null_g_2 = random.sample(range(n_rows_2), int(n_rows_2 * 0.118))
    for idx in null_g_2:
        glucose_2[idx] = None

    # Inject Glucose = 550 mg/dL (Out-of-range clinical violation)
    invalid_g_idx = random.sample([i for i in range(n_rows_2) if i not in null_g_2], 26)
    for idx in invalid_g_idx:
        glucose_2[idx] = 550.0

    bmi_2 = [round(random.uniform(19.0, 36.0), 1) for _ in range(n_rows_2)]
    # Inject BMI = 88.0 (Out of 10-70 clinical scale)
    invalid_bmi_idx = random.sample([i for i in range(n_rows_2) if i not in invalid_g_idx], 20)
    for idx in invalid_bmi_idx:
        bmi_2[idx] = 88.0

    conditions_2 = random.choices(["Normal", "Healthy", "Diabetes", "Under_Observation"], weights=[0.40, 0.25, 0.20, 0.15], k=n_rows_2)

    df_v2 = pd.DataFrame({
        "Record_ID": r_ids_2,
        "Patient_ID": p_ids_2,
        "Age": age_2,
        "Glucose": glucose_2,
        "BMI": bmi_2,
        "Diagnosis": conditions_2
    })

    file_v1_path = UPLOADS_DIR / "clinical_vitals_v1.csv"
    file_v2_path = UPLOADS_DIR / "clinical_vitals_v2.csv"

    df_v1.to_csv(file_v1_path, index=False)
    df_v2.to_csv(file_v2_path, index=False)

    return str(file_v1_path), str(file_v2_path)


def generate_course_enrollment_preset():
    """
    Generates V1 and V2 Academic Course Enrollment & Grading datasets [Academics]:
    - V1: 4,000 student course enrollments, credits (1-6 per course), valid letter grades (A, B, C, D), valid exam scores (60-98).
    - V2: 4,800 records with regressions: 52 duplicate Enrollment IDs, credits exceeding limits,
          exam scores = 105.0%, 14.0% null letter grades, unapproved registrar statuses.
    """
    random.seed(55)
    np.random.seed(55)

    # --- VERSION 1 ---
    n_rows_1 = 4000
    e_ids_1 = [f"ENR-{str(i).zfill(6)}" for i in range(10001, 10001 + n_rows_1)]
    s_ids_1 = [f"STU-{random.randint(1001, 3500)}" for _ in range(n_rows_1)]
    courses = ["CS101", "CS201", "MATH150", "DATA300", "ENG102", "PHYS110"]
    c_1 = random.choices(courses, weights=[0.25, 0.20, 0.20, 0.15, 0.10, 0.10], k=n_rows_1)
    credits_1 = random.choices([3, 4, 2], weights=[0.60, 0.30, 0.10], k=n_rows_1)
    scores_1 = [round(random.uniform(62.0, 98.0), 1) for _ in range(n_rows_1)]
    grades_1 = random.choices(["A", "A-", "B+", "B", "B-", "C+", "C"], weights=[0.25, 0.20, 0.20, 0.15, 0.10, 0.05, 0.05], k=n_rows_1)
    statuses_1 = random.choices(["Enrolled", "Active", "Completed"], weights=[0.50, 0.30, 0.20], k=n_rows_1)

    df_v1 = pd.DataFrame({
        "Enrollment_ID": e_ids_1,
        "Student_ID": s_ids_1,
        "Course_Code": c_1,
        "Credits_Earned": credits_1,
        "Exam_Score": scores_1,
        "Letter_Grade": grades_1,
        "Academic_Status": statuses_1
    })

    # --- VERSION 2 ---
    n_rows_2 = 4800
    e_ids_2 = [f"ENR-{str(i).zfill(6)}" for i in range(10001, 10001 + n_rows_2)]
    # Duplicate Enrollment IDs
    dup_sources = random.choices(range(400), k=52)
    dup_targets = random.sample(range(400, n_rows_2), 52)
    for s, t in zip(dup_sources, dup_targets):
        e_ids_2[t] = e_ids_2[s]

    s_ids_2 = [f"STU-{random.randint(1001, 3800)}" for _ in range(n_rows_2)]
    c_2 = random.choices(courses, weights=[0.25, 0.20, 0.20, 0.15, 0.10, 0.10], k=n_rows_2)
    credits_2 = random.choices([3, 4, 2], weights=[0.60, 0.30, 0.10], k=n_rows_2)

    scores_2 = [round(random.uniform(50.0, 98.0), 1) for _ in range(n_rows_2)]
    # Inject exam score = 105.0% (>100% violation)
    invalid_score_idx = random.sample(range(n_rows_2), 30)
    for idx in invalid_score_idx:
        scores_2[idx] = 105.0

    grades_2 = random.choices(["A", "A-", "B+", "B", "C", "F"], weights=[0.20, 0.15, 0.20, 0.20, 0.15, 0.10], k=n_rows_2)
    # 14.0% null letter grades (Regression)
    null_gr_idx = random.sample(range(n_rows_2), int(n_rows_2 * 0.14))
    for idx in null_gr_idx:
        grades_2[idx] = None

    statuses_2 = random.choices(["Enrolled", "Active", "Probation", "Withdrawn"], weights=[0.45, 0.25, 0.15, 0.15], k=n_rows_2)

    df_v2 = pd.DataFrame({
        "Enrollment_ID": e_ids_2,
        "Student_ID": s_ids_2,
        "Course_Code": c_2,
        "Credits_Earned": credits_2,
        "Exam_Score": scores_2,
        "Letter_Grade": grades_2,
        "Academic_Status": statuses_2
    })

    file_v1_path = UPLOADS_DIR / "course_enrollment_v1.csv"
    file_v2_path = UPLOADS_DIR / "course_enrollment_v2.csv"

    df_v1.to_csv(file_v1_path, index=False)
    df_v2.to_csv(file_v2_path, index=False)

    return str(file_v1_path), str(file_v2_path)


def generate_microservices_api_preset():
    """
    Generates V1 and V2 Cloud Microservices API & Uptime telemetry [IT & Software]:
    - V1: 4,200 API request logs, low latency (20-300ms), 99.8% uptime, valid 200/201 status codes, INFO/LOW alerts.
    - V2: 5,100 records with regressions: 65 duplicate Request IDs, SLA uptime drop to 82%,
          negative latency (-40ms), HTTP 502/504 error code spikes, CRITICAL alerts.
    """
    random.seed(44)
    np.random.seed(44)

    # --- VERSION 1 ---
    n_rows_1 = 4200
    req_ids_1 = [f"REQ-{str(i).zfill(7)}" for i in range(100001, 100001 + n_rows_1)]
    services = ["order-api", "auth-api", "catalog-service", "checkout-worker", "search-api"]
    svc_1 = random.choices(services, weights=[0.30, 0.25, 0.20, 0.15, 0.10], k=n_rows_1)
    latency_1 = [round(float(v), 1) for v in np.random.exponential(scale=95.0, size=n_rows_1) + 15.0]
    uptime_1 = [round(random.uniform(99.5, 100.0), 2) for _ in range(n_rows_1)]
    error_rates_1 = [round(random.uniform(0.01, 1.20), 2) for _ in range(n_rows_1)]
    http_codes_1 = random.choices([200, 201, 204], weights=[0.90, 0.07, 0.03], k=n_rows_1)
    severities_1 = random.choices(["INFO", "LOW"], weights=[0.80, 0.20], k=n_rows_1)
    statuses_1 = random.choices(["HEALTHY", "ACTIVE"], weights=[0.95, 0.05], k=n_rows_1)

    df_v1 = pd.DataFrame({
        "Request_ID": req_ids_1,
        "Service_Name": svc_1,
        "Response_Time_ms": latency_1,
        "Uptime_Pct": uptime_1,
        "Error_Rate_Pct": error_rates_1,
        "HTTP_Status": http_codes_1,
        "Severity": severities_1,
        "System_Status": statuses_1
    })

    # --- VERSION 2 ---
    n_rows_2 = 5100
    req_ids_2 = [f"REQ-{str(i).zfill(7)}" for i in range(100001, 100001 + n_rows_2)]
    # Duplicate Request IDs
    dup_sources = random.choices(range(400), k=65)
    dup_targets = random.sample(range(400, n_rows_2), 65)
    for s, t in zip(dup_sources, dup_targets):
        req_ids_2[t] = req_ids_2[s]

    svc_2 = random.choices(services, weights=[0.30, 0.25, 0.20, 0.15, 0.10], k=n_rows_2)
    latency_2 = [round(float(v), 1) for v in np.random.exponential(scale=310.0, size=n_rows_2) + 30.0]
    # Negative latency anomaly
    invalid_lat = random.sample(range(n_rows_2), 22)
    for idx in invalid_lat:
        latency_2[idx] = -40.0

    # 10% null response times
    null_lat = random.sample([i for i in range(n_rows_2) if i not in invalid_lat], int(n_rows_2 * 0.10))
    for idx in null_lat:
        latency_2[idx] = None

    uptime_2 = [round(random.uniform(82.0, 98.0), 2) for _ in range(n_rows_2)]
    error_rates_2 = [round(random.uniform(0.1, 15.0), 2) for _ in range(n_rows_2)]
    http_codes_2 = random.choices([200, 201, 502, 504], weights=[0.65, 0.05, 0.18, 0.12], k=n_rows_2)
    severities_2 = random.choices(["LOW", "MEDIUM", "HIGH", "CRITICAL"], weights=[0.35, 0.25, 0.25, 0.15], k=n_rows_2)
    statuses_2 = random.choices(["HEALTHY", "DEGRADED", "DOWN"], weights=[0.50, 0.35, 0.15], k=n_rows_2)

    df_v2 = pd.DataFrame({
        "Request_ID": req_ids_2,
        "Service_Name": svc_2,
        "Response_Time_ms": latency_2,
        "Uptime_Pct": uptime_2,
        "Error_Rate_Pct": error_rates_2,
        "HTTP_Status": http_codes_2,
        "Severity": severities_2,
        "System_Status": statuses_2
    })

    file_v1_path = UPLOADS_DIR / "microservices_api_v1.csv"
    file_v2_path = UPLOADS_DIR / "microservices_api_v2.csv"

    df_v1.to_csv(file_v1_path, index=False)
    df_v2.to_csv(file_v2_path, index=False)

    return str(file_v1_path), str(file_v2_path)

