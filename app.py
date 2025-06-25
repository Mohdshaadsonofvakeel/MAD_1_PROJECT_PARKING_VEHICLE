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

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    reservations = db.relationship('Reservation', backref='user', lazy=True, cascade='all, delete-orphan')

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def get_active_reservation(self):
        return Reservation.query.filter_by(user_id=self.id, status='active').first()

    def get_parking_history(self):
        return Reservation.query.filter_by(user_id=self.id).order_by(Reservation.start_time.desc()).all()

class ParkingLot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    pin_code = db.Column(db.String(10), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    price_per_hour = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    spots = db.relationship('ParkingSpot', backref='lot', lazy=True, cascade='all, delete-orphan')

    def get_available_spots(self):
        return ParkingSpot.query.filter_by(lot_id=self.id, status='available').all()

    def get_occupied_spots(self):
        return ParkingSpot.query.filter_by(lot_id=self.id, status='occupied').all()

    def get_occupancy_rate(self):
        occupied = len(self.get_occupied_spots())
        return (occupied / self.capacity) * 100 if self.capacity > 0 else 0

    def create_spots(self):
        existing_spots = ParkingSpot.query.filter_by(lot_id=self.id).count()
        for i in range(existing_spots + 1, self.capacity + 1):
            spot = ParkingSpot(
                spot_number=f"{self.name}-{i:03d}",
                lot_id=self.id,
                status='available'
            )
            db.session.add(spot)
        db.session.commit()

class ParkingSpot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    spot_number = db.Column(db.String(50), unique=True, nullable=False)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)
    status = db.Column(db.String(20), default='available')
    
    reservations = db.relationship('Reservation', backref='spot', lazy=True)

    def get_current_reservation(self):
        return Reservation.query.filter_by(spot_id=self.id, status='active').first()

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='active')
    cost = db.Column(db.Float, default=0.0)
    
    def calculate_cost(self):
        if self.end_time and self.start_time:
            duration = self.end_time - self.start_time
            hours = duration.total_seconds() / 3600
            if hours < 1:
                hours = 1
            else:
                hours = int(hours) + (1 if duration.total_seconds() % 3600 > 0 else 0)
            
            lot = ParkingLot.query.get(self.spot.lot_id)
            self.cost = hours * lot.price_per_hour
            return self.cost
        return 0

    def get_duration(self):
        if self.end_time and self.start_time:
            duration = self.end_time - self.start_time
            hours = int(duration.total_seconds() // 3600)
            minutes = int((duration.total_seconds() % 3600) // 60)
            return f"{hours}h {minutes}m"
        elif self.start_time:
            duration = datetime.utcnow() - self.start_time
            hours = int(duration.total_seconds() // 3600)
            minutes = int((duration.total_seconds() % 3600) // 60)
            return f"{hours}h {minutes}m (ongoing)"
        return "0h 0m"

    def end_reservation(self):
        self.end_time = datetime.utcnow()
        self.status = 'completed'
        self.cost = self.calculate_cost()
        
        spot = ParkingSpot.query.get(self.spot_id)
        spot.status = 'available'
        
        db.session.commit()
        return self.cost

def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def admin_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if not session.get('is_admin'):
            flash('Admin access required', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            
            if user.is_admin:
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        full_name = request.form['full_name']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('register.html')
        
        user = User(
            username=username,
            full_name=full_name,
            password=generate_password_hash(password)
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    total_lots = ParkingLot.query.count()
    total_spots = ParkingSpot.query.count()
    occupied_spots = ParkingSpot.query.filter_by(status='occupied').count()
    total_users = User.query.filter_by(is_admin=False).count()
    active_reservations = Reservation.query.filter_by(status='active').count()
    
    recent_reservations = Reservation.query.order_by(Reservation.start_time.desc()).limit(5).all()
    
    stats = {
        'total_lots': total_lots,
        'total_spots': total_spots,
        'occupied_spots': occupied_spots,
        'available_spots': total_spots - occupied_spots,
        'total_users': total_users,
        'active_reservations': active_reservations,
        'occupancy_rate': (occupied_spots / total_spots * 100) if total_spots > 0 else 0
    }
    
    return render_template('admin/dashboard.html', stats=stats, recent_reservations=recent_reservations)

@app.route('/admin/parking_lots')
@admin_required
def admin_parking_lots():
    lots = ParkingLot.query.all()
    return render_template('admin/parking_lots.html', lots=lots)

@app.route('/admin/add_lot', methods=['GET', 'POST'])
@admin_required
def admin_add_lot():
    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        pin_code = request.form['pin_code']
        capacity = int(request.form['capacity'])
        price_per_hour = float(request.form['price_per_hour'])
        
        lot = ParkingLot(
            name=name,
            address=address,
            pin_code=pin_code,
            capacity=capacity,
            price_per_hour=price_per_hour
        )
        
        db.session.add(lot)
        db.session.commit()
        
        lot.create_spots()
        
        flash(f'Parking lot "{name}" created successfully with {capacity} spots!', 'success')
        return redirect(url_for('admin_parking_lots'))
    
    return render_template('admin/add_lot.html')

@app.route('/admin/users')
@admin_required
def admin_users():
    users = User.query.filter_by(is_admin=False).all()
    return render_template('admin/users.html', users=users)

@app.route('/user/dashboard')
@login_required
def user_dashboard():
    user = User.query.get(session['user_id'])
    active_reservation = user.get_active_reservation()
    recent_reservations = user.get_parking_history()[:5]
    
    available_lots = []
    for lot in ParkingLot.query.all():
        available_spots = len(lot.get_available_spots())
        if available_spots > 0:
            available_lots.append({
                'lot': lot,
                'available_spots': available_spots
            })
    
    return render_template('user/dashboard.html', 
                         active_reservation=active_reservation,
                         recent_reservations=recent_reservations,
                         available_lots=available_lots)

@app.route('/user/book_spot/<int:lot_id>')
@login_required
def user_book_spot(lot_id):
    user = User.query.get(session['user_id'])
    
    if user.get_active_reservation():
        flash('You already have an active parking reservation!', 'error')
        return redirect(url_for('user_dashboard'))
    
    lot = ParkingLot.query.get_or_404(lot_id)
    available_spots = lot.get_available_spots()
    
    if not available_spots:
        flash('No available spots in this parking lot!', 'error')
        return redirect(url_for('user_dashboard'))
    
    first_available_spot = available_spots[0]
    first_available_spot.status = 'occupied'
    
    reservation = Reservation(
        user_id=user.id,
        spot_id=first_available_spot.id,
        start_time=datetime.utcnow(),
        status='active'
    )
    
    db.session.add(reservation)
    db.session.commit()
    
    flash(f'Successfully booked spot {first_available_spot.spot_number} at {lot.name}!', 'success')
    return redirect(url_for('user_dashboard'))

@app.route('/user/release_spot')
@login_required
def user_release_spot():
    user = User.query.get(session['user_id'])
    active_reservation = user.get_active_reservation()
    
    if not active_reservation:
        flash('No active parking reservation found!', 'error')
        return redirect(url_for('user_dashboard'))
    
    cost = active_reservation.end_reservation()
    
    flash(f'Parking released successfully! Total cost: ${cost:.2f}', 'success')
    return redirect(url_for('user_dashboard'))

@app.context_processor
def inject_user():
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        return {'current_user': user}
    return {'current_user': None}

if __name__ == '__main__':
    with app.app_context():
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
    
    app.run(debug=True)