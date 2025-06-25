import os

template_dir = "templates"
admin_template_dir = "templates/admin"
user_template_dir = "templates/user"

directories = [template_dir, admin_template_dir, user_template_dir]

for directory in directories:
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}")

file_mappings = {
    "base_template.html": "templates/base.html",
    "index_template.html": "templates/index.html", 
    "login_template.html": "templates/login.html",
    "register_template.html": "templates/register.html",
    "admin_dashboard.html": "templates/admin/dashboard.html",
    "admin_add_lot.html": "templates/admin/add_lot.html",
    "user_dashboard.html": "templates/user/dashboard.html"
}

print("\nTo organize your templates correctly, move these files:")
for source, target in file_mappings.items():
    print(f"{source} -> {target}")

print("\nMain application file: complete_app.py")
print("Rename complete_app.py to app.py before running")
print("\nTo run the application:")
print("1. Move template files to correct locations")
print("2. Rename complete_app.py to app.py") 
print("3. Run: python app.py")