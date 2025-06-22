LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>QuickServe | Access Portal</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --accent-1: #5A3D68;
            --accent-2: #7A6A82;
            --accent-3: #B8A9B8;
            --base: #F3EEF1;
            --text: #252225;
            --error: #B03A28;
            --input-border: #A895A8;
        }
        body {
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Roboto, Oxygen, sans-serif;
            background: linear-gradient(135deg, var(--accent-3) 0%, var(--base) 50%, var(--accent-3) 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            background-size: 400% 400%;
            animation: gradientBG 15s ease infinite;
        }
        @keyframes gradientBG {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        .access-panel {
            width: 90%;
            max-width: 380px;
            background: rgba(247, 243, 245, 0.85);
            backdrop-filter: blur(10px);
            border-radius: 18px;
            box-shadow: 
                0 4px 6px rgba(0, 0, 0, 0.1),
                0 10px 20px rgba(0, 0, 0, 0.15),
                0 20px 40px rgba(0, 0, 0, 0.2),
                inset 0 0 0 1px rgba(255, 255, 255, 0.4);
            overflow: hidden;
            position: relative;
            z-index: 1;
        }
        .access-panel::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            border-radius: 18px;
            box-shadow: 
                inset 0 1px 1px rgba(255, 255, 255, 0.8),
                inset 0 -1px 1px rgba(0, 0, 0, 0.05);
            pointer-events: none;
            z-index: -1;
        }
        .panel-header {
            background: linear-gradient(to right, var(--accent-1), var(--accent-2));
            padding: 25px;
            text-align: center;
            color: white;
            position: relative;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        .panel-header::after {
            content: '';
            position: absolute;
            bottom: -15px;
            left: 50%;
            transform: translateX(-50%);
            width: 30px;
            height: 30px;
            background: var(--base);
            clip-path: polygon(0% 0%, 100% 0%, 50% 50%);
            filter: drop-shadow(0 -2px 2px rgba(0,0,0,0.1));
        }
        .panel-header i {
            font-size: 2.2rem;
            margin-bottom: 10px;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
        }
        .panel-header h1 {
            margin: 0;
            font-weight: 600;
            letter-spacing: 0.5px;
        }
        .auth-form {
            padding: 30px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .input-group {
            width: 90%;
            max-width: 342px;
            position: relative;
            margin-bottom: 20px;
        }
        .input-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            color: var(--accent-1);
            font-size: 0.9rem;
        }
        .input-group input {
            width: 100%;
            padding: 10px 40px 10px 16px;
            border: 1px solid var(--input-border);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.9);
            font-size: 0.95rem;
            box-shadow: 
                inset 0 1px 3px rgba(0,0,0,0.05),
                0 1px 0 rgba(255,255,255,0.8);
            transition: all 0.3s ease;
            box-sizing: border-box;
            height: 42px;
        }
        .input-group input:focus {
            outline: none;
            border-color: var(--accent-1);
            background: white;
            box-shadow: 
                0 0 0 2px rgba(108, 77, 123, 0.2),
                0 2px 6px rgba(108, 77, 123, 0.1);
        }
        .toggle-pw {
            position: absolute;
            right: 12px;
            top: 70%;
            transform: translateY(-50%);
            color: var(--accent-2);
            cursor: pointer;
            background: none;
            border: none;
            font-size: 1rem;
            padding: 0;
            width: 24px;
            height: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .toggle-pw:hover {
            color: var(--accent-1);
        }
        .submit-btn {
            width: 90%;
            max-width: 342px;
            padding: 12px;
            border: none;
            border-radius: 8px;
            background: linear-gradient(to right, var(--accent-1), var(--accent-2));
            color: white;
            font-weight: 600;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 8px rgba(108, 77, 123, 0.3);
            margin-top: 10px;
        }
        .submit-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(108, 77, 123, 0.4);
        }
        .error-msg {
            width: 90%;
            max-width: 342px;
            color: var(--error);
            font-size: 0.85rem;
            text-align: center;
            padding: 10px;
            background: rgba(200, 70, 48, 0.1);
            border-radius: 8px;
            margin: 5px 0 15px 0;
        }
        .footer-note {
            width: 90%;
            max-width: 342px;
            text-align: center;
            font-size: 0.8rem;
            color: var(--accent-2);
            margin-top: 15px;
        }
    </style>
</head>
<body>
    <div class="access-panel">
        <div class="panel-header"><i class="fas fa-shield-alt"></i><h1>Secure Access</h1></div>
        <form class="auth-form" method="post">
            <div class="input-group">
                <label for="username">USERNAME</label>
                <input type="text" id="username" name="username" required>
            </div>
            <div class="input-group">
                <label for="password">PASSWORD</label>
                <input type="password" id="password" name="password" required>
                <button type="button" class="toggle-pw" id="togglePassword"><i class="fas fa-eye"></i></button>
            </div>
            {% if login_failed %}<div class="error-msg">Authentication failed. Please try again.</div>{% endif %}
            <button type="submit" class="submit-btn">AUTHENTICATE</button>
            <div class="footer-note">Restricted access to authorized personnel only</div>
        </form>
    </div>
    <script>
        const togglePassword = document.getElementById('togglePassword');
        const password = document.getElementById('password');
        const icon = togglePassword.querySelector('i');
        // Toggle password visibility
        togglePassword.addEventListener('click', function() {
            const type = password.getAttribute('type') === 'password' ? 'text' : 'password';
            password.setAttribute('type', type);
            icon.classList.toggle('fa-eye-slash');
        });
    </script>
</body>
</html>
"""

HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>QuickServe | File Server</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --accent-1: #5A3D68;
            --accent-2: #7A6A82;
            --accent-3: #B8A9B8;
            --base: #F3EEF1;
            --text: #252225;
            --error: #B03A28;
            --success: #2dbb56;
            --shadow-sm: 0 2px 4px rgba(0,0,0,0.1);
            --shadow-md: 0 4px 8px rgba(0,0,0,0.15);
            --shadow-lg: 0 8px 16px rgba(0,0,0,0.2);
        }
        body {
            margin: 0;
            padding: 20px;
            font-family: 'Segoe UI', Roboto, Oxygen, sans-serif;
            background: linear-gradient(135deg, var(--accent-3) 0%, var(--base) 50%, var(--accent-3) 100%);
            background-size: 400% 400%;
            animation: gradientBG 15s ease infinite;
            color: var(--text);
            min-height: 100vh;
        }
        @keyframes gradientBG {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        .main-container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(247, 243, 245, 0.85);
            backdrop-filter: blur(10px);
            border-radius: 18px;
            box-shadow: var(--shadow-lg);
            padding: 30px;
            position: relative;
            overflow: hidden;
        }
        .main-container::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            border-radius: 18px;
            box-shadow: 
                inset 0 1px 1px rgba(255, 255, 255, 0.8),
                inset 0 -1px 1px rgba(0, 0, 0, 0.05);
            pointer-events: none;
            z-index: -1;
        }
        .header {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 25px;
            color: var(--accent-1);
        }
        .header i {
            font-size: 2.5rem;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
        }
        .header h1 {
            margin: 0;
            font-weight: 600;
            letter-spacing: 0.5px;
        }
        .upload-container {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 25px;
            flex-wrap: wrap;
        }
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 12px 20px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s ease;
            border: none;
            text-decoration: none;
            gap: 8px;
            box-shadow: var(--shadow-sm);
        }
        .btn-primary {
            background: linear-gradient(to right, var(--accent-1), var(--accent-2));
            color: white;
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }
        .btn-success {
            background: var(--success);
            color: white;
        }
        .btn-success:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }
        .btn-secondary {
            background: var(--accent-3);
            color: var(--text);
        }
        .btn-secondary:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }
        .file-input {
            display: none;
        }
        .file-name-display {
            color: var(--success);
            font-weight: 600;
            font-size: 0.95rem;
        }
        .current-dir-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid var(--accent-3);
            flex-wrap: wrap;
            gap: 15px;
        }
        .current-dir-text {
            font-size: 1.1rem;
            color: var(--accent-1);
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .table-container {
            width: 100%;
            margin-top: 20px;
            overflow-x: auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background: rgba(255, 255, 255, 0.9);
            box-shadow: var(--shadow-sm);
            border-radius: 12px;
            overflow: hidden;
        }
        th, td {
            padding: 14px 16px;
            text-align: left;
            border-bottom: 1px solid var(--accent-3);
        }
        th {
            background: linear-gradient(to right, var(--accent-1), var(--accent-2));
            color: white;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85rem;
            letter-spacing: 0.5px;
        }
        td {
            font-size: 0.95rem;
        }
        td a {
            color: var(--accent-1);
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s ease;
        }
        td a:hover {
            color: var(--accent-2);
            text-decoration: underline;
        }
        .empty-state {
            text-align: center;
            padding: 40px 20px;
            color: var(--accent-2);
            font-size: 1.1rem;
        }
        .empty-state i {
            font-size: 2.5rem;
            margin-bottom: 15px;
            color: var(--accent-3);
        }
        .logout-btn {
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 60px;
            height: 60px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(to right, var(--accent-1), var(--accent-2));
            color: white;
            border-radius: 50%;
            font-size: 1.5rem;
            text-decoration: none;
            transition: all 0.3s ease;
            box-shadow: var(--shadow-md);
            z-index: 100;
        }
        .logout-btn:hover {
            transform: translateY(-3px) scale(1.05);
            box-shadow: var(--shadow-lg);
        }
        @media (max-width: 768px) {
            .main-container {
                padding: 20px;
            }
            th:nth-child(2),
            td:nth-child(2),
            th:nth-child(3),
            td:nth-child(3) {
                display: none;
            }
            .logout-btn {
                width: 50px;
                height: 50px;
                font-size: 1.2rem;
                bottom: 20px;
                right: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="main-container">
        <div class="header">
            <i class="fas fa-folder-open"></i>
            <h1>QuickServe File Server</h1>
        </div>
        <div class="upload-container">
            <form action="{{ url_for('upload_file', folder_or_file=current_dir) }}" method="post" enctype="multipart/form-data">
                <label for="file-input" class="btn btn-primary">
                    <i class="fas fa-file-upload"></i> Choose File
                </label>
                <input type="file" id="file-input" name="file" class="file-input">
                <button type="submit" class="btn btn-success" id="upload-btn">
                    <i class="fas fa-cloud-upload-alt"></i> Upload
                </button>
            </form>
            <div class="file-name-display"></div>
        </div>
        <div class="current-dir-container">
            <div class="navigation-buttons">
                {% if current_dir != '.' %}
                    <a class="btn btn-secondary" href="{{ url_for('show_folder_or_file', folder_or_file=os.path.dirname(folder_or_file)) }}">
                        <i class="fas fa-chevron-left"></i> Go Back
                    </a>
                {% endif %}
                <a class="btn btn-secondary" href="{{ url_for('index') }}">
                    <i class="fas fa-home"></i> Root
                </a>
            </div>
            <div class="current-dir-text">
                <i class="fas fa-folder"></i> {{ folder_or_file }}
            </div>
        </div>
        <div class="table-container">
            {% if is_empty %}
                <div class="empty-state">
                    <i class="fas fa-folder-open"></i>
                    <p>This folder is empty</p>
                </div>
            {% else %}
                <table>
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Date Modified</th>
                            <th>Size</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for entry in files %}
                            <tr>
                                <td>
                                    {% if entry.type == 'folder' %}
                                        <a href="{{ url_for('show_folder_or_file', folder_or_file=os.path.join(folder_or_file, entry.name)) }}">
                                            <i class="fas fa-folder"></i> {{ entry.name }}
                                        </a>
                                    {% else %}
                                        <a href="{{ url_for('download_file', file_path=entry.path) }}">
                                            <i class="fas fa-file"></i> {{ entry.name }}
                                        </a>
                                    {% endif %}
                                </td>
                                <td>{{ entry.date_modified }}</td>
                                <td>{{ entry.size }}</td>
                            </tr>
                        {% endfor %}
                    </tbody>
                </table>
            {% endif %}
        </div>
    </div>
    <a href="{{ url_for('logout') }}" class="logout-btn" id="logout-link">
        <i class="fas fa-power-off"></i>
    </a>
    <script>
        const fileInput = document.getElementById('file-input');
        const fileNameDisplay = document.querySelector('.file-name-display');
        const uploadBtn = document.getElementById('upload-btn');
        let selectedFile = null;

        fileInput.addEventListener('change', () => {
            const file = fileInput.files[0];
            if (file) {
                selectedFile = file;
                fileNameDisplay.textContent = `Selected: ${file.name}`;
                uploadBtn.innerHTML = `<i class="fas fa-cloud-upload-alt"></i> Upload ${file.name}`;
            } else {
                selectedFile = null;
                fileNameDisplay.textContent = '';
                uploadBtn.innerHTML = '<i class="fas fa-cloud-upload-alt"></i> Upload';
            }
        });

        function showTempMessage(message) {
            const originalText = uploadBtn.innerHTML;
            uploadBtn.innerHTML = `<i class="fas fa-spinner fa-pulse"></i> ${message}`;
            setTimeout(() => {
                uploadBtn.innerHTML = originalText;
            }, 2000);
        }

        const form = document.querySelector('form');
        form.addEventListener('submit', async (event) => {
            event.preventDefault();
            if (selectedFile) {
                const formData = new FormData(form);
                formData.set('file', selectedFile);
                const uploadUrl = '{{ url_for("upload_file", folder_or_file=current_dir) }}';
                try {
                    showTempMessage('Uploading...');
                    const response = await fetch(uploadUrl, {
                        method: 'POST',
                        body: formData,
                    });
                    if (response.ok) {
                        showTempMessage('Uploaded!');
                        selectedFile = null;
                        fileInput.value = '';
                        fileNameDisplay.textContent = '';
                        setTimeout(() => {
                            window.location.reload();
                        }, 1000);
                    } else {
                        showTempMessage('Failed!');
                    }
                } catch (error) {
                    showTempMessage('Failed!');
                }
            }
        });

        const logoutLink = document.getElementById('logout-link');
        logoutLink.addEventListener('click', (e) => {
            e.preventDefault();
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
"""

ERROR_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>QuickServe | Error</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --accent-1: #5A3D68;
            --accent-2: #7A6A82;
            --accent-3: #B8A9B8;
            --base: #F3EEF1;
            --text: #252225;
            --error: #B03A28;
        }
        body {
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Roboto, Oxygen, sans-serif;
            background: linear-gradient(135deg, var(--accent-3) 0%, var(--base) 50%, var(--accent-3) 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            background-size: 400% 400%;
            animation: gradientBG 15s ease infinite;
        }
        @keyframes gradientBG {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        .error-panel {
            width: 90%;
            max-width: 420px;
            background: rgba(247, 243, 245, 0.85);
            backdrop-filter: blur(10px);
            border-radius: 18px;
            box-shadow: 
                0 4px 6px rgba(0, 0, 0, 0.1),
                0 10px 20px rgba(0, 0, 0, 0.15),
                0 20px 40px rgba(0, 0, 0, 0.2),
                inset 0 0 0 1px rgba(255, 255, 255, 0.4);
            overflow: hidden;
            position: relative;
            z-index: 1;
            text-align: center;
            padding: 40px 30px;
        }
        .error-panel::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            border-radius: 18px;
            box-shadow: 
                inset 0 1px 1px rgba(255, 255, 255, 0.8),
                inset 0 -1px 1px rgba(0, 0, 0, 0.05);
            pointer-events: none;
            z-index: -1;
        }
        .error-icon {
            font-size: 3.5rem;
            color: var(--error);
            margin-bottom: 20px;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
        }
        .error-title {
            font-size: 2rem;
            color: var(--accent-1);
            margin: 0 0 15px 0;
            font-weight: 600;
        }
        .error-message {
            font-size: 1.1rem;
            color: var(--text);
            margin-bottom: 30px;
            line-height: 1.5;
        }
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 12px 24px;
            border-radius: 8px;
            background: linear-gradient(to right, var(--accent-1), var(--accent-2));
            color: white;
            font-weight: 600;
            font-size: 1rem;
            text-decoration: none;
            transition: all 0.3s ease;
            box-shadow: 0 4px 8px rgba(90, 61, 104, 0.3);
            border: none;
            cursor: pointer;
            gap: 8px;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(90, 61, 104, 0.4);
        }
        .btn:active {
            transform: translateY(0);
        }
    </style>
</head>
<body>
    <div class="error-panel">
        <div class="error-icon"><i class="fas fa-exclamation-triangle"></i></div>
        <h1 class="error-title">404 - File Not Found</h1>
        <p class="error-message">The file you requested doesn't exist or is no longer available.</p>
        <button onclick="history.back()" class="btn"><i class="fas fa-arrow-left"></i> Go Back</button>
    </div>
</body>
</html>
"""
