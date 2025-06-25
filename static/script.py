import os

project_structure = """
parking_app/
├── app.py
├── models.py  
├── routes/
│   ├── __init__.py
│   ├── auth.py
│   ├── admin.py
│   └── user.py
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── admin/
│   │   ├── dashboard.html
│   │   ├── parking_lots.html
│   │   ├── add_lot.html
│   │   ├── users.html
│   │   └── parking_history.html
│   └── user/
│       ├── dashboard.html
│       ├── book_spot.html
│       ├── my_bookings.html
│       └── parking_history.html
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── script.js
└── instance/
    └── parking_app.db
"""

print("Vehicle Parking App Project Structure:")
print(project_structure)

print("\nNow creating the complete application files...")