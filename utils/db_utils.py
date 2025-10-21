import discord
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
import asyncio
from utils.export_sheets import export_to_sheets

from config import TIMEZONE, REQUIRED_WEEKLY_POINTS, GUILD_ID

class Database:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.users_file = os.path.join(data_dir, "users.json")
        self.reports_file = os.path.join(data_dir, "reports.json")
        self.privileged_file = os.path.join(data_dir, "privileged_immunity.json")
        self.week_summary_file = os.path.join(data_dir, "week_summary.json")
        self._ensure_files_exist()

    def _ensure_files_exist(self):
        os.makedirs(self.data_dir, exist_ok=True)
        
        if not os.path.exists(self.users_file):
            default_users = {}
            self._save_json(self.users_file, default_users)
            
        if not os.path.exists(self.reports_file):
            self._save_json(self.reports_file, {})

        if not os.path.exists(self.privileged_file):
            self._save_json(self.privileged_file, {"users": [], "roles": []})

        if not os.path.exists(self.week_summary_file):
            self._save_json(self.week_summary_file, {})

    def _load_json(self, file_path: str) -> dict:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    def _save_json(self, file_path: str, data: dict):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def _get_default_user_data(self) -> dict:
        return {
            "total_points": 0,
            "weekly_points": 0,
            "weekly_quest_points": 0,
            "join_date": datetime.now(timezone.utc).isoformat(),
            "has_weekly_immunity": True
        }

    def add_user(self, user_id: int):
        users = self._load_json(self.users_file)
        user_id = str(user_id)
        
        if user_id not in users:
            users[user_id] = self._get_default_user_data()
            self._save_json(self.users_file, users)
    
    def get_user(self, user_id: int) -> dict:
        users = self._load_json(self.users_file)
        user_id = str(user_id)

        if user_id not in users:
            self.add_user(user_id)

        return users[user_id]

    def get_join_date(self, user_id: int) -> Optional[datetime]:
        users = self._load_json(self.users_file)
        user_id = str(user_id)
        
        if user_id not in users:
            self.add_user(user_id)
            
        join_date_str = users[user_id].get("join_date")
        return datetime.fromisoformat(join_date_str) if join_date_str else None
    
    def set_join_date(self, user_id: int, date: datetime):
        users = self._load_json(self.users_file)
        user_id = str(user_id)
        
        if user_id not in users:
            self.add_user(user_id)
            
        users[user_id]["join_date"] = date.astimezone(timezone.utc).isoformat()
        self._save_json(self.users_file, users)
    
    def update_weekly_immunities(self):
        """Update immunity status based on roles and join dates"""
        users = self._load_json(self.users_file)
        
        # Get week start
        week_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        while week_start.weekday() != 0:  # 0 = Monday
            week_start -= timedelta(days=1)
        
        for user_id in users:
            join_date = datetime.fromisoformat(users[user_id]["join_date"])
            # Give immunity if joined this week
            users[user_id]["has_weekly_immunity"] = join_date >= week_start
            
        self._save_json(self.users_file, users)

    def has_weekly_immunity(self, user_id: int) -> bool:
        """Check if user has immunity for current week"""
        users = self._load_json(self.users_file)
        user_id = str(user_id)
        
        if user_id not in users:
            self.add_user(user_id)
            return True  # New users get immunity
            
        return users[user_id].get("has_weekly_immunity", False)

    def save_report(self, message_id: int, report_data: dict):
        reports = self._load_json(self.reports_file)
        reports[str(message_id)] = report_data
        self._save_json(self.reports_file, reports)

    def get_report(self, message_id: int) -> Optional[dict]:
        reports = self._load_json(self.reports_file)
        return reports.get(str(message_id))

    def add_points(self, user_id: int, points: float, is_family_quest: bool = False):
        users = self._load_json(self.users_file)
        user_id = str(user_id)
        
        if user_id not in users:
            users[user_id] = self._get_default_user_data()
        
        users[user_id]["total_points"] += points
        users[user_id]["weekly_points"] += points
        if is_family_quest:
            users[user_id]["weekly_quest_points"] += points
        
        self._save_json(self.users_file, users)

    def add_points_for_date(self, user_id: int, points: int, report_date: datetime, is_family_quest: bool = False):
        users = self._load_json(self.users_file)
        user_id = str(user_id)
        if user_id not in users:
            users[user_id] = self._get_default_user_data()

        data = users[user_id]

        now = datetime.now(TIMEZONE)
        current_week_start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        current_week_end = current_week_start + timedelta(days=7)

        # За замовчуванням додаємо в total_points (всі заслуги зберігаються)
        data["total_points"] += points

        # Якщо звіт належить до поточного тижня — оновлюємо тижневу статистику
        if current_week_start <= report_date < current_week_end:
            day_key = report_date.strftime("%a")
            if "this_week" not in data:
                data["this_week"] = {d: 0 for d in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]}

            data["weekly_points"] += points
            if is_family_quest:
                data["weekly_quest_points"] += points
                data["this_week"][day_key] += points
        else:
            # Якщо звіт старший — просто додаємо в total_points
            print(f"⚠️ Звіт за {report_date.date()} належить до минулого тижня — додано лише до total_points.")

        self._save_json(self.users_file, users)

    def reset_weekly_stats(self):
        """Reset weekly points for all users"""
        users = self._load_json(self.users_file)
        
        for user_id in users:
            users[user_id]["weekly_points"] = 0
            users[user_id]["weekly_quest_points"] = 0
            
        self._save_json(self.users_file, users)
        self.update_weekly_immunities()

    def remove_report(self, message_id: int):
        reports = self._load_json(self.reports_file)
        if str(message_id) in reports:
            del reports[str(message_id)]
            self._save_json(self.reports_file, reports)

    def has_quota_immunity(self, user_id: int, member: discord.Member = None) -> bool:
        """
        Перевіряє, чи користувач має імунітет від щотижневої квоти.
        Імунітет є, якщо:
        - користувач новачок (has_weekly_immunity)
        - користувач у списку привілейованих
        - користувач має роль з привілейованим імунітетом
        """
        users = self._load_json(self.users_file)
        privileged = self._load_json(self.privileged_file)
        user_id_str = str(user_id)

        # Новачок
        if user_id_str not in users:
            self.add_user(user_id)
            return True

        # Новачок із першого тижня
        if users[user_id_str].get("has_weekly_immunity", False):
            return True

        # Привілейовані користувачі
        if user_id_str in privileged.get("users", []):
            return True

        # Привілейовані ролі
        if member:
            member_role_ids = [r.id for r in member.roles]
            if any(rid in privileged.get("roles", []) for rid in member_role_ids):
                return True

        return False
    
    def has_privileged_immunity(self, user_id: int, member: Optional[discord.Member] = None) -> bool:
        """Перевіряє, чи користувач має привілейований імунітет (роль або індивідуальний список)."""
        privileged = self._load_json(self.privileged_file)

        # Індивідуальний імунітет
        if str(user_id) in privileged.get("users", []):
            return True

        # Імунітет за роллю
        if member:
            member_role_ids = [role.id for role in member.roles]
            if any(rid in privileged.get("roles", []) for rid in member_role_ids):
                return True

        return False

    def finalize_weekly_stats(self, guild: discord.Guild):
        """Підбиття підсумків тижня — незалежно від Discord, з урахуванням імунітетів"""
        users = self._load_json(self.users_file)
        
        rewards_data = {
            "week_start": (datetime.now(TIMEZONE) - timedelta(days=datetime.now(TIMEZONE).weekday())).strftime("%d.%m.%Y"),
            "top_players": [],
            "non_quota_users": [],
            "week_table": []
        }

        days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

        # Підготовка топу по квестах (всі користувачі, імунітет не виключає премії)
        top_candidates = [(uid, data["weekly_quest_points"]) for uid, data in users.items() if data["weekly_quest_points"] > 0]
        top_candidates.sort(key=lambda x: x[1], reverse=True)

        top_players = []
        current_place = 1
        last_points = None
        same_place_count = 0  # скільки людей поділяють місце

        for idx, (uid, points) in enumerate(top_candidates):
            # якщо це новий результат — підвищуємо місце з урахуванням попередніх груп
            if last_points is not None and points != last_points:
                current_place += same_place_count
                same_place_count = 0

            # додаємо гравця
            top_players.append({"user_id": int(uid), "points": points, "place": current_place})

            # оновлюємо лічильники
            last_points = points
            same_place_count += 1

            # обмеження: тільки топ-3 (але враховуємо нічиї)
            if current_place > 3:
                break

        rewards_data["top_players"] = top_players

        # Користувачі, що не виконали квоту (ігнор імунітету)
        non_quota_users = []
        for uid, data in users.items():
            member = guild.get_member(int(uid))
            if member and not self.has_quota_immunity(int(uid), member) and data["weekly_points"] < REQUIRED_WEEKLY_POINTS:
                non_quota_users.append({"user_id": int(uid), "points": data["weekly_points"]})

        rewards_data["non_quota_users"] = non_quota_users

        # Формування таблиці минулого тижня
        week_table = []

        # Дати днів минулого тижня
        # today = datetime.now(TIMEZONE)
        # start_of_week = today - timedelta(days=today.weekday())
        # week_dates = [(start_of_week + timedelta(days=i)).strftime("%d.%m") for i in range(7)]

        today = datetime.now(TIMEZONE)
        start_last_week = today - timedelta(days=today.weekday() + 7)  # понеділок минулого тижня
        week_dates = [(start_last_week + timedelta(days=i)).strftime("%d.%m") for i in range(7)]

        for uid, data in users.items():
            member = guild.get_member(int(uid))
            if not member:
                continue  # виключаємо тих, кого нема на сервері

            # # Визначаємо, чи користувач має привілейований імунітет
            # privileged_immunity = self.has_privileged_immunity(int(uid), member)  # тут треба реалізувати або мати метод
            # is_newbie = data.get("has_weekly_immunity", False)

            # if privileged_immunity and not is_newbie:
            #     continue  # виключаємо привілейованих, залишаємо тільки новачків з has_weekly_immunity

            is_has_quest_points = data.get("weekly_quest_points", 0) > 0
            if not is_has_quest_points:
                continue  # виключаємо тих, хто не має балів за квести

            # last_week містить ключі "Mon","Tue",... → перетворюємо у дати
            last_week = data.get("this_week", {d:0 for d in ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]})
            days_dict = {week_dates[i]: last_week.get(day, 0) for i, day in enumerate(["Mon","Tue","Wed","Thu","Fri","Sat","Sun"])}
            # total = sum(days_dict.values())
            total = data.get("weekly_quest_points", 0)

            week_table.append({
                "user_id": int(uid),
                "days": days_dict,
                "total": total
            })

        rewards_data["week_table"] = week_table

        # Переносимо this_week → last_week і обнуляємо this_week
        for uid, data in users.items():
            data["last_week"] = data.get("this_week", {d: 0 for d in ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]})
            data["this_week"] = {d: 0 for d in ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]}
            data["weekly_points"] = 0
            data["weekly_quest_points"] = 0

        # Збереження
        self._save_json(self.users_file, users)
        self._save_json(self.week_summary_file, rewards_data)

        # Експорт у Google Sheets
        asyncio.create_task(export_to_sheets(guild))

        return rewards_data, users