import sqlite3
from datetime import datetime

DB_NAME = "bot_data.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
        cursor.execute("CREATE TABLE IF NOT EXISTS birthdays (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, name TEXT, birth_date TEXT)")
        conn.commit()

def add_user(user_id: int):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()

def add_birthday(user_id: int, name: str, date_str: str):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO birthdays (user_id, name, birth_date) VALUES (?, ?, ?)", (user_id, name, date_str))
        conn.commit()

def get_all_birthdays(user_id: int):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, birth_date FROM birthdays WHERE user_id = ?", (user_id,))
        return cursor.fetchall()

def get_all_users():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        return [row[0] for row in cursor.fetchall()]

def get_birthdays_by_days_left(days_left: int):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, name, birth_date FROM birthdays")
        all_bdays = cursor.fetchall()
    
    matched = []
    today = datetime.now().date()
    for u_id, name, b_date_str in all_bdays:
        try:
            b_date = datetime.strptime(b_date_str, "%d.%m.%Y").date().replace(year=today.year)
            if b_date < today: b_date = b_date.replace(year=today.year + 1)
            if (b_date - today).days == days_left:
                matched.append((u_id, name))
        except: continue
    return matched
