import os
import time
import json
import sys
import uvicorn
import bcrypt
import socket
import fnmatch
import mimetypes
import shutil
import zipfile
import io

from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

APPNAME = "QuickServe API"
VERSION = "3.2.0-rc5"


class BruteForceProtection:
    def __init__(self, config: Dict):
        self.enabled = config.get("enabled", True)
        self.max_attempts_before_cooldown = config.get("max_attempts_before_cooldown", 3)
        self.initial_cooldown = config.get("initial_cooldown", 10)
        self.cooldown_increment = config.get("cooldown_increment", 10)
        self.max_attempts_before_lockout = config.get("max_attempts_before_lockout", 10)
        self.lockout_duration = config.get("lockout_duration", 86400)
        self.failed_attempts = {}
        self.lockouts = {}

    def is_locked(self, username: str) -> tuple[bool, str]:
        if not self.enabled:
            return False, ""
        if username in self.lockouts:
            lock_time, attempts = self.lockouts[username]
            if time.time() - lock_time < self.lockout_duration:
                remaining = int(self.lockout_duration - (time.time() - lock_time))
                hours = remaining // 3600
                minutes = (remaining % 3600) // 60
                return True, f"Account locked for {hours}h {minutes}m due to too many failed attempts"
            else:
                del self.lockouts[username]
                if username in self.failed_attempts:
                    del self.failed_attempts[username]
        return False, ""

    def record_failed_attempt(self, username: str) -> tuple[bool, str]:
        if not self.enabled:
            return False, ""
        if username not in self.failed_attempts:
            self.failed_attempts[username] = {
                "attempts": 0,
                "last_attempt": 0,
                "cooldown_until": 0,
            }
        data = self.failed_attempts[username]
        current_time = time.time()
        if current_time < data["cooldown_until"]:
            remaining = int(data["cooldown_until"] - current_time)
            return True, f"Please wait {remaining} seconds before trying again"
        data["attempts"] += 1
        data["last_attempt"] = current_time
        if data["attempts"] >= self.max_attempts_before_cooldown:
            cooldown_time = self.initial_cooldown + (
                (data["attempts"] - self.max_attempts_before_cooldown) * self.cooldown_increment
            )
            data["cooldown_until"] = current_time + cooldown_time
            return True, f"Too many attempts. Please wait {cooldown_time} seconds"
        if data["attempts"] >= self.max_attempts_before_lockout:
            self.lockouts[username] = (current_time, data["attempts"])
            lockout_hours = self.lockout_duration // 3600
            return True, f"Account locked for {lockout_hours} hours due to too many failed attempts"
        return False, "Invalid credentials"

    def record_successful_attempt(self, username: str):
        if not self.enabled:
            return
        if username in self.failed_attempts:
            del self.failed_attempts[username]
        if username in self.lockouts:
            del self.lockouts[username]


class ServerConfig:
    def __init__(self, config_file: str):
        self.config_file = config_file
        self.load_config()

    def load_config(self):
        if not os.path.exists(self.config_file):
            raise SystemExit("Configuration file not found. Please run qconfig first.")
        try:
            with open(self.config_file, "r") as file:
                self.config = json.load(file)
        except json.JSONDecodeError:
            raise SystemExit("Invalid configuration in config.json")

    @property
    def port(self) -> int:
        return self.config.get("port", 5000)

    @property
    def allow_origins(self) -> List[str]:
        return self.config.get("allow_origins", ["*"])

    @property
    def use_recycle_bin(self) -> bool:
        return self.config.get("use_recycle_bin", True)

    @property
    def users(self) -> Dict:
        return self.config.get("users", {})

    @property
    def brute_force_protection(self) -> Dict:
        return self.config.get("brute_force_protection", {})


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


class LoginRequest(BaseModel):
    username: str
    password: str


class SearchResponse(BaseModel):
    results: List[Dict]
    search_path: str
    pattern: str
    count: int


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    uptime: str
    brute_force_protection: Dict


class UserPermissions(BaseModel):
    can_upload: bool
    can_download: bool
    can_see_preview: bool
    can_delete: bool


class FileSystemService:
    def __init__(self, server_root: str, use_recycle_bin: bool):
        self.server_root = server_root
        self.use_recycle_bin = use_recycle_bin
        self.start_time = time.time()

    def get_uptime(self) -> str:
        minutes = int((time.time() - self.start_time) / 60)
        return f"{minutes} minutes"

    def get_local_ip(self) -> str:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            try:
                hostname = socket.gethostname()
                return socket.gethostbyname(hostname)
            except Exception:
                return "Unable to determine IP"

    def clean_path(self, path: str) -> str:
        if not path or path == "/":
            return ""
        path = path.strip().lstrip("/")
        return path.replace("\\", "/")

    def get_absolute_path(self, clean_path: str) -> str:
        if not clean_path:
            return self.server_root
        absolute_path = os.path.join(self.server_root, clean_path)
        absolute_path = os.path.normpath(absolute_path)
        if not absolute_path.startswith(self.server_root):
            raise ValueError("Path traversal detected")
        return absolute_path

    def get_parent_path(self, clean_path: str) -> str:
        if not clean_path:
            return ""
        parts = clean_path.split("/")
        if len(parts) <= 1:
            return ""
        return "/".join(parts[:-1])

    def is_recycle_bin_path(self, path: str) -> bool:
        return ".recycle_bin" in path.split("/")

    def get_file_date_modified(self, file_path: str) -> str:
        return time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(file_path))
        )

    def get_file_size(self, file_path: str) -> int:
        try:
            return os.path.getsize(file_path)
        except (OSError, FileNotFoundError):
            return 0

    def get_folder_size(self, folder_path: str) -> int:
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(folder_path):
                if ".recycle_bin" in dirpath.split(os.sep):
                    continue

                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except (OSError, FileNotFoundError):
                        continue
        except (OSError, FileNotFoundError):
            return 0
        return total_size

    def move_to_recycle_bin(self, absolute_path: str) -> bool:
        if not self.use_recycle_bin:
            return False
        try:
            dir_path = os.path.dirname(absolute_path)
            recycle_bin_path = os.path.join(dir_path, ".recycle_bin")
            if not os.path.exists(recycle_bin_path):
                os.makedirs(recycle_bin_path)
            item_name = os.path.basename(absolute_path)
            destination = os.path.join(recycle_bin_path, item_name)
            counter = 1
            while os.path.exists(destination):
                if os.path.isfile(absolute_path):
                    name, ext = os.path.splitext(item_name)
                    new_name = f"{name} ({counter}){ext}"
                else:
                    new_name = f"{item_name} ({counter})"
                destination = os.path.join(recycle_bin_path, new_name)
                counter += 1
            shutil.move(absolute_path, destination)
            return True
        except Exception as e:
            print(f"Error moving to recycle bin: {e}")
            return False

    def get_files_in_directory(self, clean_path: str) -> List[FileEntry]:
        folders = []
        files = []
        try:
            absolute_path = self.get_absolute_path(clean_path)
            if not os.path.exists(absolute_path) or not os.path.isdir(absolute_path):
                raise HTTPException(status_code=404, detail="Directory not found")
            for entry in sorted(os.listdir(absolute_path), key=lambda x: x.lower()):
                if entry == ".recycle_bin":
                    continue
                entry_path = os.path.join(absolute_path, entry)
                entry_clean_path = self.clean_path(
                    os.path.relpath(entry_path, self.server_root)
                )

                if self.is_recycle_bin_path(entry_clean_path):
                    continue

                if os.path.isdir(entry_path):
                    folder_size = self.get_folder_size(entry_path)
                    folders.append(
                        FileEntry(
                            name=entry,
                            path=entry_clean_path,
                            type="folder",
                            date_modified=self.get_file_date_modified(entry_path),
                            size=folder_size,
                        )
                    )
                elif os.path.isfile(entry_path):
                    files.append(
                        FileEntry(
                            name=entry,
                            path=entry_clean_path,
                            type="file",
                            date_modified=self.get_file_date_modified(entry_path),
                            size=self.get_file_size(entry_path),
                        )
                    )
        except ValueError:
            return []
        return folders + files

    def search_files(self, search_path: str, pattern: str) -> List[Dict]:
        results = []
        try:
            clean_path = self.clean_path(search_path)
            absolute_path = self.get_absolute_path(clean_path)
            if not os.path.exists(absolute_path) or not os.path.isdir(absolute_path):
                return results
            for root, dirs, files in os.walk(absolute_path):
                if ".recycle_bin" in root.split(os.sep):
                    continue
                dirs[:] = [d for d in dirs if d != ".recycle_bin"]
                for file in files:
                    if fnmatch.fnmatch(file.lower(), f"*{pattern.lower()}*"):
                        file_path = os.path.join(root, file)
                        try:
                            file_clean_path = self.clean_path(
                                os.path.relpath(file_path, self.server_root)
                            )
                            if self.is_recycle_bin_path(file_clean_path):
                                continue
                            rel_path = os.path.relpath(file_path, absolute_path)
                            results.append(
                                {
                                    "name": file,
                                    "path": file_clean_path,
                                    "relative_path": rel_path,
                                    "type": "file",
                                    "date_modified": self.get_file_date_modified(file_path),
                                    "size": self.get_file_size(file_path),
                                    "directory": os.path.dirname(rel_path),
                                }
                            )
                        except (ValueError, OSError):
                            continue
        except ValueError:
            return []
        return sorted(results, key=lambda x: x["name"].lower())


class AuthenticationService:
    def __init__(self, config: ServerConfig):
        self.config = config
        self.brute_force = BruteForceProtection(config.brute_force_protection)

    def authenticate_user(self, username: str, password: str) -> tuple[bool, Optional[str]]:
        is_locked, lock_message = self.brute_force.is_locked(username)
        if is_locked:
            return False, lock_message
        users = self.config.users
        if username not in users:
            needs_cooldown, cooldown_message = self.brute_force.record_failed_attempt(username)
            return False, cooldown_message if needs_cooldown else "Invalid credentials"
        user_data = users[username]
        if isinstance(user_data, dict):
            stored_hash = user_data.get("password", "")
        else:
            stored_hash = user_data
        try:
            if bcrypt.checkpw(password.encode(), stored_hash.encode()):
                self.brute_force.record_successful_attempt(username)
                return True, None
            else:
                needs_cooldown, cooldown_message = self.brute_force.record_failed_attempt(username)
                return False, cooldown_message if needs_cooldown else "Invalid credentials"
        except Exception:
            needs_cooldown, cooldown_message = self.brute_force.record_failed_attempt(username)
            return False, cooldown_message if needs_cooldown else "Authentication error"

    def get_user_permissions(self, username: str) -> Optional[UserPermissions]:
        users = self.config.users
        if username not in users:
            return None
        user_data = users[username]
        if isinstance(user_data, dict):
            return UserPermissions(
                can_upload=user_data.get("can_upload", True),
                can_download=user_data.get("can_download", True),
                can_see_preview=user_data.get("can_see_preview", True),
                can_delete=user_data.get("can_delete", True),
            )
        else:
            return UserPermissions(
                can_upload=True,
                can_download=True,
                can_see_preview=True,
                can_delete=True,
            )


class QuickServe:
    def __init__(self):
        self._setup_paths()
        self.config = ServerConfig(self.config_file)
        self.auth_service = AuthenticationService(self.config)
        self.fs_service = FileSystemService(
            self.SERVER_ROOT, self.config.use_recycle_bin
        )
        self.app = FastAPI(title=APPNAME, version=VERSION)
        self._setup_cors()
        self._setup_routes()

    def _setup_paths(self):
        if getattr(sys, "frozen", False):
            self.current_directory = os.path.dirname(sys.executable)
        else:
            self.current_directory = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.current_directory, "config.json")
        self.SERVER_ROOT = os.getcwd()

    def _setup_cors(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.allow_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_routes(self):
        self.app.post("/api/login")(self.login)
        self.app.get("/api/files")(self.list_files)
        self.app.get("/api/download")(self.download_file)
        self.app.get("/api/preview")(self.preview_file)
        self.app.post("/api/upload")(self.upload_file)
        self.app.delete("/api/delete")(self.delete_file)
        self.app.get("/api/health")(self.health_check)
        self.app.get("/api/config")(self.get_config)
        self.app.get("/api/search")(self.search_files_route)
        self.app.get("/api/permissions")(self.get_user_permissions_route)
        self.app.get("/api/download-zip")(self.download_zip)

    async def _authenticate_user(self, username: str, password: str) -> UserPermissions:
        authenticated, message = self.auth_service.authenticate_user(username, password)
        if not authenticated:
            raise HTTPException(status_code=401, detail=message)
        permissions = self.auth_service.get_user_permissions(username)
        if not permissions:
            raise HTTPException(status_code=401, detail="User not found")
        return permissions

    async def login(self, login_data: LoginRequest):
        permissions = await self._authenticate_user(
            login_data.username, login_data.password
        )
        return {
            "status": "success",
            "message": "Login successful",
            "permissions": permissions.model_dump(),
        }

    async def get_user_permissions_route(
        self, username: str = Query(...), password: str = Query(...)
    ):
        permissions = await self._authenticate_user(username, password)
        return {"status": "success", "permissions": permissions.model_dump()}

    async def list_files(self, path: str = Query("")):
        try:
            clean_path = self.fs_service.clean_path(path)
            absolute_path = self.fs_service.get_absolute_path(clean_path)
            if not os.path.exists(absolute_path) or not os.path.isdir(absolute_path):
                raise HTTPException(status_code=404, detail="Directory not found")
            files = self.fs_service.get_files_in_directory(clean_path)
            parent_path = self.fs_service.get_parent_path(clean_path)
            return DirectoryResponse(
                current_dir=clean_path, parent_dir=parent_path, files=files
            )
        except ValueError:
            raise HTTPException(status_code=403, detail="Access denied")

    async def download_file(
        self,
        path: str = Query(...),
        username: str = Query(...),
        password: str = Query(...),
    ):
        permissions = await self._authenticate_user(username, password)
        if not permissions.can_download:
            raise HTTPException(status_code=403, detail="Download not permitted")
        try:
            clean_path = self.fs_service.clean_path(path)
            absolute_path = self.fs_service.get_absolute_path(clean_path)
            if not os.path.exists(absolute_path) or not os.path.isfile(absolute_path):
                raise HTTPException(status_code=404, detail="File not found")
            filename = os.path.basename(absolute_path)
            return FileResponse(
                absolute_path, media_type="application/octet-stream", filename=filename
            )
        except ValueError:
            raise HTTPException(status_code=403, detail="Access denied")

    async def download_zip(
        self,
        paths: List[str] = Query(...),
        username: str = Query(...),
        password: str = Query(...),
    ):
        permissions = await self._authenticate_user(username, password)
        if not permissions.can_download:
            raise HTTPException(status_code=403, detail="Download not permitted")

        try:
            if isinstance(paths, str):
                paths = [paths]

            absolute_paths = []
            for path in paths:
                clean_path = self.fs_service.clean_path(path)
                absolute_path = self.fs_service.get_absolute_path(clean_path)
                if not os.path.exists(absolute_path):
                    raise HTTPException(status_code=404, detail=f"Path not found: {path}")
                absolute_paths.append(absolute_path)

            if len(absolute_paths) == 1:
                folder_name = os.path.basename(absolute_paths[0]) or "folder"
            else:
                folder_name = "selected_files"
            zip_filename = f"{folder_name}.zip"

            def generate_zip():
                memory_file = io.BytesIO()
                with zipfile.ZipFile(memory_file, "w", zipfile.ZIP_DEFLATED) as zf:
                    for absolute_path in absolute_paths:
                        if os.path.isfile(absolute_path):
                            if not self.fs_service.is_recycle_bin_path(absolute_path):
                                arcname = os.path.basename(absolute_path)
                                zf.write(absolute_path, arcname)
                        elif os.path.isdir(absolute_path):
                            for root, dirs, files in os.walk(absolute_path):
                                if ".recycle_bin" in root.split(os.sep):
                                    continue
                                dirs[:] = [d for d in dirs if d != ".recycle_bin"]

                                for file in files:
                                    file_path = os.path.join(root, file)
                                    if self.fs_service.is_recycle_bin_path(file_path):
                                        continue
                                    arcname = os.path.relpath(file_path, os.path.dirname(absolute_path))
                                    zf.write(file_path, arcname)

                memory_file.seek(0)
                return memory_file

            return StreamingResponse(
                generate_zip(),
                media_type="application/zip",
                headers={"Content-Disposition": f"attachment; filename={zip_filename}"},
            )
        except ValueError:
            raise HTTPException(status_code=403, detail="Access denied")
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to create zip: {str(e)}"
            )

    async def preview_file(
        self,
        path: str = Query(...),
        username: str = Query(...),
        password: str = Query(...),
    ):
        permissions = await self._authenticate_user(username, password)
        if not permissions.can_see_preview:
            raise HTTPException(status_code=403, detail="Preview not permitted")
        try:
            clean_path = self.fs_service.clean_path(path)
            absolute_path = self.fs_service.get_absolute_path(clean_path)
            if not os.path.exists(absolute_path) or not os.path.isfile(absolute_path):
                raise HTTPException(status_code=404, detail="File not found")
            filename = os.path.basename(absolute_path)
            media_type, _ = mimetypes.guess_type(filename)
            if media_type is None:
                media_type = "application/octet-stream"
            headers = {}
            if media_type.startswith(("text/", "image/", "application/pdf")):
                headers["Content-Disposition"] = f'inline; filename="{filename}"'
            else:
                headers["Content-Disposition"] = f'attachment; filename="{filename}"'
            return FileResponse(absolute_path, media_type=media_type, headers=headers)
        except ValueError:
            raise HTTPException(status_code=403, detail="Access denied")

    async def upload_file(
        self,
        path: str = Form(...),
        file: UploadFile = File(...),
        username: str = Form(...),
        password: str = Form(...),
    ):
        permissions = await self._authenticate_user(username, password)
        if not permissions.can_upload:
            raise HTTPException(status_code=403, detail="Upload not permitted")
        try:
            clean_path = self.fs_service.clean_path(path)
            absolute_path = self.fs_service.get_absolute_path(clean_path)
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

    async def delete_file(
        self,
        path: str = Form(...),
        username: str = Form(...),
        password: str = Form(...),
    ):
        permissions = await self._authenticate_user(username, password)
        if not permissions.can_delete:
            raise HTTPException(status_code=403, detail="Delete not permitted")
        try:
            clean_path = self.fs_service.clean_path(path)
            absolute_path = self.fs_service.get_absolute_path(clean_path)
            if not os.path.exists(absolute_path):
                raise HTTPException(
                    status_code=404, detail="File or directory not found"
                )
            
            if os.path.isfile(absolute_path):
                if self.config.use_recycle_bin:
                    moved = self.fs_service.move_to_recycle_bin(absolute_path)
                    if moved:
                        return {
                            "status": "success",
                            "message": "File deleted successfully",
                        }
                    else:
                        raise HTTPException(
                            status_code=500, 
                            detail="Unable to delete file (operation failed)"
                        )
                else:
                    os.remove(absolute_path)
                    return {
                        "status": "success", 
                        "message": "File deleted successfully"
                    }
            
            elif os.path.isdir(absolute_path):
                if self.config.use_recycle_bin:
                    moved = self.fs_service.move_to_recycle_bin(absolute_path)
                    if moved:
                        return {
                            "status": "success",
                            "message": "Directory deleted successfully",
                        }
                    else:
                        raise HTTPException(
                            status_code=500,
                            detail="Unable to delete directory (operation failed)"
                        )
                else:
                    shutil.rmtree(absolute_path)
                    return {
                        "status": "success",
                        "message": "Directory deleted successfully",
                    }
            
            else:
                raise HTTPException(
                    status_code=400, detail="Path is not a file or directory"
                )
        except ValueError:
            raise HTTPException(status_code=403, detail="Access denied")
        except OSError as e:
            raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

    async def health_check(self):
        locked_count = 0
        for username in self.config.users:
            is_locked, message = self.auth_service.brute_force.is_locked(username)
            if is_locked:
                locked_count += 1
        return HealthResponse(
            status="healthy",
            service="QuickServe API",
            version=f"{VERSION}",
            uptime=self.fs_service.get_uptime(),
            brute_force_protection={
                "enabled": self.config.brute_force_protection.get("enabled", True),
                "locked_accounts_count": locked_count,
            },
        )

    async def get_config(self):
        return {
            "port": self.config.port,
            "users_count": len(self.config.users),
            "allow_origins": self.config.allow_origins,
            "use_recycle_bin": self.config.use_recycle_bin,
            "brute_force_protection": self.config.brute_force_protection,
        }

    async def search_files_route(self, path: str = Query(""), pattern: str = Query("")):
        if not pattern or len(pattern.strip()) < 2:
            raise HTTPException(
                status_code=400,
                detail="Search pattern must be at least 2 characters long",
            )
        try:
            results = self.fs_service.search_files(path, pattern.strip())
            return SearchResponse(
                results=results,
                search_path=path,
                pattern=pattern,
                count=len(results),
            )
        except ValueError:
            raise HTTPException(status_code=403, detail="Access denied")

    def _get_terminal_width(self):
        try:
            return shutil.get_terminal_size().columns
        except:
            return 80

    def _print_centered(self, text, width, char=" "):
        padding = (width - len(text)) // 2
        print(f"{char * padding}{text}{char * (width - len(text) - padding)}")

    def _print_line(self, text="", width=80, char="-"):
        if not text:
            print(char * width)
        else:
            side = (width - len(text) - 2) // 2
            print(f"{char * side} {text} {char * (width - len(text) - 2 - side)}")

    def run(self):
        width = self._get_terminal_width()

        print("=" * width)
        self._print_centered(f"QUICKSERVE FILE SERVER API v{VERSION}", width)
        print("=" * width)

        print(f"PORT:            {self.config.port}")
        print(f"ROOT DIRECTORY:  {self.fs_service.server_root}")
        print(f"CORS ORIGINS:    {self.config.allow_origins}")
        print(f"RECYCLE BIN:     {self.config.use_recycle_bin}")

        bf_config = self.config.brute_force_protection
        enabled = bf_config.get("enabled", True)
        print(f"BRUTE FORCE:     {'ENABLED' if enabled else 'DISABLED'}")
        if enabled:
            print(f"  Max attempts:  {bf_config.get('max_attempts_before_cooldown', 3)}")
            print(f"  Cooldown:      {bf_config.get('initial_cooldown', 10)}s + {bf_config.get('cooldown_increment', 10)}s/attempt")
            lockout_hours = bf_config.get('lockout_duration', 86400) // 3600
            print(f"  Lockout:       {bf_config.get('max_attempts_before_lockout', 10)} attempts = {lockout_hours}h lockout")
            print(f"  Note:          Server restart clears all locks")

        print("-" * width)
        print("ACCESS URLs:")
        print(f"Local:           http://localhost:{self.config.port}")
        print(f"Network:         http://0.0.0.0:{self.config.port}")

        local_ip = self.fs_service.get_local_ip()
        if local_ip != "Unable to determine IP":
            print(f"Local Network:   http://{local_ip}:{self.config.port}")

        print("-" * width)
        print("Use the Local URL for access from this machine")
        print("Use the Local Network URL for access from other devices on the same network")
        print("=" * width)

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
            port=self.config.port,
            log_config=log_config,
            access_log=False,
        )


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

