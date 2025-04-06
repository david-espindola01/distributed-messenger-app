import sqlite3
import os
from contextlib import contextmanager

DB_NAME = "messenger.db"

@contextmanager
def get_cursor():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # permite acceso por nombre de columna
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    finally:
        conn.close()


def create_db():
    if not os.path.exists(DB_NAME):
        schema_path = os.path.join(os.path.dirname(__file__), "..", "schema.sql")
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = f.read()
        with get_cursor() as cursor:
            cursor.executescript(schema)



# -------------------- Usuarios --------------------

def create_user(username, password, first_name, last_name):
    with get_cursor() as cursor:
        cursor.execute("""
            INSERT INTO users (username, password, first_name, last_name)
            VALUES (?, ?, ?, ?)
        """, (username, password, first_name, last_name))
        return cursor.lastrowid

def find_all_users():
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM users")
        return cursor.fetchall()

def find_user_by_id(user_id):
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return cursor.fetchone()

def find_user_by_username(username):
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        return cursor.fetchone()

def activate_user(user_id):
    with get_cursor() as cursor:
        cursor.execute("UPDATE users SET is_active = 1 WHERE id = ?", (user_id,))

# -------------------- Chats --------------------

def create_chat(chat_id, name, created_at, updated_at):
    with get_cursor() as cursor:
        cursor.execute("""
            INSERT INTO chats (id, name, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        """, (chat_id, name, created_at, updated_at))

def add_user_to_chat(user_id, chat_id, is_admin=0):
    with get_cursor() as cursor:
        cursor.execute("""
            INSERT INTO user_chat (user_id, chat_id, is_admin)
            VALUES (?, ?, ?)
        """, (user_id, chat_id, is_admin))

def find_user_chats(user_id):
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT c.*, uc.is_admin FROM chats c
            JOIN user_chat uc ON c.id = uc.chat_id
            WHERE uc.user_id = ?
        """, (user_id,))
        return cursor.fetchall()

def get_chat_participants(chat_id):
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT u.* FROM users u
            JOIN user_chat uc ON u.id = uc.user_id
            WHERE uc.chat_id = ?
        """, (chat_id,))
        return cursor.fetchall()

# -------------------- Mensajes --------------------

def add_message(sender_id, chat_id, content, timestamp):
    with get_cursor() as cursor:
        cursor.execute("""
            INSERT INTO messages (sender_id, chat_id, content, timestamp)
            VALUES (?, ?, ?, ?)
        """, (sender_id, chat_id, content, timestamp))

def get_messages_for_chat(chat_id):
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT * FROM messages WHERE chat_id = ?
            ORDER BY timestamp ASC
        """, (chat_id,))
        return cursor.fetchall()

create_db()