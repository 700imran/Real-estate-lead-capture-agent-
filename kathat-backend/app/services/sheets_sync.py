"""
Optional Google Sheets mirror. This is NOT the database — SQLite is the
system of record (see database.py). This just appends a row to a Sheet
whenever a lead turns warm or hot, for anyone on the team who'd rather
glance at a spreadsheet than log into the dashboard.

Setup (skip entirely if you don't want this):
  1. Create a Google Cloud service account, enable the Sheets API.
  2. Download its JSON key, set GOOGLE_SERVICE_ACCOUNT_JSON to that file's path.
  3. Create a Google Sheet, share it with the service account's email
     (found in the JSON key as "client_email") as an Editor.
  4. Set GOOGLE_SHEET_ID to the sheet's ID (from its URL).

If either env var is missing, this silently no-ops — nothing else in the
app depends on it.
"""
from ..config import settings

_client = None
_client_load_attempted = False


def _get_worksheet():
    global _client, _client_load_attempted
    if not (settings.google_service_account_json and settings.google_sheet_id):
        return None
    if _client is None and not _client_load_attempted:
        _client_load_attempted = True
        try:
            import gspread
            _client = gspread.service_account(filename=settings.google_service_account_json)
        except Exception as e:
            print(f"Google Sheets client init failed (check credentials path/format): {e}")
            return None
    if _client is None:
        return None
    try:
        sheet = _client.open_by_key(settings.google_sheet_id)
        return sheet.sheet1
    except Exception as e:
        print(f"Google Sheets open failed (check sheet ID + sharing permissions): {e}")
        return None


async def append_lead_row(lead: dict) -> None:
    worksheet = _get_worksheet()
    if not worksheet:
        return
    try:
        worksheet.append_row([
            lead.get("id", ""),
            lead.get("name") or "",
            lead.get("email") or "",
            lead.get("phone") or "",
            lead.get("score", 0),
            lead.get("temperature", ""),
            lead.get("source_page") or "",
        ])
    except Exception as e:
        print(f"Google Sheets append failed: {e}")
