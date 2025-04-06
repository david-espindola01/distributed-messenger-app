from flask import Flask, request, jsonify
from controllers.controller import send_message, get_chat_messages, get_user

app = Flask(__name__)

@app.route('/message', methods=['POST'])
def send():
    data = request.json
    user = get_user(data["sender_id"])
    if not user:
        return jsonify({"error": "User not found"}), 404

    for chat in user.chats:
        if chat.chat_id == data["chat_id"]:
            msg = send_message(chat, user, data["content"])
            return jsonify(msg.to_dict())
    return jsonify({"error": "Chat not found or user not part of it"}), 404

@app.route('/chat/<chat_id>/messages', methods=['GET'])
def get_messages(chat_id):
    messages = get_chat_messages(chat_id)
    return jsonify([msg.to_dict() for msg in messages])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)

