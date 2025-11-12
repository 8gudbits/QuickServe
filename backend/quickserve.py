import os
import time
import json
import sys
import uvicorn
import bcrypt
import socket

from fastapi import FastAPI, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List


class QuickServe:
    def __init__(self):
        self.app = FastAPI(title="QuickServe API", version="2.0")
        self._setup_paths()
        self._load_config()
        self._setup_cors()
        self._setup_routes()

    def _setup_paths(self):
        if getattr(sys, "frozen", False):
            self.current_directory = os.path.dirname(sys.executable)
        else:
            self.current_directory = os.path.dirname(os.path.abspath(__file__))

        self.config_file = os.path.join(self.current_directory, "config.json")
        self.SERVER_ROOT = os.getcwd()

    def _load_config(self):
        if not os.path.exists(self.config_file):
            raise SystemExit(
                "Configuration file not found. Please run qconfig command first."
            )

        try:
            with open(self.config_file, "r") as file:
                self.config = json.load(file)
        except json.JSONDecodeError:
            raise SystemExit("Invalid configuration in config.json")

        self.port = self.config.get("port", 5000)
        self.allow_origins = self.config.get("allow_origins", ["*"])

    def _setup_cors(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.allow_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_routes(self):
        self.app.post("/api/login")(self.login)
        self.app.get("/api/files")(self.list_files)
        self.app.get("/api/download")(self.download_file)
        self.app.post("/api/upload")(self.upload_file)
        self.app.get("/api/health")(self.health_check)
        self.app.get("/api/config")(self.get_config)

    def get_local_ip(self):
        """Get the local IP address of the current machine"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except:
            try:
                hostname = socket.gethostname()
                return socket.gethostbyname(hostname)
            except:
                return "Unable to determine IP"

    def get_navigation_path(self, absolute_path):
        try:
            rel_path = os.path.relpath(absolute_path, self.SERVER_ROOT)
            if rel_path.startswith("..") or rel_path == ".":
                return ""
            nav_path = rel_path.replace("\\", "/")
            return nav_path if nav_path != "." else ""
        except ValueError:
            return ""

    def get_absolute_path(self, nav_path):
        if not nav_path:
            return self.SERVER_ROOT

        absolute_path = os.path.join(self.SERVER_ROOT, nav_path)
        if not absolute_path.startswith(self.SERVER_ROOT):
            raise ValueError("Path traversal detected")
        return absolute_path

    def get_parent_navigation_path(self, nav_path):
        if not nav_path:
            return ""
        parts = nav_path.split("/")
        if len(parts) <= 1:
            return ""
        return "/".join(parts[:-1])

    def get_files_in_directory(self, nav_path):
        folders = []
        files = []

        try:
            absolute_path = self.get_absolute_path(nav_path)

            if os.path.exists(absolute_path) and os.path.isdir(absolute_path):
                for entry in sorted(os.listdir(absolute_path), key=lambda x: x.lower()):
                    entry_path = os.path.join(absolute_path, entry)
                    entry_nav_path = self.get_navigation_path(entry_path)

                    if os.path.isdir(entry_path):
                        folders.append(
                            FileEntry(
                                name=entry,
                                path=entry_nav_path,
                                type="folder",
                                date_modified=self.get_file_date_modified(entry_path),
                                size=self.get_file_size(entry_path),
                            )
                        )
                    elif os.path.isfile(entry_path):
                        files.append(
                            FileEntry(
                                name=entry,
                                path=entry_nav_path,
                                type="file",
                                date_modified=self.get_file_date_modified(entry_path),
                                size=self.get_file_size(entry_path),
                            )
                        )
        except ValueError:
            return []

        return folders + files

    def get_file_date_modified(self, file_path):
        return time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(file_path))
        )

    def get_file_size(self, file_path):
        return os.path.getsize(file_path)

    def authenticate_user(self, username: str, password_sha256: str):
        users = self.config.get("users", {})
        if username not in users:
            return False

        stored_hash = users[username]
        try:
            return bcrypt.checkpw(password_sha256.encode(), stored_hash.encode())
        except:
            return False

    async def login(self, login_data: LoginRequest):
        if self.authenticate_user(login_data.username, login_data.password):
            return {"status": "success", "message": "Login successful"}
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    async def list_files(self, path: str = ""):
        try:
            absolute_path = self.get_absolute_path(path)

            if not os.path.exists(absolute_path) or not os.path.isdir(absolute_path):
                raise HTTPException(status_code=404, detail="Directory not found")

            files = self.get_files_in_directory(path)
            current_dir_nav = self.get_navigation_path(absolute_path)
            parent_dir_nav = self.get_parent_navigation_path(current_dir_nav)

            return DirectoryResponse(
                current_dir=current_dir_nav, parent_dir=parent_dir_nav, files=files
            )
        except ValueError:
            raise HTTPException(status_code=403, detail="Access denied")

    async def download_file(self, file_path: str):
        try:
            absolute_path = self.get_absolute_path(file_path)

            if not os.path.exists(absolute_path) or not os.path.isfile(absolute_path):
                raise HTTPException(status_code=404, detail="File not found")

            filename = os.path.basename(absolute_path)
            return FileResponse(
                absolute_path, media_type="application/octet-stream", filename=filename
            )
        except ValueError:
            raise HTTPException(status_code=403, detail="Access denied")

    async def upload_file(self, path: str = Form(...), file: UploadFile = File(...)):
        try:
            absolute_path = self.get_absolute_path(path)

            if not os.path.exists(absolute_path) or not os.path.isdir(absolute_path):
                raise HTTPException(status_code=404, detail="Directory not found")

            file_path = os.path.join(absolute_path, file.filename)
            counter = 1
            while os.path.exists(file_path):
                name, ext = os.path.splitext(file.filename)
                new_filename = f"{name} ({counter}){ext}"
                file_path = os.path.join(absolute_path, new_filename)
                counter += 1

            try:
                contents = await file.read()
                with open(file_path, "wb") as f:
                    f.write(contents)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

            return {
                "status": "success",
                "message": "File uploaded successfully",
                "filename": os.path.basename(file_path),
            }
        except ValueError:
            raise HTTPException(status_code=403, detail="Access denied")

    async def health_check(self):
        return {"status": "healthy", "service": "QuickServe API"}

    async def get_config(self):
        return {
            "port": self.config.get("port", 5000),
            "users_count": len(self.config.get("users", {})),
            "allow_origins": self.config.get("allow_origins", ["*"]),
        }

    def run(self):
        local_ip = self.get_local_ip()

        print("=" * 60)
        print("QUICKSERVE FILE SERVER")
        print("=" * 60)
        print(f"PORT:            {self.port}")
        print(f"ROOT DIRECTORY:  {self.SERVER_ROOT}")
        print(f"CORS ORIGINS:    {self.allow_origins}")
        print("-" * 60)
        print("ACCESS URLs:")
        print(f"Local:           http://localhost:{self.port}")
        print(f"Network:         http://0.0.0.0:{self.port}")
        if local_ip != "Unable to determine IP":
            print(f"Local Network:   http://{local_ip}:{self.port}")
        print("-" * 60)
        print("Use the Local URL for access from this machine")
        print("Use the Local Network URL for access from other devices")
        print("on the same network")
        print("=" * 60)

        log_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "loggers": {
                "uvicorn": {"level": "WARNING", "handlers": []},
                "uvicorn.error": {"level": "WARNING", "handlers": []},
                "uvicorn.access": {"level": "WARNING", "handlers": []},
            },
        }

        uvicorn.run(
            self.app,
            host="0.0.0.0",
            port=self.port,
            log_config=log_config,
            access_log=False,
        )


class LoginRequest(BaseModel):
    username: str
    password: str


class FileEntry(BaseModel):
    name: str
    path: str
    type: str
    date_modified: str
    size: int


class DirectoryResponse(BaseModel):
    current_dir: str
    parent_dir: str
    files: List[FileEntry]


if __name__ == "__main__":
    try:
        server = QuickServe()
        server.run()
    except SystemExit as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

