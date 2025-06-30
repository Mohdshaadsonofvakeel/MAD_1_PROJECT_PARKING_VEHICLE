import sqlite3
import hashlib

DATABASE = 'parking.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = get_db_connection()
    # ... (all your CREATE TABLE and admin user INSERT code here, unchanged)
    conn.commit()
    conn.close()
