# Vehicle Parking System - Installation Guide

## Quick Start

1. **Extract files to project directory**
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the application:**
   ```bash
   python complete_app.py
   ```
4. **Open browser and visit:** http://localhost:5000

## Default Admin Login
- Username: admin@parking.com
- Password: admin123

## File Structure

```
parking_app/
├── complete_app.py          # Main application file (run this)
├── requirements.txt         # Python dependencies
├── templates/              # HTML templates
│   ├── base_template.html
│   ├── index_template.html
│   ├── login_template.html
│   ├── register_template.html
│   ├── admin_dashboard.html
│   ├── admin_add_lot.html
│   └── user_dashboard.html
└── parking_app.db         # SQLite database (auto-created)
```

## Features Implemented

### Core Requirements (All Milestones Complete)
✅ Database Models: User, ParkingLot, ParkingSpot, Reservation
✅ Authentication: User registration/login, Admin login
✅ Admin Dashboard: Create/edit/delete parking lots, view users
✅ User Dashboard: Book spots, release spots, view history
✅ Auto-spot allocation: First available spot assignment
✅ Time-based cost calculation
✅ Parking history and summaries

### Technical Features
✅ SQLite database with programmatic creation
✅ Bootstrap responsive UI
✅ Session-based authentication (no Flask-Login)
✅ Real-time occupancy tracking
✅ Automatic parking spot generation
✅ Duration tracking and cost calculation

## How to Use

### As Admin:
1. Login with admin credentials
2. Create parking lots via "Add Parking Lot"
3. Spots are automatically generated based on capacity
4. Monitor real-time statistics and user activity
5. View all reservations and user management

### As User:
1. Register new account or login
2. View available parking lots on dashboard
3. Click "Book Spot" to reserve first available spot
4. Track active parking duration and estimated cost
5. Click "Release Spot" to end parking and calculate final cost

## Database Schema

- **User**: id, username, full_name, password, is_admin, created_at
- **ParkingLot**: id, name, address, pin_code, capacity, price_per_hour, created_at
- **ParkingSpot**: id, spot_number, lot_id, status (available/occupied)
- **Reservation**: id, user_id, spot_id, start_time, end_time, status, cost

## Cost Calculation Logic

- Hourly rates set per parking lot
- Minimum 1 hour charge
- Partial hours rounded up to next full hour
- Real-time duration tracking for active reservations

## Security Features

- Password hashing with Werkzeug
- Session-based authentication
- Admin-only route protection
- Input validation and CSRF protection

This application follows all MAD-I project requirements and is ready for submission.