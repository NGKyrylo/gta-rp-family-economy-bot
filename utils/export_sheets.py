import json
import os
import gspread
# from oauth2client.service_account import ServiceAccountCredentials  # removed
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import discord
from config import SPREADSHEET_ID, TIMEZONE
import asyncio
import logging

WEEK_SUMMARY_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "week_summary.json")
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "..", "google_api.json")

QUESTS_SHEET = "Квести"
TOP_SHEET = "Топ тижня"

logger = logging.getLogger(__name__)

async def export_to_sheets(guild: discord.Guild):
    try:
        # load week data (fast file I/O; ok in event loop for small files)
        with open(WEEK_SUMMARY_FILE, "r", encoding="utf-8") as f:
            week_data = json.load(f)
    except Exception as e:
        logger.exception("Failed to load week summary file")
        return

    # Збираємо потрібні display_name у event loop (без запитів API)
    user_ids = set()
    for ud in week_data.get("week_table", []):
        user_ids.add(ud.get("user_id"))
    for p in week_data.get("top_players", []):
        user_ids.add(p.get("user_id"))

    name_map = {}
    for uid in user_ids:
        if uid is None:
            continue
        member = guild.get_member(uid)
        name_map[uid] = member.display_name if member else f"ID:{uid}"

    # Весь гугл-інтеракт виконуємо в окремому потоці, щоб не блокувати event loop
    def _sync_export(week_data, name_map):
        try:
            # авторизація gspread через service_account (сучасний підхід)
            scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            client = gspread.service_account(filename=CREDENTIALS_FILE, scopes=scope)

            sheet = client.open_by_key(SPREADSHEET_ID)

            # ===== Квести =====
            quests_ws = sheet.worksheet(QUESTS_SHEET)

            all_values = quests_ws.get_all_values()
            if len(all_values) > 1:
                # delete_rows expects row index; for великих таблиць це може бути повільно,
                # але поки видаляємо діапазон рядків через API
                quests_ws.delete_rows(2, len(all_values))

            if week_data.get("week_table"):
                dates = list(week_data["week_table"][0]["days"].keys())
                quests_ws.update("C1", [dates])

                rows = []
                for user_data in week_data["week_table"]:
                    uid = user_data.get("user_id")
                    name = name_map.get(uid, f"ID:{uid}")
                    if sum(user_data["days"].values()) == 0:
                        continue
                    day_points = [d if d != 0 else "" for d in user_data["days"].values()]
                    total = user_data.get("total", 0)
                    row = [name] + day_points + [total]
                    rows.append(row)

                if rows:
                    quests_ws.update(f"B2", rows)
                    num_rows = len(rows)
                    for col_letter in "CDEFGHIJ":
                        range_str = f"{col_letter}2:{col_letter}{num_rows+1}"
                        if col_letter == "J":
                            quests_ws.format(range_str, {
                                "horizontalAlignment": "CENTER",
                                "backgroundColor": {"red": 0.8, "green": 0.8, "blue": 0.8}
                            })
                        else:
                            quests_ws.format(range_str, {
                                "horizontalAlignment": "CENTER",
                                "backgroundColor": {"red": 0.6, "green": 0.6, "blue": 0.6}
                            })
            else:
                today = datetime.now(TIMEZONE)
                start_last_week = today - timedelta(days=today.weekday() + 7)
                week_dates = [(start_last_week + timedelta(days=i)).strftime("%d.%m") for i in range(7)]
                quests_ws.update("C1:I1", [week_dates])

            # ===== Топ тижня =====
            top_ws = sheet.worksheet(TOP_SHEET)
            places_dict = {1: [], 2: [], 3: []}
            for place in week_data.get("top_players", []):
                uid = place.get("user_id")
                name = name_map.get(uid, f"ID:{uid}")
                place_num = place.get("place", 0)
                if place_num in places_dict:
                    places_dict[place_num].append(name)

            for place_num in range(1, 4):
                names = ", ".join(places_dict[place_num])
                top_ws.update(f"C{2 + place_num}", [[names]])

            # Автоширина через google sheets API (service account credentials)
            service_creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=["https://www.googleapis.com/auth/spreadsheets"])
            service = build('sheets', 'v4', credentials=service_creds)

            quests_sheet_id = quests_ws._properties['sheetId']
            top_sheet_id = top_ws._properties['sheetId']

            requests = [
                {
                    "autoResizeDimensions": {
                        "dimensions": {
                            "sheetId": quests_sheet_id,
                            "dimension": "COLUMNS",
                            "startIndex": 1,
                            "endIndex": 2
                        }
                    }
                },
                {
                    "autoResizeDimensions": {
                        "dimensions": {
                            "sheetId": top_sheet_id,
                            "dimension": "COLUMNS",
                            "startIndex": 2,
                            "endIndex": 3
                        }
                    }
                }
            ]
            body = {"requests": requests}
            service.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()
            return True
        except Exception:
            logger.exception("Failed to export to Google Sheets (sync part)")
            return False

    ok = await asyncio.to_thread(_sync_export, week_data, name_map)
    if ok:
        logger.info("✅ Дані успішно експортовано до Google Sheets")
    else:
        logger.error("Експорт до Google Sheets завершився з помилкою")
