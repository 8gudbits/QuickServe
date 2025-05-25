# pyFlaskyServe: A Server to Serve files fresh from your disk.

## Introduction

- Be the server, share files fresh from your disk, with unlimited space and bandwidth.
- No intermediaries—give a huge file to your friend without waiting for it to be uploaded to a server first.

## Features

- User authentication using username and password
- Browse files and directories on the server
- Upload files to the server
- Download files from the server
- Built-in basic anti-DDoS protection
- Includes a simple PyQt5 GUI

## Installation

![Static Badge](https://img.shields.io/badge/Version-v1.0-blue)

#### Get the latest release for windows from here. [[Version-v1.0]](https://github.com/8gudbits/pyFlaskyServe/releases)

  - **or:**

1. Clone the repository:

   ```bash
   git clone https://github.com/8gudbits/pyFlaskyServe.git
   ```

2. Install the required dependencies using pip:

   ```bash
   pip install Flask Flask-Limiter PyQt5
   ```

3. Run the application:

- For command-line interface (CLI) access (for debuging):

  ```bash
  python pyFlaskyServe.py
  ```

- For graphical user interface (GUI) access:

  ```bash
  python FlaskyServeGUI.py
  ```

4. Open your web browser and navigate to `http://localhost:5000` (or any other port if you are using the GUI) to access the file server.

## Usage

To get started, simply open the accounts.json file and create user accounts with usernames and passwords like this:

```json
{
  "username_1":"superstrongpasswd",
  "username_2":"passwordforthisuser",
  "username_3":"anotherexamplepasswd"
}
```

- The login page allows users to authenticate using their username and password.
- After logging in, users can browse and manage files and directories on the server.
- Use the "Choose File" button to upload files to the server.
- Click on a folder name to navigate into that folder.
- Click on a file name to download the file.
- Use the "Go back" button to navigate to the parent directory.
- Use the "Root" button to navigate back to the root directory.
- Click on the circular logout button to log out of the application.

## Screenshots

<img src="https://github.com/8gudbits/pyFlaskyServe/blob/main/Preview/login_page.png?raw=true" alt="Login page"><br>
<img src="https://github.com/8gudbits/pyFlaskyServe/blob/main/Preview/file_server.png?raw=true" alt="File server">

## License

This project is licensed under the [MIT License](https://github.com/8gudbits/pyFlaskyServe/blob/main/LICENSE).

---

Built with ❤️ using Python and Flask.
