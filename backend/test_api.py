import time
import json
import urllib.request
import urllib.error
import subprocess
import sys
import uuid
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PYTHON_EXE = BASE_DIR / "venv" / "Scripts" / "python.exe"

def make_request(url, method="GET", data=None):
    headers = {"Content-Type": "application/json"}
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            status = resp.status
            res_body = json.loads(resp.read().decode("utf-8"))
            return status, res_body
    except urllib.error.HTTPError as e:
        res_body = json.loads(e.read().decode("utf-8"))
        return e.code, res_body

def upload_file_multipart(url, filename, content_bytes, user_email):
    boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
    body = bytearray()

    # File field
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode())
    body.extend(b'Content-Type: text/csv\r\n\r\n')
    body.extend(content_bytes)
    body.extend(b'\r\n')

    # user_email field
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(b'Content-Disposition: form-data; name="user_email"\r\n\r\n')
    body.extend(user_email.encode())
    body.extend(b'\r\n')

    body.extend(f"--{boundary}--\r\n".encode())

    req = urllib.request.Request(
        url,
        data=bytes(body),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))

def run_tests():
    print("Testing server endpoints against running server or fresh instance...")
    
    # Check if server is already running
    server_running = False
    try:
        status, _ = make_request("http://127.0.0.1:8000/api-status")
        if status == 200:
            server_running = True
    except Exception:
        server_running = False

    proc = None
    if not server_running:
        print("Starting FastAPI server process...")
        proc = subprocess.Popen(
            [str(PYTHON_EXE), "-m", "uvicorn", "main:app", "--port", "8000", "--host", "127.0.0.1"],
            cwd=str(BASE_DIR)
        )
        # Wait up to 20 seconds for server startup
        for attempt in range(20):
            time.sleep(1)
            try:
                status, _ = make_request("http://127.0.0.1:8000/api-status")
                if status == 200:
                    print(f"   Server ready after {attempt + 1}s.")
                    break
            except Exception:
                pass

    try:
        print("1. Testing GET /api-status...")
        status, body = make_request("http://127.0.0.1:8000/api-status")
        assert status == 200
        print("   Status OK:", body)

        # Test Registration
        test_email = f"user_{int(time.time())}@example.com"
        print("2. Testing POST /register...")
        status, reg_res = make_request("http://127.0.0.1:8000/register", method="POST", data={
            "name": "Dashboard Tester",
            "email": test_email,
            "password": "Password123!"
        })
        assert status == 200
        assert "access_token" in reg_res
        print("   Register OK:", reg_res["message"])

        # Test that an invalid Google credential is rejected
        print("3. Testing POST /auth/google rejects invalid credentials...")
        g_status, g_res = make_request("http://127.0.0.1:8000/auth/google", method="POST", data={
            "credential": "not-a-google-id-token"
        })
        assert g_status in (401, 503)
        assert "access_token" not in g_res
        print("   Invalid Google credential rejected:", g_res)

        # Test CSV Upload
        print("4. Testing POST /upload-csv...")
        csv_content_a = b"id,account_name,balance,revenue,status\n101,Account A,5000,12000,Active\n102,Account B,8500,25000,Active\n103,Account C,3100,8000,Pending\n"
        csv_content_b = b"id,account_name,balance,revenue,region\n101,Account A,5500,12000,US\n102,Account B,8500,27000,EU\n104,Account D,4000,15000,APAC\n"
        
        u_status_a, u_res_a = upload_file_multipart(
            "http://127.0.0.1:8000/upload-csv",
            "baseline_period.csv",
            csv_content_a,
            test_email
        )
        assert u_status_a == 200
        assert u_res_a["file"]["row_count"] == 3
        file_id_a = u_res_a["file"]["id"]
        print("   Upload Baseline CSV OK:", u_res_a["file"])

        u_status_b, u_res_b = upload_file_multipart(
            "http://127.0.0.1:8000/upload-csv",
            "target_period.csv",
            csv_content_b,
            test_email
        )
        assert u_status_b == 200
        assert u_res_b["file"]["row_count"] == 3
        file_id_b = u_res_b["file"]["id"]
        print("   Upload Target CSV OK:", u_res_b["file"])

        # Test CSV History
        print("5. Testing GET /history...")
        h_status, h_res = make_request(f"http://127.0.0.1:8000/history?user_email={test_email}")
        assert h_status == 200
        assert h_res["count"] >= 2
        print("   History OK: Total files =", h_res["count"])

        # Test CSV Comparison Endpoint via IDs
        print("6. Testing POST /compare-csv-ids...")
        c_status, c_res = make_request("http://127.0.0.1:8000/compare-csv-ids", method="POST", data={
            "file_id_a": file_id_a,
            "file_id_b": file_id_b,
            "key_column": "id"
        })
        assert c_status == 200
        assert c_res["success"] is True
        data = c_res["data"]
        assert data["summary"]["rows_a"] == 3
        assert data["summary"]["rows_b"] == 3
        assert data["schema_drift"]["has_drift"] is True
        assert "status" in data["schema_drift"]["columns_only_in_a"]
        assert "region" in data["schema_drift"]["columns_only_in_b"]

        # Verify Financial Metrics profiling & median fields
        fin_metrics = data["financial_metrics"]
        assert len(fin_metrics) > 0
        balance_metric = next(f for f in fin_metrics if f["column"] == "balance")
        assert "median_a" in balance_metric
        assert "median_b" in balance_metric
        assert "median_delta" in balance_metric
        assert "zero_count_delta" in balance_metric
        assert "negative_count_delta" in balance_metric
        print("   Financial Metrics profiling OK: Balance Sum Delta =", balance_metric["sum_delta"], "Median Delta =", balance_metric["median_delta"])

        # Test Sample Dataset Presets Endpoint
        print("7. Testing POST /api/sample-datasets/bank-transactions...")
        p_status_1, p_res_1 = make_request("http://127.0.0.1:8000/api/sample-datasets/bank-transactions", method="POST")
        assert p_status_1 == 200
        assert p_res_1["success"] is True
        b_data = p_res_1["data"]
        assert b_data["summary"]["rows_a"] == 10000
        assert b_data["summary"]["rows_b"] == 12000
        assert b_data["classification"]["overall_status"] == "REGRESSION"
        print("   Bank Transactions Preset OK: Status =", b_data["classification"]["overall_status"])

        print("8. Testing POST /api/sample-datasets/loan-portfolio...")
        p_status_2, p_res_2 = make_request("http://127.0.0.1:8000/api/sample-datasets/loan-portfolio", method="POST")
        assert p_status_2 == 200
        assert p_res_2["success"] is True
        l_data = p_res_2["data"]
        assert l_data["summary"]["rows_a"] == 5000
        assert l_data["summary"]["rows_b"] == 5500
        assert len(l_data["validation_b"]["row_violations"]) > 0
        print("   Loan Portfolio Preset OK: Row Violations Flagged =", len(l_data["validation_b"]["row_violations"]))

        # Test Academics Domain Rules & Preset
        print("9. Testing GET /api/rules?domain=academics...")
        r_status_acad, r_res_acad = make_request("http://127.0.0.1:8000/api/rules?domain=academics")
        assert r_status_acad == 200
        assert r_res_acad["success"] is True
        assert r_res_acad["count"] >= 8
        assert any(r["id"] == "gpa_valid_range" for r in r_res_acad["rules"])
        # Test Clinical Vitals Preset (Healthcare #2)
        print("9b. Testing POST /api/sample-datasets/clinical-vitals...")
        p_status_cv, p_res_cv = make_request("http://127.0.0.1:8000/api/sample-datasets/clinical-vitals", method="POST")
        assert p_status_cv == 200
        assert p_res_cv["success"] is True
        cv_data = p_res_cv["data"]
        assert cv_data["domain"] == "healthcare"
        assert cv_data["summary"]["rows_a"] == 4500
        assert cv_data["summary"]["rows_b"] == 5200
        print("   Clinical Vitals Preset OK: Status =", cv_data["classification"]["overall_status"])

        # Test Academics Domain Rules & Presets
        print("10. Testing GET /api/rules?domain=academics...")
        r_status_acad, r_res_acad = make_request("http://127.0.0.1:8000/api/rules?domain=academics")
        assert r_status_acad == 200
        assert r_res_acad["success"] is True
        assert r_res_acad["count"] >= 8
        assert any(r["id"] == "gpa_valid_range" for r in r_res_acad["rules"])
        print("   Academics Rules OK: Total Rules =", r_res_acad["count"])

        print("11. Testing POST /api/sample-datasets/student-academics...")
        p_status_acad, p_res_acad = make_request("http://127.0.0.1:8000/api/sample-datasets/student-academics", method="POST")
        assert p_status_acad == 200
        assert p_res_acad["success"] is True
        acad_data = p_res_acad["data"]
        assert acad_data["domain"] == "academics"
        assert acad_data["summary"]["rows_a"] == 5000
        assert acad_data["summary"]["rows_b"] == 6000
        print("   Student Academics Preset OK: Domain =", acad_data["domain"], "Status =", acad_data["classification"]["overall_status"])

        print("12. Testing POST /api/sample-datasets/course-enrollment...")
        p_status_ce, p_res_ce = make_request("http://127.0.0.1:8000/api/sample-datasets/course-enrollment", method="POST")
        assert p_status_ce == 200
        assert p_res_ce["success"] is True
        ce_data = p_res_ce["data"]
        assert ce_data["domain"] == "academics"
        assert ce_data["summary"]["rows_a"] == 4000
        assert ce_data["summary"]["rows_b"] == 4800
        print("   Course Enrollment Preset OK: Domain =", ce_data["domain"], "Status =", ce_data["classification"]["overall_status"])

        # Test IT & Software Systems Domain Rules & Presets
        print("13. Testing GET /api/rules?domain=software_systems...")
        r_status_soft, r_res_soft = make_request("http://127.0.0.1:8000/api/rules?domain=software_systems")
        assert r_status_soft == 200
        assert r_res_soft["success"] is True
        assert r_res_soft["count"] >= 8
        assert any(r["id"] == "resource_utilization_range" for r in r_res_soft["rules"])
        print("   IT & Software Systems Rules OK: Total Rules =", r_res_soft["count"])

        print("14. Testing POST /api/sample-datasets/software-systems...")
        p_status_soft, p_res_soft = make_request("http://127.0.0.1:8000/api/sample-datasets/software-systems", method="POST")
        assert p_status_soft == 200
        assert p_res_soft["success"] is True
        soft_data = p_res_soft["data"]
        assert soft_data["domain"] == "software_systems"
        assert soft_data["summary"]["rows_a"] == 5000
        assert soft_data["summary"]["rows_b"] == 6200
        print("   Software Systems Preset OK: Domain =", soft_data["domain"], "Status =", soft_data["classification"]["overall_status"])

        print("15. Testing POST /api/sample-datasets/microservices-api...")
        p_status_ms, p_res_ms = make_request("http://127.0.0.1:8000/api/sample-datasets/microservices-api", method="POST")
        assert p_status_ms == 200
        assert p_res_ms["success"] is True
        ms_data = p_res_ms["data"]
        assert ms_data["domain"] == "software_systems"
        assert ms_data["summary"]["rows_a"] == 4200
        assert ms_data["summary"]["rows_b"] == 5100
        print("   Microservices API Preset OK: Domain =", ms_data["domain"], "Status =", ms_data["classification"]["overall_status"])

        # =========================================================
        # NEW WORKBENCH, VISUAL EXPLORER & DISCOVERY TESTS
        # =========================================================

        print("16. Testing GET /api/datasets...")
        ds_status, ds_res = make_request(f"http://127.0.0.1:8000/api/datasets?user_email={test_email}")
        assert ds_status == 200
        assert ds_res["success"] is True
        assert ds_res["count"] >= 2
        print(f"   Datasets listing OK: Total = {ds_res['count']}")

        print("17. Testing GET /api/datasets/{file_id_a}/schema...")
        sch_status, sch_res = make_request(f"http://127.0.0.1:8000/api/datasets/{file_id_a}/schema")
        assert sch_status == 200
        assert sch_res["success"] is True
        assert len(sch_res["schema"]["columns"]) >= 4
        print(f"   Schema extraction OK: Columns = {[c['name'] for c in sch_res['schema']['columns']]}")

        print("18. Testing POST /api/query/execute (Analytical SELECT & Aggregation)...")
        q_status, q_res = make_request("http://127.0.0.1:8000/api/query/execute", method="POST", data={
            "query": "SELECT status, COUNT(*) AS count, ROUND(AVG(balance), 2) AS avg_balance FROM dataset GROUP BY status ORDER BY count DESC",
            "dataset_id": file_id_a,
            "page": 1,
            "page_size": 10
        })
        assert q_status == 200
        assert q_res["success"] is True
        assert q_res["total_rows"] >= 1
        assert "execution_time_ms" in q_res
        print(f"   Analytical SQL OK: {len(q_res['rows'])} aggregated rows in {q_res['execution_time_ms']}ms")

        print("19. Testing POST /api/query/execute (Security Policy Rejection of Destructive SQL)...")
        bad_status, bad_res = make_request("http://127.0.0.1:8000/api/query/execute", method="POST", data={
            "query": "DROP TABLE csv_files; DELETE FROM users;",
            "dataset_id": file_id_a
        })
        assert bad_status == 400
        print("   Security policy successfully rejected destructive query:", bad_res["detail"])

        print("20. Testing POST /api/query/generate (Natural-Language-to-SQL)...")
        nl_status, nl_res = make_request("http://127.0.0.1:8000/api/query/generate", method="POST", data={
            "prompt": "Show categories with highest average balance",
            "dataset_id": file_id_a,
            "domain": "finance"
        })
        assert nl_status == 200
        assert nl_res["success"] is True
        assert "sql" in nl_res["data"]
        print(f"   NL-to-SQL OK: Proposed SQL = {nl_res['data']['sql']}")

        print("21. Testing POST /api/query/explain (Verified Query Explanation)...")
        exp_status, exp_res = make_request("http://127.0.0.1:8000/api/query/explain", method="POST", data={
            "query": "SELECT status, COUNT(*) FROM dataset GROUP BY status",
            "columns": ["status", "count"],
            "rows": [["Active", 2], ["Pending", 1]],
            "total_rows": 2,
            "execution_time_ms": 1.25,
            "domain": "finance"
        })
        assert exp_status == 200
        assert exp_res["success"] is True
        print(f"   Query Explanation OK: {exp_res['explanation']['summary'][:80]}...")

        print("22. Testing POST /api/queries/save & GET /api/queries...")
        save_status, save_res = make_request("http://127.0.0.1:8000/api/queries/save", method="POST", data={
            "user_email": test_email,
            "query_name": "Active Account Balances",
            "query_sql": "SELECT * FROM dataset WHERE balance > 4000",
            "dataset_id": file_id_a,
            "domain": "finance"
        })
        assert save_status == 200
        saved_q_id = save_res["query"]["id"]

        list_q_status, list_q_res = make_request(f"http://127.0.0.1:8000/api/queries?user_email={test_email}")
        assert list_q_status == 200
        assert any(q["id"] == saved_q_id for q in list_q_res["queries"])
        print(f"   Saved Query OK: ID {saved_q_id}")

        print("23. Testing POST /api/queries/{id}/rerun (Lineage Tracking)...")
        rerun_status, rerun_res = make_request(f"http://127.0.0.1:8000/api/queries/{saved_q_id}/rerun", method="POST", data={
            "user_email": test_email,
            "target_dataset_id": file_id_b
        })
        assert rerun_status == 200
        assert rerun_res["success"] is True
        assert "lineage" in rerun_res
        print(f"   Query Rerun & Lineage OK: Row delta = {rerun_res['lineage']['row_delta_vs_previous']}")

        print("24. Testing GET /api/external-sources/search & POST /api/external-sources/import...")
        src_status, src_res = make_request("http://127.0.0.1:8000/api/external-sources/search?domain=finance")
        assert src_status == 200
        assert src_res["count"] >= 1

        target_ext_id = src_res["results"][0]["id"]
        imp_status, imp_res = make_request("http://127.0.0.1:8000/api/external-sources/import", method="POST", data={
            "dataset_id": target_ext_id,
            "user_email": test_email
        })
        assert imp_status == 200
        assert imp_res["success"] is True
        print(f"   External Ingestion OK: Imported '{imp_res['dataset']['name']}' ({imp_res['dataset']['row_count']} rows)")

        print("\n>>> ALL 24 SYSTEM INTEGRATION TESTS (PRESETS, SQL WORKBENCH, GEMINI NL, LINEAGE, DISCOVERY) PASSED! <<<\n")


    finally:
        if proc:
            proc.terminate()
            proc.wait()

if __name__ == "__main__":
    run_tests()

