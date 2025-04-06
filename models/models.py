import datetime
import uuid

class User:
    def __init__(self, username, password, first_name, last_name, user_id):
        self.username = username
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.user_id = user_id
        self.is_active = False
        self.groupChats = []
        self.chats = []

    def new_chat(self, chat):
        if chat not in self.chats:
            if chat.is_group_chat():
                self.groupChats.append(chat)
                chat.set_admin(self)
            else:
                self.chats.append(chat)
        chat.participants.append(self)
    
    def remove_chat(self, chat):
        if chat in self.chats:
            self.chats.remove(chat)
        
    def __repr__(self):
        return f"User(username={self.username})"
    
    def to_dict(self):
        return self.__dict__

class Message:
    def __init__(self, sender, recipient, content):
        self.sender = sender
        self.recipient = recipient
        self.content = content
        self.timestamp = datetime.now()

    def __repr__(self):
        return f"Message(sender={self.sender.username}, recipient={self.recipient}, content={self.content})"


class Chat:
    def __init__(self, participants):
        self.participants = participants
        self.name = None
        self.messages = []
        self.is_active = True
        self.admin = []
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
        return self.__dict__