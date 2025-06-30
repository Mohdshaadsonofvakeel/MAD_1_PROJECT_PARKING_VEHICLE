from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import hashlib
from datetime import datetime
import os
from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash('Access denied. Admins only.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

app = Flask(__name__)
app.secret_key = 'parking_app_secret_key_2025'

DATABASE = 'parking.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()

    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            address TEXT NOT NULL,
            pin_code TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS parking_lots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            pin_code TEXT NOT NULL,
            price_per_hour REAL NOT NULL,
            max_spots INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS parking_spots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lot_id INTEGER NOT NULL,
            spot_number INTEGER NOT NULL,
            status TEXT DEFAULT 'available',
            vehicle_number TEXT,
            FOREIGN KEY (lot_id) REFERENCES parking_lots (id)
        )
    ''')

 
    conn.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            spot_id INTEGER NOT NULL,
            lot_id INTEGER NOT NULL,
            vehicle_number TEXT,
            check_in_time TIMESTAMP,
            check_out_time TIMESTAMP,
            total_cost REAL DEFAULT 0,
            status TEXT DEFAULT 'active',
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (spot_id) REFERENCES parking_spots (id),
            FOREIGN KEY (lot_id) REFERENCES parking_lots (id)
        )
    ''')

  
    admin_password = hashlib.sha256('admin123'.encode()).hexdigest()
    conn.execute('''
        INSERT OR IGNORE INTO users 
        (full_name, username, email, password, address, pin_code, role)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        'Administrator',        # full_name
        'admin',               # username  
        'admin@parking.com',   # email
        admin_password,        # password
        'Admin Office',        # address
        '000000',             # pin_code
        'admin'               # role
    ))
    
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()
