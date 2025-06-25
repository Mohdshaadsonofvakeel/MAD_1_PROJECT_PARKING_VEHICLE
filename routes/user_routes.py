from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import User, ParkingLot, ParkingSpot, Reservation, db
from auth_routes import login_required
from datetime import datetime

user_bp = Blueprint('user', __name__)

@user_bp.route('/dashboard')
@login_required
def dashboard():
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

@user_bp.route('/book_spot/<int:lot_id>')
@login_required
def book_spot(lot_id):
    user = User.query.get(session['user_id'])
    
    if user.get_active_reservation():
        flash('You already have an active parking reservation!', 'error')
        return redirect(url_for('user.dashboard'))
    
    lot = ParkingLot.query.get_or_404(lot_id)
    available_spots = lot.get_available_spots()
    
    if not available_spots:
        flash('No available spots in this parking lot!', 'error')
        return redirect(url_for('user.dashboard'))
    
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
    return redirect(url_for('user.dashboard'))

@user_bp.route('/release_spot')
@login_required
def release_spot():
    user = User.query.get(session['user_id'])
    active_reservation = user.get_active_reservation()
    
    if not active_reservation:
        flash('No active parking reservation found!', 'error')
        return redirect(url_for('user.dashboard'))
    
    cost = active_reservation.end_reservation()
    
    flash(f'Parking released successfully! Total cost: ${cost:.2f}', 'success')
    return redirect(url_for('user.dashboard'))

@user_bp.route('/my_bookings')
@login_required
def my_bookings():
    user = User.query.get(session['user_id'])
    reservations = user.get_parking_history()
    return render_template('user/my_bookings.html', reservations=reservations)

@user_bp.route('/parking_history')
@login_required
def parking_history():
    user = User.query.get(session['user_id'])
    page = request.args.get('page', 1, type=int)
    
    reservations = Reservation.query.filter_by(user_id=user.id).order_by(
        Reservation.start_time.desc()
    ).paginate(per_page=10, page=page, error_out=False)
    
    total_spent = db.session.query(db.func.sum(Reservation.cost)).filter_by(
        user_id=user.id, status='completed'
    ).scalar() or 0
    
    total_reservations = Reservation.query.filter_by(user_id=user.id).count()
    
    stats = {
        'total_spent': total_spent,
        'total_reservations': total_reservations,
        'completed_reservations': Reservation.query.filter_by(
            user_id=user.id, status='completed'
        ).count()
    }
    
    return render_template('user/parking_history.html', 
                         reservations=reservations, 
                         stats=stats)

@user_bp.route('/available_lots')
@login_required
def available_lots():
    lots_data = []
    for lot in ParkingLot.query.all():
        available_spots = lot.get_available_spots()
        lots_data.append({
            'lot': lot,
            'available_spots': len(available_spots),
            'occupancy_rate': lot.get_occupancy_rate()
        })
    
    return render_template('user/available_lots.html', lots_data=lots_data)