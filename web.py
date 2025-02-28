from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room
import os

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # Enable cross-origin for multiple clients

CHAT_DATA_PATH = "C:/Users/saikarthik/Desktop/New Chat/chatdata/"

os.makedirs(CHAT_DATA_PATH, exist_ok=True)
@app.route('/get_old_messages', methods=['GET'])
def get_old_messages():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    chat_file = os.path.join(CHAT_DATA_PATH, f"{user_id}.txt")
    if not os.path.exists(chat_file):
        return jsonify({"messages": []})  # Return empty if no messages yet

    with open(chat_file, "r") as f:
        messages = f.readlines()

    return jsonify({"messages": [message.strip() for message in messages]})

@socketio.on('connect')
def handle_connect():
    print(f"Client {request.sid} connected")

@socketio.on('join')
def handle_join(data):
    user_id = data.get('user_id')
    if user_id:
        join_room(user_id)  # Add client to a room based on user_id
        print(f"Client {request.sid} joined room: {user_id}")
    else:
        emit('error', {'error': 'User ID is required to join a room'})

@socketio.on('message_to_server')
def handle_message(data):
    user_id = data.get('user_id')
    message = data.get('message', '').strip()
    sport = data.get('port')
    print(sport)
    if not user_id or not message:
        return  # Ignore invalid requests
    sender_info = "Patient" if sport == '5001' else "Doctor"
    chat_file = os.path.join(CHAT_DATA_PATH, f"{user_id}.txt")

    # Append the message to the user's chat file
    with open(chat_file, "a") as f:
        f.write(f"{sender_info}: {message}\n")

    # Send the message to the specific room
    emit('message_to_client', {
        "message": f"{sender_info}: {message}",
        "sender": sender_info
    }, room=user_id)

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5400)
