import urllib.request
import json

BASE_URL = "http://127.0.0.1:5000"

def test_api():
    # 1. Login to get token
    login_req = urllib.request.Request(
        f"{BASE_URL}/api/auth/login",
        data=json.dumps({"username": "admin", "password": "admin1234"}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(login_req) as resp:
        login_data = json.loads(resp.read().decode("utf-8"))
        token = login_data["access_token"]
        assert token, "Login failed to return access_token"
        print("[PASS] Login successful, token obtained")

    headers = {"Authorization": f"Bearer {token}"}

    # 2. Test /api/filters/sections
    req = urllib.request.Request(f"{BASE_URL}/api/filters/sections?academic_year=2024-2025", headers=headers)
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        sections = json.loads(resp.read().decode("utf-8"))
        assert isinstance(sections, list)
        print(f"[PASS] /api/filters/sections returned {len(sections)} sections")

    # 3. Test /api/kpis/student-faculty-ratio (institutional scope without department filter)
    req = urllib.request.Request(f"{BASE_URL}/api/kpis/student-faculty-ratio?academic_year=2024-2025", headers=headers)
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert "ratio" in data
        assert "totalStudents" in data
        assert "totalFaculty" in data
        print(f"[PASS] /api/kpis/student-faculty-ratio (no dept filter): ratio={data['ratio']}, students={data['totalStudents']}, faculty={data['totalFaculty']}")

    # 4. Test /api/kpis/pass-percentage (institutional scope)
    req = urllib.request.Request(f"{BASE_URL}/api/kpis/pass-percentage?academic_year=2024-2025", headers=headers)
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert "overall_pass_percentage" in data
        print(f"[PASS] /api/kpis/pass-percentage: pass_pct={data['overall_pass_percentage']}%")

    # 5. Test /api/attendance
    req = urllib.request.Request(f"{BASE_URL}/api/attendance?academic_year=2024-2025", headers=headers)
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert isinstance(data, list)
        print(f"[PASS] /api/attendance returned {len(data)} attendance records")

    # 6. Test /api/lab-utilization
    req = urllib.request.Request(f"{BASE_URL}/api/lab-utilization?academic_year=2024-2025", headers=headers)
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert isinstance(data, list)
        print(f"[PASS] /api/lab-utilization returned {len(data)} lab records")

    # 7. Test /api/feedback/summary
    req = urllib.request.Request(f"{BASE_URL}/api/feedback/summary?academic_year=2024-2025", headers=headers)
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert "total_responses" in data
        print(f"[PASS] /api/feedback/summary returned total_responses={data['total_responses']}")

    # 8. Test /api/departments/overview (Preserved)
    req = urllib.request.Request(f"{BASE_URL}/api/departments/overview", headers=headers)
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert isinstance(data, list)
        assert len(data) >= 2
        print(f"[PASS] /api/departments/overview returned {len(data)} departments (Preserved)")

    print("\nALL LIVE API ENDPOINT TESTS PASSED!")

if __name__ == "__main__":
    test_api()
