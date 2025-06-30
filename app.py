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
from flask import render_template, request, redirect, url_for, session, flash
from models import get_db_connection, hash_password
from functools import wraps
from datetime import datetime

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash('Access denied. Admins only.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def register_routes(app):
    @app.route('/')
    def index():
        # ... (rest of your route code)
        pass

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        # ... (rest of your route code)
        pass

    # ... (all your other @app.route functions, unchanged)
