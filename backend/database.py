import mysql.connector
from mysql.connector import pooling
import time


try:
    connection_pool = pooling.MySQLConnectionPool(
        pool_name="chat_pool",
        pool_size=10,
        pool_reset_session=True,
        host="localhost",
        user="admin",
        password="root",
        database="chat_db"
    )
    print("Connection pool created successfully")
except mysql.connector.Error as e:
    print(f"Error creating connection pool: {e}")
    connection_pool = None

def get_connection():
    if connection_pool is None:

        return mysql.connector.connect(
            host="localhost",
            user="admin",
            password="root",
            database="chat_db"
        )
    return connection_pool.get_connection()

def generate_chatid(userid1, userid2):
    user_pair = tuple(sorted([userid1, userid2]))
    return f"{user_pair[0]}:{user_pair[1]}"

def decode_chatid(chatid):
    userid1, userid2 = tuple(chatid.split(':'))
    return int(userid1), int(userid2)

def database_setup():
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS chat_db")
        cursor.execute("USE chat_db")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(16) UNIQUE,
                password VARCHAR(32),
                session_id CHAR(32)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sender VARCHAR(10),
                receiver VARCHAR(10),
                ciphertext TEXT,
                iv VARCHAR(24),
                chat_id VARCHAR(50),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS key_exchanges (
                id INT AUTO_INCREMENT PRIMARY KEY,
                reciever_id VARCHAR(20),
                sender_id VARCHAR(20),
                chat_id VARCHAR(50),
                public_key TEXT,
                accepted BOOLEAN DEFAULT FALSE
            )
        """)
        
        connection.commit()
        print("Database setup completed successfully")
    except mysql.connector.Error as e:
        print(f"Database setup error: {e}")
        if connection:
            connection.rollback()
        raise
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
def add_user(username, password, session_id):
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        sql = "INSERT INTO users (username, password, session_id) VALUES (%s, %s, %s)"
        cursor.execute(sql, (username, password, session_id))
        connection.commit()
    except mysql.connector.Error as e:
        print(f"Add user error: {e}")
        if connection:
            connection.rollback()
        raise
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def get_user(username):
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        sql = "SELECT * FROM users WHERE username = %s"
        cursor.execute(sql, (username,))
        user = cursor.fetchone()
        return user
    except mysql.connector.Error as e:
        print(f"Get user error: {e}")
        raise
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
def get_username(user_id):
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        sql = "SELECT username FROM users WHERE id = %s"
        cursor.execute(sql, (user_id,))
        username = cursor.fetchone()
        return username
    except mysql.connector.Error as e:
        print(f"Get username error: {e}")
        raise
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
def session_check(session_id):
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        sql = "SELECT * FROM users WHERE session_id = %s"
        cursor.execute(sql, (session_id,))
        user = cursor.fetchone()
        return user
    except mysql.connector.Error as e:
        print(f"Session check error: {e}")
        raise
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def add_message(message_data):
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        sql = "INSERT INTO messages (sender, receiver, ciphertext, iv, chat_id, timestamp) VALUES (%s, %s, %s, %s, %s, FROM_UNIXTIME(%s))"
        print(message_data)
        chat_id = generate_chatid(message_data.get('sender'), message_data.get('receiver'))
        cursor.execute(sql, (
            message_data.get('sender'), 
            message_data.get('receiver'), 
            message_data.get('ciphertext'), 
            message_data.get('iv'), 
            chat_id,
            time.time()
        ))
        connection.commit()
    except mysql.connector.Error as e:
        print(f"Add message error: {e}")
        if connection:
            connection.rollback()
        raise
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def get_messages(chat_id):
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        sql = "SELECT * FROM messages WHERE chat_id = %s ORDER BY timestamp ASC"
        cursor.execute(sql, (chat_id,))
        messages = cursor.fetchall()
        return messages
    except mysql.connector.Error as e:
        print(f"Get messages error: {e}")
        raise
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def get_key_exchanges(user_id):
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        sql = "SELECT * FROM key_exchanges WHERE reciever_id = %s"
        cursor.execute(sql, (user_id,))
        key_exchanges = cursor.fetchall()
        return key_exchanges
    except mysql.connector.Error as e:
        print(f"Get key exchanges error: {e}")
        raise
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def add_key_exchange(reciever_id, sender_id, chat_id, public_key):
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        sql = "INSERT INTO key_exchanges (reciever_id, sender_id, chat_id, public_key) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (reciever_id, sender_id, chat_id, public_key))
        connection.commit()
    except mysql.connector.Error as e:
        print(f"Add key exchange error: {e}")
        if connection:
            connection.rollback()
        raise
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def accept_key_exchange(reciever_id, chat_id):
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        sql = "UPDATE key_exchanges SET accepted = TRUE WHERE reciever_id = %s AND chat_id = %s"
        cursor.execute(sql, (reciever_id, chat_id))
        connection.commit()
    except mysql.connector.Error as e:
        print(f"Accept key exchange error: {e}")
        if connection:
            connection.rollback()
        raise
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def get_accepted_key_exchanges(user_id):
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        sql = "SELECT * FROM key_exchanges WHERE (reciever_id = %s OR sender_id = %s) AND accepted = TRUE"
        cursor.execute(sql, (user_id, user_id))
        key_exchanges = cursor.fetchall()
        return key_exchanges
    except mysql.connector.Error as e:
        print(f"Get accepted key exchanges error: {e}")
        raise
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
def get_key_exchange(chat_id):
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        sql = "SELECT * FROM key_exchanges WHERE chat_id = %s"
        cursor.execute(sql, (chat_id,))
        key_exchange = cursor.fetchone()
        return key_exchange
    except mysql.connector.Error as e:
        print(f"Get key exchange error: {e}")
        raise
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
def get_pool_status():
    if connection_pool:
        return {
            "pool_size": connection_pool.pool_size,
            "pool_name": connection_pool.pool_name
        }
    return None

if __name__ == "__main__":
  connection = get_connection()
  cursor = connection.cursor()
  cursor.execute("DROP TABLE messages")
  connection.commit()
  database_setup()