from flask import Flask, request, jsonify
from controllers.controller import register_user, get_user, get_user_by_username, list_users, activate_user

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    user = register_user(data["username"], data["password"], data["first_name"], data["last_name"])
    return jsonify(user.to_dict())

@app.route('/users/<user_id>', methods=['GET'])
def get_user_endpoint(user_id):
    user = get_user(user_id)
    return jsonify(user.to_dict() if user else {})

@app.route('/users', methods=['GET'])
def list_all_users():
    users = list_users()
    return jsonify([u.to_dict() for u in users])

@app.route('/users/<user_id>/activate', methods=['POST'])
def activate(user_id):
    activate_user(user_id)
    return jsonify({"message": "User activated"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

