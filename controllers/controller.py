from models.models import User, Chat, Message
from datetime import datetime
import uuid
import database.connect as connect

# Sesiones en memoria
sessions = {}

connect.create_db()
# ----------------- Usuarios -----------------

def register_user(username, password, first_name, last_name):
    user_id = connect.create_user(username, password, first_name, last_name)
    return get_user(user_id)

def get_user(user_id):
    row = connect.find_user_by_id(user_id)
    if not row:
        return None

    user = User(row["username"], row["password"], row["first_name"], row["last_name"], row["id"])
    user.is_active = row["is_active"] == 1

    user_chats = connect.find_user_chats(user.user_id)
    for chat_row in user_chats:
        chat = Chat(participants=[])  # se llenará luego
        chat.chat_id = chat_row["id"]
        chat.name = chat_row["name"]
        chat.is_active = chat_row["is_active"] == 1
        chat.created_at = datetime.fromisoformat(chat_row["created_at"])
        chat.updated_at = datetime.fromisoformat(chat_row["updated_at"])
        is_admin = chat_row["is_admin"] == 1

        participants = connect.get_chat_participants(chat.chat_id)
        for p in participants:
            p_user = User(p["username"], p["password"], p["first_name"], p["last_name"], p["id"])
            p_user.is_active = p["is_active"] == 1
            chat.participants.append(p_user)
            if p_user.user_id == user.user_id:
                user.new_chat(chat)

        if is_admin:
            chat.set_admin(user)

    return user

def get_user_by_username(username):
    row = connect.find_user_by_username(username)
    return User(row["username"], row["password"], row["first_name"], row["last_name"], row["id"]) if row else None

def list_users():
    rows = connect.find_all_users()
    return [User(row["username"], row["password"], row["first_name"], row["last_name"], row["id"]) for row in rows]

def activate_user(user_id):
    connect.activate_user(user_id)

# ----------------- Sesiones -----------------

def login(username, password):
    user = get_user_by_username(username)
    if user and user.password == password:
        sessions[user.user_id] = user
        return user
    raise ValueError("Usuario o contraseña incorrectos.")

def logout(user_id):
    if user_id in sessions:
        del sessions[user_id]

def get_logged_user(user_id):
    return sessions.get(user_id)

# ----------------- Chats -----------------

def new_chat(creator_id, participant_ids, name=None):
    creator = get_user(creator_id)
    if not creator:
        raise ValueError("Usuario creador no encontrado.")

    participants = [creator]
    for pid in participant_ids:
        if pid != creator.user_id:
            user = get_user(pid)
            if user:
                participants.append(user)
            else:
                raise ValueError(f"Participante con ID {pid} no encontrado.")

    chat_id = str(uuid.uuid4())[:8]
    now = datetime.now().isoformat()
    connect.create_chat(chat_id, name or f"Chat-{chat_id}", now, now)

    for user in participants:
        is_admin = 1 if user.user_id == creator.user_id else 0
        connect.add_user_to_chat(user.user_id, chat_id, is_admin)

    chat = Chat(participants=participants)
    chat.chat_id = chat_id
    chat.name = name or f"Chat-{chat_id}"
    chat.created_at = datetime.fromisoformat(now)
    chat.updated_at = datetime.fromisoformat(now)
    chat.admin.append(creator)
    for user in participants:
        user.new_chat(chat)

    return chat

def send_message(chat, sender, content):
    if sender not in chat.participants:
        raise ValueError("El remitente no pertenece al chat.")

    timestamp = datetime.now().isoformat()
    connect.add_message(sender.user_id, chat.chat_id, content, timestamp)

    message = Message(sender, chat, content)
    message.timestamp = datetime.fromisoformat(timestamp)
    chat.messages.append(message)
    chat.updated_at = datetime.now()
    return message

def get_chat_messages(chat_id):
    rows = connect.get_messages_for_chat(chat_id)
    messages = []
    for row in rows:
        sender = get_user(row["sender_id"])
        chat = Chat(participants=[])  # No se usan participantes aquí
        chat.chat_id = row["chat_id"]
        msg = Message(sender, chat, row["content"])
        msg.timestamp = datetime.fromisoformat(row["timestamp"])
        messages.append(msg)
    return messages
