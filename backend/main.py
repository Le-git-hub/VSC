import flask
import bcrypt
import uuid
import os
from database import add_user, get_user, session_check, get_messages, add_message, decode_chatid, get_key_exchanges, add_key_exchange, accept_key_exchange, get_accepted_key_exchanges, get_key_exchange, get_username
from flask_cors import CORS
from flask_socketio import SocketIO, emit, disconnect, join_room
import traceback
import time
app = flask.Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
CORS(app, origins=["http://localhost:3000"], supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins="http://localhost:3000", cors_credentials=True)

api = flask.Blueprint('api', __name__)

@api.route('/signup', methods=['POST'])
def signup():
    try:
        data = flask.request.json
        username = data['username']
        password = data['password']
        session_id = uuid.uuid4().hex
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')
        add_user(username, hashed_password, session_id)

        resp = flask.make_response(flask.jsonify({'success': True, 'message': 'User created successfully', 'session_id': session_id}), 200)
        resp.set_cookie('session_id', session_id, httponly=True, secure=False, samesite='None')
        return resp
    except Exception as e:
        print(f"Signup error: {e}")
        return flask.jsonify({'success': False, 'message': 'Signup failed'}), 401

@api.route('/login', methods=['POST'])
def login():
    data = flask.request.json
    username = data['username']
    password = data['password']
    try:
        user_info = get_user(username)
        if user_info:
            password_hash = user_info[2]
            password_check = bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
            if password_check:
                resp = flask.make_response(flask.jsonify({"success": True, "message": "Login successful", "session_id": user_info[3]}), 200)
                resp.set_cookie('session_id', user_info[3], httponly=True, secure=False, samesite='None')
                
                return resp
            else:
                return flask.jsonify({"success": False, "message": "Wrong Password"}), 401
        else:
            return flask.jsonify({"success": False, "message": "User not found"}), 401
    except Exception as e:
        print(f"Login error: {e}")
        return flask.jsonify({"success": False, "message": "Error occurred, please try again later"}), 500

@api.route("/check_username", methods=['POST'])
def check_username():
    data = flask.request.json
    username = data['username']
    try:
        user = get_user(username)
        if user:
            return flask.jsonify({"success": False, "message": "Username not available"}), 409
        else:
            return flask.jsonify({"success": True, "message": "Username is available"}), 200
    except Exception as e:
        print(f"Check username error: {e}")
        return flask.jsonify({"success": False, "message": "Error occurred, please try again later"}), 500
    
@api.route("/username_to_id", methods=['POST'])
def username_to_id():
    try:
        data = flask.request.json
        username = data['username']
        user = get_user(username)
        if user:
            return flask.jsonify({"success": True, "message": "Username to id conversion successful", "data": {"User_id": user[0]}}), 200
        else:
            return flask.jsonify({"success": False, "message": "User not found"}), 404
    except Exception as e:
        print(f"Username to ID error: {e}")
        return flask.jsonify({"success": False, "message": "Error occurred, please try again later"}), 500

@api.route("/authenticate", methods=['GET'])
def authenticate():
    try:
        user = session_check(flask.request.cookies['session_id'])
        if user:
            return flask.jsonify({"success": True, "message": "Authentication successful", "data": {"User_id": user[0], "Username": user[1]}}), 200
        else:
            return flask.jsonify({"success": False, "message": "Authentication Failed"}), 401
    except Exception as e:
        print(f"Authentication error: {e}")
        return flask.jsonify({"success": False, "message": "Error occurred, please try again later"}), 500
    
# -- websocket --
def authenticate_check():
    session_id = flask.request.cookies.get('session_id')
    if not session_id:
        disconnect()
        return None
    user_data = session_check(session_id)
    if user_data:
        return user_data[0]
    disconnect()
    return None

@socketio.on('connect')
def handle_connect():
    user_id = authenticate_check()
    if user_id is None:
        return
    
    try:
        join_room(f"user_{user_id}")
        key_exchanges = get_key_exchanges(user_id)
        emit('key_exchange_requests', key_exchanges, room=f"user_{user_id}")
    except Exception as e:
        print(f"Connect error: {e}")
        disconnect()

@socketio.on('connected_chats')
def handle_connected_chats():
    user_id = authenticate_check()
    if user_id is None:
        return
    
    try:
        key_exchanges = get_accepted_key_exchanges(user_id)
        for key_exchange in key_exchanges:
            join_room(f"chat_{key_exchange[3]}")
        emit('connected_chats', {'chats': [{"reciever_id": int(key_exchange[1]), "sender_id": int(key_exchange[2]), "chat_id": key_exchange[3], "unread_messages": len(get_messages(key_exchange[2])), "reciever_username": get_username(key_exchange[1]), "sender_username": get_username(key_exchange[2])} for key_exchange in key_exchanges]}, room=f"user_{user_id}")
    except Exception as e:
        print(f"Connected chats error: {e}")

@socketio.on('connect_chat')
def handle_connect_chat(data):
    user_id = authenticate_check()
    if user_id is None:
        return
        
    chat_id = data.get('chat_id') if data else None
    if not chat_id:
        disconnect()
        return
        
    try:
        chat_users = decode_chatid(chat_id)
        if user_id not in chat_users:
            disconnect()
            return

        messages = get_messages(chat_id)
        join_room(f"chat_{chat_id}")
        emit('message_history', messages, room=f"chat_{chat_id}")
    except Exception as e:
        print(f"Connect chat error: {e}")
        disconnect()
@socketio.on('key_exchange_requests')
def handle_key_exchange_requests():
    user_id = authenticate_check()
    if user_id is None:
        return
    key_exchanges = get_key_exchanges(user_id)
    emit('key_exchange_requests', key_exchanges, room=f"user_{user_id}")

@socketio.on('key_exchange_success')
def handle_key_exchange_success(data):
    user_id = authenticate_check()
    if user_id is None:
        return
        
    try:
        chat_id = data.get('chat_id')
        public_key = data.get('public_key')
        
        if not chat_id or not public_key:
            return
        
        existing_exchanges = get_accepted_key_exchanges(user_id)
        for exchange in existing_exchanges:
            if exchange[3] == chat_id:
                print(f"Key exchange already accepted for chat_id: {chat_id}, ignoring")
                return
            
        accept_key_exchange(user_id, chat_id)
        emit('key_exchange_success', {
            'sender_id': user_id,
            'chat_id': chat_id,
            'public_key': public_key
        }, room=f"chat_{chat_id}")
    except Exception as e:
        print(f"Key exchange success error: {e}")

@socketio.on('key_exchange_request')
def handle_key_exchange_request(data):
    user_id = authenticate_check()
    if user_id is None:
        return
        
    try:
        reciever_id = data.get('reciever_id')
        chat_id = data.get('chat_id')
        public_key = data.get('public_key')
        
        if get_key_exchange(chat_id):
            print(f"Key exchange already exists for chat_id: {chat_id}, ignoring request")
            return
            
        if not all([reciever_id, chat_id, public_key]):
            return
            
        chat_users = decode_chatid(chat_id)
        if user_id not in chat_users:
            disconnect()
            return
            
        add_key_exchange(reciever_id, user_id, chat_id, public_key)
        
        join_room(f"chat_{chat_id}")

        emit('new_key_exchange_request', {
            'sender_id': user_id,
            'chat_id': chat_id,
            'public_key': public_key
        }, room=f"user_{reciever_id}")
        
    except Exception as e:
        print(f"Key exchange request error: {e}")

@socketio.on('get_history')
def handle_get_history(data):
    user_id = authenticate_check()
    if user_id is None:
        return
        
    try:
        chat_id = data.get('chat_id') if data else None
        if not chat_id:
            return
            
        chat_users = decode_chatid(chat_id)
        if user_id not in chat_users:
            disconnect()
            return

        messages = get_messages(chat_id)
        emit('message_history', {"messages": [{"sender": m[1], "receiver": m[2], "ciphertext": m[3], "iv": m[4], "chat_id": m[5], "timestamp": m[6].timestamp()} for m in messages]})
    except Exception as e:
        print(f"Get history error: {e}")

@socketio.on('send_message')
def handle_send_message(data):
    user_id = authenticate_check()
    if user_id is None:
        return
        
    try:
        chat_id = data.get('chat_id')
        print(chat_id)
        if not chat_id:
            return
            
        chat_users = decode_chatid(chat_id)
        if user_id not in chat_users:
            disconnect()
            return
        print(data)
        message_data = {
            'sender': data.get('sender'),
            'receiver': data.get('receiver'),
            'ciphertext': data.get('ciphertext'),
            'iv': data.get('iv'),
            'timestamp': time.time(),
        }

        if user_id != message_data['sender']:
            disconnect()
            return

        add_message(message_data)
        emit('new_message', message_data, room=f"chat_{chat_id}")
        
    except Exception as e:
        print(f"Send message error: {traceback.format_exc()}")

app.register_blueprint(api, url_prefix="/api")

if __name__ == "__main__":
    socketio.run(app, debug=True)