from flask import Flask, request, jsonify
from controllers.controller import login, logout, get_logged_user

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login_user():
    data = request.json
    try:
        user = login(data["username"], data["password"])
        return jsonify(user.to_dict())
    except ValueError as e:
        return jsonify({"error": str(e)}), 401

@app.route('/logout/<user_id>', methods=['POST'])
def logout_user(user_id):
    logout(user_id)
    return jsonify({"message": "Logged out"})

@app.route('/session/<user_id>', methods=['GET'])
def session_user(user_id):
    user = get_logged_user(user_id)
    return jsonify(user.to_dict() if user else {})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)

