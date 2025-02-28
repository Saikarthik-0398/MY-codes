from flask import Flask, render_template, request
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_old_messages', methods=['GET'])
def get_old_messages():
    user_id = request.args.get("user_id")  # Expect user_id passed from the client
    if not user_id:
        return {"error": "User ID is required"}, 400

    messages = []
    chat_file = f"C:/Users/saikarthik/Desktop/New Chat/chatdata/{user_id}.txt"
    
    if os.path.exists(chat_file):
        with open(chat_file, "r") as file:
            messages = file.readlines()
    return {"messages": [msg.strip() for msg in messages]}

if __name__ == '__main__':
    app.run(debug=True, port=5001)
