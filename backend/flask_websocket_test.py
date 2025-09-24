from flask import Flask
from flask_socketio import SocketIO, emit, join_room, leave_room
import threading
import os
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
socketio = SocketIO(app, cors_allowed_origins="*")

messages = []
lock = threading.Lock()

@socketio.on('connect')
def handle_connect():
    with lock:
        emit('message_history', messages)

@socketio.on('get_history')
def handle_get_history():
    with lock:
        emit('message_history', messages)

@socketio.on('send_message')
def handle_send_message(data):
    message_data = {
        'content': data.get('content'),
        'timestamp': data.get('timestamp'),
        'sender': data.get('sender', 'Unknown')
    }
    with lock:
        messages.append(message_data)
    emit('new_message', message_data, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
