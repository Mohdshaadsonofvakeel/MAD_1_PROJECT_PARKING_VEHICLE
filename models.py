from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

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