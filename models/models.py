from datetime import datetime
import uuid

class User:
    def __init__(self, username, password, first_name, last_name, user_id):
        self.username = username
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.user_id = user_id
        self.is_active = False
        self.groupChats = []  # Lista de instancias Chat
        self.chats = []       # Lista de instancias Chat

    def new_chat(self, chat):
        if chat not in self.chats:
            if chat.is_group_chat():
                self.groupChats.append(chat)
                chat.set_admin(self)
            else:
                self.chats.append(chat)
        # Agrega el usuario a la lista de participantes del chat si aún no está
        if self not in chat.participants:
            chat.participants.append(self)
    
    def remove_chat(self, chat):
        if chat in self.chats:
            self.chats.remove(chat)
        
    def __repr__(self):
        return f"User(username={self.username})"
    
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "is_active": self.is_active,
            # Si deseas incluir los chats, podrías agregar una lista de chat IDs:
            "chats": [chat.chat_id for chat in self.chats],
            "groupChats": [chat.chat_id for chat in self.groupChats]
        }

class Message:
    def __init__(self, sender, recipient, content):
        self.sender = sender      # Instancia de User
        self.recipient = recipient  # Puede ser una instancia de Chat o User, según tu lógica
        self.content = content
        self.timestamp = datetime.now()

    def __repr__(self):
        return f"Message(sender={self.sender.username}, recipient={self.recipient}, content={self.content})"
    
    def to_dict(self):
        return {
            "sender": self.sender.to_dict() if hasattr(self.sender, "to_dict") else str(self.sender),
            "recipient": self.recipient.to_dict() if hasattr(self.recipient, "to_dict") else str(self.recipient),
            "content": self.content,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

class Chat:
    def __init__(self, participants):
        self.participants = participants  # Lista de instancias User
        self.name = None
        self.messages = []    # Lista de instancias Message
        self.is_active = True
        self.admin = []       # Lista de instancias User (administradores)
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.chat_id = self.generate_chat_id()
    
    def is_group_chat(self):
        return len(self.participants) > 2
    
    def set_admin(self, user):
        if user not in self.admin:
            self.admin.append(user)

    def generate_chat_id(self):
        return str(uuid.uuid4())[:8]
    
    def to_dict(self):
        return {
            "chat_id": self.chat_id,
            "name": self.name,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "participants": [participant.to_dict() for participant in self.participants],
            "admin": [admin.to_dict() for admin in self.admin],
            "messages": [message.to_dict() for message in self.messages]
        }
