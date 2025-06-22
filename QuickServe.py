import os
import time
import json
import secrets
import sys

from templates import LOGIN_TEMPLATE, HOME_TEMPLATE, ERROR_TEMPLATE
from flask import Flask, render_template_string, request, send_file, session
from flask_limiter import Limiter
from waitress import serve


app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
limiter = Limiter(
    app,
    default_limits=["32 per minute"],
)

# Get the directory where the executable or script is located
if getattr(sys, "frozen", False):  # If the code is compiled into an executable
    current_directory = os.path.dirname(sys.executable)
else:
    current_directory = os.path.dirname(os.path.abspath(__file__))

ignore_files = [
    f"{os.path.join(current_directory, __file__)}",
    f"{os.path.join(current_directory, 'favicon.ico')}",
    f"{os.path.join(current_directory, 'config.json')}",
]

# Create a config.json file if not already present in current dir
config_file = os.path.join(current_directory, "config.json")

if not os.path.exists(config_file):  # Create config.json file if not present
    with open(config_file, "w") as file:
        json.dump({"users": {}, "port": 5000}, file, indent=4)

# Load configuration from the config.json file
def load_config():
    with open(config_file, "r") as file:
        data = json.load(file)
        return data.get("users", {}), data.get("port", 5000)  # Default port 5000 if missing

# Save configuration back to config.json
def save_config(users, port):
    with open(config_file, "w") as file:
        json.dump({"users": users, "port": port}, file, indent=4)

# Load users and port
user_accounts, server_port = load_config()


# Get the current working directory
def get_current_directory():
    return os.getcwd()


# Get the formatted date of last modification for a file
def get_file_date_modified(file_path):
    return time.strftime(
        "%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(file_path))
    )


# Get the size of a file in bytes
def get_file_size(file_path):
    return os.path.getsize(file_path)


# Class representing a file or folder entry
class FileEntry:
    def __init__(self, name, path, type):
        self.name = name
        self.path = path
        self.type = type
        self.date_modified = get_file_date_modified(path)
        self.size = get_file_size(path)


# Register the route to serve the favicon.ico file from the root directory
@app.route("/favicon.ico")
def serve_favicon():
    return send_file(os.path.join(current_directory, "favicon.ico"), mimetype="image/x-icon")


# Route to render the main page
@app.route("/")
def index():
    if "logged_in" in session and session["logged_in"]:
        current_dir = get_current_directory()
        files = get_files_in_directory(current_dir)
        return render_template_string(
            HOME_TEMPLATE, files=files, current_dir=current_dir, folder_or_file=""
        )
    else:
        return render_template_string(LOGIN_TEMPLATE, login_failed=False)


# Route to handle file server operations
@app.route("/", methods=["POST"])
@limiter.limit("32 per minute")
def file_server():
    global user_accounts
    user_accounts, _ = load_config()  # Reload users

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in user_accounts and user_accounts[username] == password:
            session["logged_in"] = True
            current_dir = get_current_directory()
            files = get_files_in_directory(current_dir)
            return render_template_string(HOME_TEMPLATE, files=files, current_dir=current_dir, folder_or_file="")
        else:
            return render_template_string(LOGIN_TEMPLATE, login_failed=True)

    if "logged_in" in session and session["logged_in"]:
        current_dir = request.args.get("current_dir", "")
        files = get_files_in_directory(current_dir)
        return render_template_string(HOME_TEMPLATE, files=files, current_dir=current_dir, folder_or_file="")

    return render_template_string(LOGIN_TEMPLATE, login_failed=False)


# Route to log out the user
@app.route("/logout")
def logout():
    session.clear()
    return render_template_string(LOGIN_TEMPLATE, login_failed=False)


# Route to upload a file to the specified folder
@app.route("/upload/<path:folder_or_file>", methods=["POST"])
@limiter.limit("10 per minute")
def upload_file(folder_or_file):
    if "file" not in request.files:
        return "No file part"

    file = request.files["file"]

    if file.filename == "":
        return "No selected file"

    current_dir = os.path.join(get_current_directory(), folder_or_file)
    uploaded_filename = file.filename

    counter = 1
    while os.path.exists(os.path.join(current_dir, uploaded_filename)):
        name, ext = os.path.splitext(file.filename)
        uploaded_filename = f"{name} ({counter}){ext}"
        counter += 1

    file.save(os.path.join(current_dir, uploaded_filename))
    return "File uploaded successfully"


# Route to download a file
@app.route("/download/<path:file_path>")
@limiter.limit("32 per minute")
def download_file(file_path):
    return send_file(file_path, as_attachment=True)


# Route to display the contents of a folder or serve a file for download
@app.route("/<path:folder_or_file>")
def show_folder_or_file(folder_or_file):
    folder_or_file_path = os.path.join(get_current_directory(), folder_or_file)
    return_text = ERROR_TEMPLATE
    if os.path.exists(folder_or_file_path):
        if os.path.isdir(folder_or_file_path):
            files = get_files_in_directory(folder_or_file_path)
            current_dir = folder_or_file_path
            return render_template_string(
                HOME_TEMPLATE,
                files=files,
                current_dir=current_dir,
                folder_or_file=folder_or_file,
            )

        if folder_or_file_path in ignore_files:
            return return_text

        return send_file(folder_or_file_path, as_attachment=True)

    return return_text


# Get a list of file and folder entries in a directory
def get_files_in_directory(directory):
    folders = []
    files = []

    if os.path.exists(directory) and os.path.isdir(directory):
        for entry in sorted(os.listdir(directory), key=lambda x: x.lower()): # Sort naturally (A-Z, special chars first)
            entry_path = os.path.join(directory, entry)
            if os.path.isdir(entry_path): # Collect folders first
                folders.append(FileEntry(entry, entry_path, "folder"))
            elif os.path.isfile(entry_path) and entry_path not in ignore_files: # Collect files
                files.append(FileEntry(entry, entry_path, "file"))
    
    return folders + files # Ensure folders appear first, then files


# Route to update the server port dynamically
@app.route("/set_port", methods=["POST"])
def set_port():
    global server_port
    new_port = request.form.get("port", type=int)

    if new_port and 1024 <= new_port <= 65535:  # Ensure valid port range
        server_port = new_port
        save_config(user_accounts, server_port)
        return f"Port updated to {server_port}. Restart the server for changes to take effect."
    else:
        return "Invalid port. Choose a number between 1024 and 65535."


# Get the directory name from a path
def dirname(path):
    return os.path.dirname(path)


# Get the base name of a path
def os_path_basename(path):
    return os.path.basename(path)


app.jinja_env.globals["os"] = os
app.jinja_env.filters["dirname"] = dirname
app.jinja_env.filters["basename"] = os_path_basename


# Run the app on the specified host and port for debugging
if __name__ == "__main__":
    # app.run(host="0.0.0.0", port=server_port, debug=True)
    print(f"Starting server on 'http://localhost:{server_port}'...")
    serve(app, host="0.0.0.0", port=server_port)
