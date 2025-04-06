from flask import Flask, request, jsonify
from controllers.controller import new_chat, get_user
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  

@app.route('/chat', methods=['POST'])
def create_chat():
    data = request.json
    chat = new_chat(data["creator_id"], data["participant_ids"], data.get("name"))
    return jsonify(chat.to_dict())

@app.route('/user/<user_id>/chats', methods=['GET'])
def get_user_chats(user_id):
    user = get_user(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify([chat.to_dict() for chat in user.chats])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

