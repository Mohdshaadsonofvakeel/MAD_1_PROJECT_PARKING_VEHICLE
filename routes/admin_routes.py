from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import User, ParkingLot, ParkingSpot, Reservation, db
from auth_routes import admin_required
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
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

@admin_bp.route('/parking_lots')
@admin_required
def parking_lots():
    lots = ParkingLot.query.all()
    return render_template('admin/parking_lots.html', lots=lots)

@admin_bp.route('/add_lot', methods=['GET', 'POST'])
@admin_required
def add_lot():
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
        return redirect(url_for('admin.parking_lots'))
    
    return render_template('admin/add_lot.html')

@admin_bp.route('/edit_lot/<int:lot_id>', methods=['GET', 'POST'])
@admin_required
def edit_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    
    if request.method == 'POST':
        lot.name = request.form['name']
        lot.address = request.form['address']
        lot.pin_code = request.form['pin_code']
        new_capacity = int(request.form['capacity'])
        lot.price_per_hour = float(request.form['price_per_hour'])
        
        if new_capacity != lot.capacity:
            if new_capacity < lot.capacity:
                spots_to_remove = ParkingSpot.query.filter_by(lot_id=lot_id).filter(
                    ParkingSpot.id > new_capacity
                ).all()
                for spot in spots_to_remove:
                    if spot.status == 'occupied':
                        flash('Cannot reduce capacity. Some spots are occupied.', 'error')
                        return render_template('admin/add_lot.html', lot=lot, edit=True)
                    db.session.delete(spot)
            
            lot.capacity = new_capacity
            db.session.commit()
            lot.create_spots()
        else:
            db.session.commit()
        
        flash(f'Parking lot "{lot.name}" updated successfully!', 'success')
        return redirect(url_for('admin.parking_lots'))
    
    return render_template('admin/add_lot.html', lot=lot, edit=True)

@admin_bp.route('/delete_lot/<int:lot_id>')
@admin_required
def delete_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    
    occupied_spots = ParkingSpot.query.filter_by(lot_id=lot_id, status='occupied').count()
    if occupied_spots > 0:
        flash(f'Cannot delete lot "{lot.name}". {occupied_spots} spots are currently occupied.', 'error')
        return redirect(url_for('admin.parking_lots'))
    
    db.session.delete(lot)
    db.session.commit()
    
    flash(f'Parking lot "{lot.name}" deleted successfully!', 'success')
    return redirect(url_for('admin.parking_lots'))

@admin_bp.route('/users')
@admin_required
def users():
    users = User.query.filter_by(is_admin=False).all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/parking_history')
@admin_required
def parking_history():
    page = request.args.get('page', 1, type=int)
    reservations = Reservation.query.order_by(Reservation.start_time.desc()).paginate(
        per_page=20, page=page, error_out=False
    )
    return render_template('admin/parking_history.html', reservations=reservations)

@admin_bp.route('/search')
@admin_required
def search():
    query = request.args.get('q', '')
    results = {
        'users': [],
        'lots': [],
        'spots': [],
        'reservations': []
    }
    
    if query:
        results['users'] = User.query.filter(
            User.username.contains(query) | User.full_name.contains(query)
        ).filter_by(is_admin=False).all()
        
        results['lots'] = ParkingLot.query.filter(
            ParkingLot.name.contains(query) | ParkingLot.address.contains(query)
        ).all()
        
        results['spots'] = ParkingSpot.query.filter(
            ParkingSpot.spot_number.contains(query)
        ).all()
        
        results['reservations'] = Reservation.query.join(User).filter(
            User.username.contains(query) | User.full_name.contains(query)
        ).all()
    
    return render_template('admin/search_results.html', results=results, query=query)