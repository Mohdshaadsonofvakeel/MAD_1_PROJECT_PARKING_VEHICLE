from flask import Flask, render_template, redirect, url_for, flash, session, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import secrets
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parking_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

from models import User, ParkingLot, ParkingSpot, Reservation
from routes.auth import auth_bp
from routes.admin import admin_bp  
from routes.user import user_bp

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(user_bp, url_prefix='/user')

@app.before_first_request
def create_tables():
    db.create_all()
    
    admin_exists = User.query.filter_by(username='admin@parking.com').first()
    if not admin_exists:
        admin_user = User(
            username='admin@parking.com',
            full_name='System Administrator', 
            password=generate_password_hash('admin123'),
            is_admin=True
        )
        db.session.add(admin_user)
        db.session.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.context_processor
def inject_user():
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        return {'current_user': user}
    return {'current_user': None}

if __name__ == '__main__':
    with app.app_context():
        create_tables()
    app.run(debug=True)