import os
import time
import threading
import json
import secrets
import sys
from waitress import serve
from flask import Flask, render_template_string, request, send_file, session
from flask_limiter import Limiter


app = Flask(__name__)
app.secret_key = secrets.token_hex(16)


limiter = Limiter(
    app,
    default_limits=["32 per minute"],
)


# Get the directory where the executable or script is located
if getattr(sys, 'frozen', False):  # If the code is compiled into an executable
    current_directory = os.path.dirname(sys.executable)
else:
    current_directory = os.path.dirname(os.path.abspath(__file__))

ignore_files = [f"{os.path.join(current_directory, __file__)}",
                f"{os.path.join(current_directory, 'favicon.ico')}",
                f"{os.path.join(current_directory, 'accounts.json')}"]


# Create a account.json file if not already present in current dir
user_accounts_file = os.path.join(current_directory, 'accounts.json')

if not os.path.exists(user_accounts_file):
    with open(user_accounts_file, 'w') as file:
        file.write("{}")


# Function to get the current working directory
def get_current_directory():
    """Get the current working directory.

    Returns:
        str: The current working directory.
    """
    return os.getcwd()


# Function to get the relative path of a file or directory from the current directory
def get_relative_path(path):
    """Get the relative path of a file or directory from the current directory.

    Args:
        path (str): The path to the file or directory.

    Returns:
        str: The relative path.
    """
    current_dir = get_current_directory()
    relative_path = os.path.relpath(path, start=current_dir)
    return os.path.basename(relative_path)


# Function to get the formatted date of last modification for a file
def get_file_date_modified(file_path):
    """Get the formatted date of last modification for a file.

    Args:
        file_path (str): The path to the file.

    Returns:
        str: The formatted date.
    """
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(file_path)))


# Function to get the size of a file in bytes
def get_file_size(file_path):
    """Get the size of a file in bytes.

    Args:
        file_path (str): The path to the file.

    Returns:
        int: The file size in bytes.
    """
    return os.path.getsize(file_path)


# Class representing a file or folder entry
class FileEntry:
    """Represents a file or folder entry."""
    def __init__(self, name, path, type):
        """Initialize a FileEntry object.

        Args:
            name (str): The name of the entry.
            path (str): The path to the entry.
            type (str): The type of the entry ('file' or 'folder').
        """
        self.name = name
        self.path = path
        self.type = type
        self.date_modified = get_file_date_modified(path)
        self.size = get_file_size(path)


# Function to load user accounts from the accounts.json file
def load_user_accounts():
    """Load user accounts from the accounts.json file.

    Returns:
        dict: A dictionary containing user accounts.
    """
    with open("accounts.json", "r") as accounts_file:
        return json.load(accounts_file)


user_accounts = load_user_accounts()


LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Login</title>
    <!-- Link to Font Awesome CSS -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
    <link rel="icon" href="/favicon.ico" type="image/x-icon">
    <!-- Internal CSS styles -->
    <style>
        /* Styling for the entire page */
        body {
            font-family: Arial, sans-serif;
            background-color: #d9d9d9;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }

        /* Styling for the login container */
        .login-container {
            background-color: #f5f5f5;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0px 0px 20px rgba(0, 0, 0, 0.1);
            width: 300px;
            height: 340px;
            text-align: center;
        }

        /* Styling for the login header */
        .login-header {
            text-align: center;
            margin-bottom: 20px;
            color: #0056b3;
        }

        /* Styling for login labels */
        .login-label {
            text-align: center;
            margin-bottom: 20px;
        }

        /* Styling for the login form */
        .login-form {
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        /* Styling for form groups */
        .form-group {
            margin-bottom: 15px;
            position: relative;
            width: 100%;
        }

        /* Hiding the label */
        .form-group label {
            display: none;
        }

        /* Styling for input fields */
        .form-group input {
            background-color: #f5f5f5;
            padding: 10px;
            border: 1px solid #0056b3;
            border-radius: 4px;
            width: 80%;
            transition: border-color 0.3s;
            box-sizing: border-box;
        }

        /* Styling for input focus */
        .form-group input:focus {
            border-color: #004380;
        }

        /* Styling for the show/hide password button */
        .show-hide-button {
            position: absolute;
            top: 50%;
            right: 40px;
            color: #444444;
            transform: translateY(-50%);
            cursor: pointer;
            transition: color 0.3s;
        }

        /* Styling for show/hide button hover */
        .show-hide-button:hover {
            color: #004380;
        }

        /* Styling for the login button */
        .login-button {
            background-color: #0056b3;
            color: white;
            border: none;
            padding: 10px;
            border-radius: 4px;
            cursor: pointer;
            transition: background-color 0.3s;
            width: 80%;
            font-size: 14px;
        }

        /* Styling for login button hover */
        .login-button:hover {
            background-color: #004380;
        }

        /* Styling for error messages */
        .error-message {
            color: red;
            margin-top: 10px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="login-header">
            <h1><i class="fas fa-folder-open"></i> File Server</h1>
        </div>
        <div class="login-label">
            <h1>Login</h1>
        </div>
        <form class="login-form" method="post">
            <div class="form-group">
                <input type="text" id="username" name="username" placeholder="Username" required>
            </div>
            <div class="form-group">
                <input type="password" id="password" name="password" placeholder="Password" required>
                <i class="fas fa-eye show-hide-button" id="show-hide-password"></i>
            </div>
            <button class="login-button" type="submit">Log In</button>
        </form>
        <!-- Display error message if login failed -->
        {% if login_failed %}
            <p class="error-message">Incorrect username or password. Please try again.</p>
        {% endif %}
    </div>
    <script>
        <!-- JavaScript to toggle password visibility -->
        const passwordInput = document.getElementById('password');
        const showHideButton = document.getElementById('show-hide-password');
        showHideButton.addEventListener('click', () => {
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                showHideButton.classList.remove('fa-eye');
                showHideButton.classList.add('fa-eye-slash');
            } else {
                passwordInput.type = 'password';
                showHideButton.classList.remove('fa-eye-slash');
                showHideButton.classList.add('fa-eye');
            }
        });
    </script>
</body>
</html>
'''


# Register the route to serve the favicon.ico file from the root directory
@app.route('/favicon.ico')
def serve_favicon():
    """Serve the favicon.ico file for the web application.

    This route function serves the favicon.ico file, which is a small icon
    displayed in the browser's tab or title bar. The function retrieves the
    favicon.ico file from the root directory of the Flask application and
    sends it as a response with the appropriate MIME type.

    Returns:
        Response: A Flask response object containing the favicon.ico file.
    """
    root_dir = os.path.dirname(os.path.abspath(__file__))
    return send_file(os.path.join(root_dir, 'favicon.ico'), mimetype='image/x-icon')


# Route to render the main page
@app.route('/')
def index():
    """Render the main page.

    Returns:
        str: The HTML content of the main page.
    """
    if 'logged_in' in session and session['logged_in']:
        current_dir = get_current_directory()
        files = get_files_in_directory(current_dir)
        return render_template_string(HTML_TEMPLATE, files=files, current_dir=current_dir, folder_or_file='')
    else:
        return render_template_string(LOGIN_TEMPLATE, login_failed=False)


# Route to handle file server operations
@app.route('/', methods=['POST'])
@limiter.limit("32 per minute")
def file_server():
    """Handle file server operations.

    Returns:
        str: The response HTML content.
    """
    global user_accounts

    user_accounts = load_user_accounts()

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in user_accounts and user_accounts[username] == password:
            session['logged_in'] = True
            current_dir = get_current_directory()
            files = get_files_in_directory(current_dir)
            return render_template_string(HTML_TEMPLATE, files=files, current_dir=current_dir, folder_or_file='')
        else:
            return render_template_string(LOGIN_TEMPLATE, login_failed=True)

    if 'logged_in' in session and session['logged_in']:
        current_dir = request.args.get('current_dir', '')
        files = get_files_in_directory(current_dir)
        return render_template_string(HTML_TEMPLATE, files=files, current_dir=current_dir, folder_or_file='')

    return render_template_string(LOGIN_TEMPLATE, login_failed=False)


# Route to log out the user
@app.route('/logout')
def logout():
    """Log out the user.

    Returns:
        str: The login page HTML content.
    """
    session.clear()
    return render_template_string(LOGIN_TEMPLATE, login_failed=False)


# Route to upload a file to the specified folder
@app.route('/upload/<path:folder_or_file>', methods=['POST'])
@limiter.limit("10 per minute")
def upload_file(folder_or_file):
    """Upload a file to the specified folder.

    Args:
        folder_or_file (str): The path to the folder.

    Returns:
        str: The upload status message.
    """
    if 'file' not in request.files:
        return 'No file part'

    file = request.files['file']

    if file.filename == '':
        return 'No selected file'

    current_dir = os.path.join(get_current_directory(), folder_or_file)
    uploaded_filename = file.filename

    counter = 1
    while os.path.exists(os.path.join(current_dir, uploaded_filename)):
        name, ext = os.path.splitext(file.filename)
        uploaded_filename = f"{name} ({counter}){ext}"
        counter += 1

    file.save(os.path.join(current_dir, uploaded_filename))
    return 'File uploaded successfully'


# Route to download a file
@app.route('/download/<path:file_path>')
@limiter.limit("32 per minute")
def download_file(file_path):
    """Download a file.

    Args:
        file_path (str): The path to the file.

    Returns:
        obj: The file to be downloaded.
    """
    return send_file(file_path, as_attachment=True)


# Route to display the contents of a folder or serve a file for download
@app.route('/<path:folder_or_file>')
def show_folder_or_file(folder_or_file):
    """Display the contents of a folder or serve a file for download.

    Args:
        folder_or_file (str): The path to the folder or file.

    Returns:
        str: The HTML content of the folder or file page.
    """
    folder_or_file_path = os.path.join(get_current_directory(), folder_or_file)
    return_text = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>File Not Found (404)</title>
        <link rel="icon" href="/favicon.ico" type="image/x-icon">
        <style>
            /* Styling for the entire page */
            body {
                font-family: Arial, sans-serif;
                background-color: #d9d9d9;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                text-align: center;
            }

            /* Styling for the main heading */
            h1 {
                font-size: 36px;
                color: #333;
                margin-bottom: 20px;
            }

            /* Styling for the paragraph */
            p {
                font-size: 18px;
                color: #777;
                margin-bottom: 30px;
            }

            /* Styling for the button */
            .btn {
                display: inline-block;
                background-color: #0056b3;
                color: #fff;
                font-size: 16px;
                padding: 10px 20px;
                border-radius: 5px;
                text-decoration: none;
                transition: background-color 0.3s ease;
            }

            /* Styling for the button hover state */
            .btn:hover {
                background-color: #0056b3;
            }
        </style>
    </head>
    <body>
        <div>
            <!-- Main heading -->
            <h1>404 - File Not Found</h1>
            <!-- Paragraph explaining the issue -->
            <p>The file you requested doesn't exist.</p>
            <!-- Button to go back -->
            <a href="javascript:history.back()" class="btn">Go Back</a>
        </div>
    </body>
    </html>
    """
    if os.path.exists(folder_or_file_path):
        if os.path.isdir(folder_or_file_path):
            files = get_files_in_directory(folder_or_file_path)
            current_dir = folder_or_file_path
            return render_template_string(HTML_TEMPLATE, files=files, current_dir=current_dir, folder_or_file=folder_or_file)

        if folder_or_file_path in ignore_files:
            return return_text

        return send_file(folder_or_file_path, as_attachment=True)

    return return_text


# Function to get a list of file and folder entries in a directory
def get_files_in_directory(directory):
    """Get a list of file and folder entries in a directory.

    Args:
        directory (str): The directory path.

    Returns:
        list: A list of FileEntry objects representing the entries.
    """
    files_and_folders = []
    if os.path.exists(directory) and os.path.isdir(directory):
        for entry in os.listdir(directory):
            entry_path = os.path.join(directory, entry)
            if os.path.isfile(entry_path) and entry_path not in ignore_files:
                files_and_folders.append(FileEntry(entry, entry_path, 'file'))
            elif os.path.isdir(entry_path):
                files_and_folders.append(FileEntry(entry, entry_path, 'folder'))
    return files_and_folders


# Function to get the directory name from a path
def dirname(path):
    """Get the directory name from a path.

    Args:
        path (str): The path.

    Returns:
        str: The directory name.
    """
    return os.path.dirname(path)


# Function to get the base name of a path
def os_path_basename(path):
    """Get the base name of a path.

    Args:
        path (str): The path.

    Returns:
        str: The base name.
    """
    return os.path.basename(path)


HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>File Server</title>
    <link rel="icon" href="/favicon.ico" type="image/x-icon">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #d9d9d9;
            color: #333;
            margin: 20px;
            padding: 0;
        }
        h1 {
            font-size: 40px;
            color: #0056b3;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
        }
        .btn {
            background-color: #0056b3;
            color: white;
            padding: 10px 20px;
            border: none;
            cursor: pointer;
            font-size: 14px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            margin: 5px;
            border-radius: 4px;
            transition: background-color 0.3s ease-in-out;
        }
        .btn:hover {
            background-color: #004380;
        }
        .file-input {
            display: none;
        }
        .go-back-root {
            margin-top: 10px;
        }
        .current-dir-text {
            font-size: 18px;
            color: #666;
        }
        .current-dir-container {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-top: 10px;
            border-bottom: 1px solid #ddd;
            padding-bottom: 10px;
        }
        .file-name {
            font-size: 14px;
            margin-top: 10px;
        }
        .table-container {
            width: 100%;
            margin-top: 20px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background-color: #fff;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            border-radius: 8px;
            overflow: hidden;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #0056b3;
            color: white;
            font-weight: bold;
            text-transform: uppercase;
            font-size: 14px;
        }
        td {
            font-size: 14px;
            background-color: #e9e9e9;
        }
        td a {
            color: #0056b3;
            text-decoration: none;
            transition: color 0.3s ease-in-out;
        }
        td a:hover {
            color: #004380;
        }
        .table-container p {
            font-size: 18px;
            color: #777;
            text-align: center;
            margin: 20px 0;
        }
        .upload-container {
            display: flex;
            align-items: center;
            margin-bottom: 5px;
        }
        .upload-container .btn {
            background-color: #2dbb56;
            margin-right: 10px;
        }
        .file-name-display {
            color: #2dbb56;
            font-weight: bold;
        }
        .go-back-root .btn i {
            margin-right: 5px;
        }
        ::-webkit-scrollbar {
            width: 8px;
        }
        ::-webkit-scrollbar-track {
            background-color: #f1f1f1;
        }
        ::-webkit-scrollbar-thumb {
            background-color: #0056b3;
            border-radius: 4px;
        }
        .logout-btn {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 50px;
            height: 50px;
            display: flex;
            align-items: center;
            justify-content: center;
            background-color: #0056b3;
            color: white;
            border-radius: 50%;
            font-size: 24px;
            text-decoration: none;
            transition: background-color 0.3s ease-in-out;
        }
        .logout-btn:hover {
            background-color: #004380;
        }
        @media (max-width: 768px) {
            table {
                width: 100%;
            }
            th:nth-child(2),
            td:nth-child(2),
            th:nth-child(3),
            td:nth-child(3) {
                display: none;
            }
            th:nth-child(1),
            td:nth-child(1) {
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <h1><i class="fas fa-folder-open"></i> File Server</h1>
    <div class="upload-container">
        <form action="{{ url_for('upload_file', folder_or_file=current_dir) }}" method="post" enctype="multipart/form-data">
            <label for="file-input" class="btn"><i class="fas fa-file-upload"></i> Choose File</label>
            <input type="file" id="file-input" name="file" class="file-input">
            <button type="submit" class="btn" id="upload-btn"><i class="fas fa-cloud-upload-alt"></i> Upload</button>
        </form>
        <div class="file-name-display"></div>
    </div>
    <div class="current-dir-container">
        <div class="go-back-root">
            {% if current_dir != '.' %}
                <a class="btn" href="{{ url_for('show_folder_or_file', folder_or_file=os.path.dirname(folder_or_file)) }}"><i class="fas fa-chevron-left"></i> Go back</a>
            {% endif %}
            <a class="btn" href="{{ url_for('index') }}"><i class="fas fa-home"></i> Root</a>
        </div>
        <h2>
            <span class="current-dir-text"><i class="fas fa-folder"></i> Current Directory: \{{ folder_or_file }}</span>
        </h2>
    </div>
    <div class="table-container">
        {% if is_empty %}
            <p>Folder is empty.</p>
        {% else %}
            <table>
                <tr>
                    <th>Name</th>
                    <th>Date Modified</th>
                    <th>Size</th>
                </tr>
                {% for entry in files %}
                    <tr>
                        <td>
                            {% if entry.type == 'folder' %}
                                <a href="{{ url_for('show_folder_or_file', folder_or_file=os.path.join(folder_or_file, entry.name)) }}"><i class="fas fa-folder"></i> {{ entry.name }}</a>
                            {% else %}
                                <a href="{{ url_for('download_file', file_path=entry.path) }}"><i class="fas fa-file"></i> {{ entry.name }}</a>
                            {% endif %}
                        </td>
                        <td>{{ entry.date_modified }}</td>
                        <td>{{ entry.size }}</td>
                    </tr>
                {% endfor %}
            </table>
        {% endif %}
    </div>
    <a href="{{ url_for('logout') }}" class="logout-btn" id="logout-link"><i class="fas fa-power-off"></i></a>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/js/all.min.js"></script>
    <script>
        // Get references to DOM elements
        const fileInput = document.getElementById('file-input');
        const fileNameDisplay = document.querySelector('.file-name-display');
        const uploadBtn = document.getElementById('upload-btn');
        let selectedFile = null;

        // Listen for changes in the file input
        fileInput.addEventListener('change', () => {
            const file = fileInput.files[0];
            if (file) {
                selectedFile = file;
                uploadBtn.textContent = `Upload ${file.name}`;
            } else {
                selectedFile = null;
                uploadBtn.textContent = 'Upload';
            }
        });

        // Display a temporary message on the upload button
        function showTempMessage(message) {
            uploadBtn.textContent = message;
            setTimeout(() => {
                uploadBtn.textContent = 'Upload';
            }, 2000);
        }

        // Handle form submission (uploading a file)
        const form = document.querySelector('form');
        form.addEventListener('submit', async (event) => {
            event.preventDefault();
            if (selectedFile) {
                const formData = new FormData(form);
                formData.set('file', selectedFile);
                const uploadUrl = '{{ url_for("upload_file", folder_or_file=current_dir) }}';
                try {
                    uploadBtn.textContent = 'Uploading...';
                    const response = await fetch(uploadUrl, {
                        method: 'POST',
                        body: formData,
                    });
                    if (response.ok) {
                        showTempMessage('Upload successful...');
                        selectedFile = null;
                        fileInput.value = '';
                        fileNameDisplay.textContent = '';
                    } else {
                        showTempMessage('Upload failed...');
                    }
                } catch (error) {
                    showTempMessage('Upload failed...');
                }
            }
        });

        // Handle user logout
        const logoutLink = document.getElementById('logout-link');
        logoutLink.addEventListener('click', () => {
            fetch('{{ url_for('logout') }}')
                .then(() => {
                    window.location.href = '{{ url_for('index') }}';
                })
                .catch((error) => {
                    console.error('Logout error:', error);
                });
        });
    </script>
</body>
</html>
'''


app.jinja_env.globals['os'] = os
app.jinja_env.filters['dirname'] = dirname
app.jinja_env.filters['basename'] = os_path_basename


# Run the app on the specified host and port in a seperate thread
class ServerThread(threading.Thread):
    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port

    def run(self):
        serve(app, host=self.host, port=self.port)


# Run the app on the specified host and port for debuging
if __name__=="__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
