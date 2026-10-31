import sys
import os
import json
import csv
from datetime import datetime
import hashlib
from sqlalchemy import text

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import database

def create_backup():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backup", f"student_data_backup_{timestamp}")
    os.makedirs(backup_dir, exist_ok=True)

    print("=" * 60)
    print("BACKING UP AFFECTED STUDENT DATA FROM SUPABASE")
    print(f"Target Database Host: {database.engine.url.host}")
    print(f"Backup Directory: {backup_dir}")
    print("=" * 60)

    manifest = {
        "timestamp": timestamp,
        "database_host": database.engine.url.host,
        "database_name": database.engine.url.database,
        "tables": {}
    }

    tables_to_backup = [
        ("student_uploads", 'SELECT * FROM "student_uploads" WHERE academic_year IN (\'2024-2025\', \'2025-2026\') ORDER BY "id"'),
        ("student_attendance", 'SELECT * FROM "student_attendance" WHERE academic_year IN (\'2024-2025\', \'2025-2026\') ORDER BY "id"'),
        ("student_feedback", 'SELECT * FROM "student_feedback" WHERE academic_year IN (\'2024-2025\', \'2025-2026\') ORDER BY "id"'),
    ]

    with database.engine.connect() as conn:
        for tbl_name, query_sql in tables_to_backup:
            result = conn.execute(text(query_sql))
            col_names = list(result.keys())
            rows = result.fetchall()
            
            # Convert rows to dicts for JSON serialization
            data = [dict(zip(col_names, row)) for row in rows]

            # Format datetimes / dates for JSON
            for r in data:
                for k, v in r.items():
                    if isinstance(v, (datetime,)):
                        r[k] = v.isoformat()

            # 1. Save JSON
            json_filename = f"{tbl_name}_{timestamp}.json"
            json_path = os.path.join(backup_dir, json_filename)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Compute sha256
            with open(json_path, "rb") as f:
                sha256 = hashlib.sha256(f.read()).hexdigest()

            # 2. Save CSV
            csv_filename = f"{tbl_name}_{timestamp}.csv"
            csv_path = os.path.join(backup_dir, csv_filename)
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                if data:
                    writer = csv.DictWriter(f, fieldnames=col_names)
                    writer.writeheader()
                    writer.writerows(data)
                else:
                    writer = csv.writer(f)
                    writer.writerow(col_names)

            manifest["tables"][tbl_name] = {
                "count": len(data),
                "json_file": json_filename,
                "csv_file": csv_filename,
                "sha256": sha256,
            }
            print(f"  [BACKED UP] {tbl_name}: {len(data)} records -> {json_filename} & {csv_filename}")

    # Write manifest
    manifest_path = os.path.join(backup_dir, f"manifest_{timestamp}.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"\n[SUCCESS] Backup completed successfully in {backup_dir}")
    print(f"Manifest written to: {manifest_path}")
    return backup_dir, manifest

if __name__ == "__main__":
    create_backup()

