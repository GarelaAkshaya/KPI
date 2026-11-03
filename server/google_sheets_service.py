import os
from pathlib import Path
from typing import Optional, List, Any

from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def get_google_sheets_service():
    credentials_file = os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE")
    spreadsheet_id = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")

    if not credentials_file or not spreadsheet_id:
        raise ValueError("Google Sheets environment variables are missing.")

    credentials_path = BASE_DIR / credentials_file

    if not credentials_path.is_file():
        raise FileNotFoundError("Google Sheets credentials file was not found.")

    credentials = Credentials.from_service_account_file(
        str(credentials_path),
        scopes=SCOPES,
    )

    service = build(
        "sheets",
        "v4",
        credentials=credentials,
        cache_discovery=False,
    )

    return service, spreadsheet_id


def get_feedback_sheet_name(service, spreadsheet_id: str) -> str:
    """Dynamically determine the sheet/tab name containing form responses."""
    try:
        meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheets = meta.get("sheets", [])
        if not sheets:
            return "Form responses 1"
        for s in sheets:
            title = s.get("properties", {}).get("title", "")
            if "response" in title.lower() or "form" in title.lower():
                return title
        return sheets[0].get("properties", {}).get("title", "Form responses 1")
    except Exception:
        return "Form responses 1"


def fetch_google_sheet_feedback_rows(sheet_range: Optional[str] = None) -> List[List[Any]]:
    """
    Fetch all available response rows dynamically from Google Sheets.
    Without fixed row or column boundaries.
    """
    service, spreadsheet_id = get_google_sheets_service()
    if not sheet_range:
        sheet_title = get_feedback_sheet_name(service, spreadsheet_id)
        sheet_range = f"'{sheet_title}'"

    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=sheet_range,
    ).execute()
    return result.get("values", [])
