import os
import json
import sys
import hashlib
import bcrypt

from getpass import getpass


class QuickServeConfig:
    def __init__(self):
        self.config_file = "config.json"
        if getattr(sys, "frozen", False):
            self.current_directory = os.path.dirname(sys.executable)
        else:
            self.current_directory = os.path.dirname(os.path.abspath(__file__))

        self.config_path = os.path.join(self.current_directory, self.config_file)
        self.config = self.load_existing_config()

    def load_existing_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    config_data = json.load(f)

                    users = config_data.get("users", {})
                    for username, user_data in users.items():
                        if isinstance(user_data, str):
                            config_data["users"][username] = {
                                "password": user_data,
                                "can_upload": True,
                                "can_download": True,
                                "can_see_preview": True,
                                "can_delete": True,
                            }

                    return config_data
            except:
                print("Existing config file is corrupted. Creating new configuration.")

        return {"port": 5000, "allow_origins": [], "users": {}, "use_recycle_bin": True}

    def hash_password(self, password):
        sha256_hash = hashlib.sha256(password.encode()).hexdigest()
        salt = bcrypt.gensalt()
        bcrypt_hash = bcrypt.hashpw(sha256_hash.encode(), salt)
        return bcrypt_hash.decode()

    def save_config(self):
        try:
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=2)
            print(f"Configuration saved to {self.config_path}")
        except Exception as e:
            print(f"Error saving configuration: {e}")
            print(f"Attempted to save to: {self.config_path}")

    def clear_screen(self):
        os.system("cls" if os.name == "nt" else "clear")

    def show_banner(self):
        banner = """
============================================
          QuickServe Configurator
         FastAPI File Server Setup
============================================"""
        print(banner)

    def main_menu(self):
        while True:
            self.clear_screen()
            self.show_banner()

            print("\nMAIN MENU")
            print("1. Quick Setup (Recommended for first time)")
            print("2. Manage Users")
            print("3. Manage CORS Origins")
            print("4. Server Settings")
            print("5. View Current Configuration")
            print("6. Save and Exit")
            print("7. Exit Without Saving")

            choice = input("\nEnter your choice (1-7): ").strip()

            if choice == "1":
                self.quick_setup()
            elif choice == "2":
                self.manage_users()
            elif choice == "3":
                self.manage_cors()
            elif choice == "4":
                self.server_settings()
            elif choice == "5":
                self.view_config()
            elif choice == "6":
                self.save_config()
                print("Configuration completed! You can now run your server.")
                break
            elif choice == "7":
                if input("Exit without saving? (y/N): ").lower() == "y":
                    print("Exiting without saving changes.")
                    break
            else:
                input("Invalid choice. Press Enter to continue...")

    def quick_setup(self):
        self.clear_screen()
        print("QUICK SETUP WIZARD\n")

        current_port = self.config.get("port", 5000)
        port_input = input(f"Enter server port [{current_port}]: ").strip()
        if port_input:
            try:
                self.config["port"] = int(port_input)
                print(f"Port set to {self.config['port']}")
            except ValueError:
                print("Invalid port number. Using default.")

        current_recycle_bin = self.config.get("use_recycle_bin", True)
        recycle_bin_input = (
            input(f"Use recycle bin for deleted files? (Y/n) [{current_recycle_bin}]: ")
            .strip()
            .lower()
        )
        if recycle_bin_input in ["y", "yes", ""]:
            self.config["use_recycle_bin"] = True
            print("✓ Recycle bin enabled")
        elif recycle_bin_input in ["n", "no"]:
            self.config["use_recycle_bin"] = False
            print("✗ Recycle bin disabled")

        print("\nCORS Configuration (required for frontend access):")
        print("Authentication requires specific frontend URLs.")
        if input("Use default frontend URLs? (Y/n): ").strip().lower() in [
            "",
            "y",
            "yes",
        ]:
            default_origins = [
                "https://quickserve.noman.qzz.io",
                "https://8gudbits.github.io",
            ]
            self.config["allow_origins"] = default_origins
            print("Default origins set for official QuickServe frontends")
        else:
            print("You'll need to configure CORS origins manually in the main menu.")

        print("\nUser Setup:")
        if input("Add a user account? (y/N): ").lower() == "y":
            self.add_user()

        input("\nQuick setup completed! Press Enter to continue...")

    def server_settings(self):
        while True:
            self.clear_screen()
            print("SERVER SETTINGS\n")

            current_port = self.config.get("port", 5000)
            current_recycle_bin = self.config.get("use_recycle_bin", True)

            print(f"1. Server Port: {current_port}")
            print(f"2. Use Recycle Bin: {current_recycle_bin}")
            print("3. Back to Main Menu")

            choice = input("\nEnter your choice (1-3): ").strip()

            if choice == "1":
                self.change_port()
            elif choice == "2":
                self.toggle_recycle_bin()
            elif choice == "3":
                break
            else:
                input("Invalid choice. Press Enter to continue...")

    def change_port(self):
        print("\nCHANGE SERVER PORT")
        current_port = self.config.get("port", 5000)
        port_input = input(f"Enter new server port [{current_port}]: ").strip()

        if port_input:
            try:
                new_port = int(port_input)
                if 1 <= new_port <= 65535:
                    self.config["port"] = new_port
                    print(f"Port changed to {new_port}")
                else:
                    print("Port must be between 1 and 65535")
            except ValueError:
                print("Invalid port number")
        else:
            print("Port unchanged")

        input("Press Enter to continue...")

    def toggle_recycle_bin(self):
        print("\nRECYCLE BIN SETTING")
        current_setting = self.config.get("use_recycle_bin", True)
        print("When enabled, deleted files are moved to .recycle_bin folder instead")
        print("of being permanently deleted. This prevents accidental data loss.")
        print(f"Current setting: {current_setting}")

        choice = input("Use recycle bin for deleted files? (Y/n): ").strip().lower()
        if choice in ["y", "yes", ""]:
            self.config["use_recycle_bin"] = True
            print("✓ Recycle bin enabled")
        elif choice in ["n", "no"]:
            self.config["use_recycle_bin"] = False
            print("✗ Recycle bin disabled")
        else:
            print("Setting unchanged")

        input("Press Enter to continue...")

    def manage_users(self):
        while True:
            self.clear_screen()
            print("USER MANAGEMENT\n")

            users = self.config.get("users", {})
            if users:
                print("Current users:")
                for i, (username, user_data) in enumerate(users.items(), 1):
                    if isinstance(user_data, dict):
                        permissions = []
                        if user_data.get("can_upload", True):
                            permissions.append("upload")
                        if user_data.get("can_download", True):
                            permissions.append("download")
                        if user_data.get("can_see_preview", True):
                            permissions.append("preview")
                        if user_data.get("can_delete", True):
                            permissions.append("delete")
                        print(
                            f"  {i}. {username} [Permissions: {', '.join(permissions)}]"
                        )
                    else:
                        print(f"  {i}. {username} [All permissions]")
            else:
                print("No users configured.")

            print("\nOptions:")
            print("1. Add User")
            print("2. Remove User")
            print("3. Change Password")
            print("4. Edit Permissions")
            print("5. Back to Main Menu")

            choice = input("\nEnter your choice (1-5): ").strip()

            if choice == "1":
                self.add_user()
            elif choice == "2":
                self.remove_user()
            elif choice == "3":
                self.change_password()
            elif choice == "4":
                self.edit_permissions()
            elif choice == "5":
                break
            else:
                input("Invalid choice. Press Enter to continue...")

    def add_user(self):
        print("\nADD NEW USER")
        username = input("Username: ").strip()

        if not username:
            print("Username cannot be empty")
            return

        if username in self.config.get("users", {}):
            print("User already exists")
            return

        print("Input will not be visible as you type for security reasons")
        password = getpass("Password: ")
        confirm_password = getpass("Confirm Password: ")

        if password != confirm_password:
            print("Passwords do not match")
            return

        if not password:
            print("Password cannot be empty")
            return

        print("\nUser Permissions:")
        can_upload = input("Allow file upload? (Y/n): ").strip().lower() in [
            "",
            "y",
            "yes",
        ]
        can_download = input("Allow file download? (Y/n): ").strip().lower() in [
            "",
            "y",
            "yes",
        ]
        can_see_preview = input("Allow file preview? (Y/n): ").strip().lower() in [
            "",
            "y",
            "yes",
        ]
        can_delete = input("Allow file deletion? (Y/n): ").strip().lower() in [
            "",
            "y",
            "yes",
        ]

        if "users" not in self.config:
            self.config["users"] = {}

        hashed_password = self.hash_password(password)
        self.config["users"][username] = {
            "password": hashed_password,
            "can_upload": can_upload,
            "can_download": can_download,
            "can_see_preview": can_see_preview,
            "can_delete": can_delete,
        }
        print(f"User '{username}' added successfully with selected permissions")

    def remove_user(self):
        users = self.config.get("users", {})
        if not users:
            input("No users to remove. Press Enter to continue...")
            return

        print("\nREMOVE USER")
        username = input("Enter username to remove: ").strip()

        if username in users:
            if (
                input(
                    f"Are you sure you want to remove user '{username}'? (y/N): "
                ).lower()
                == "y"
            ):
                del self.config["users"][username]
                print(f"User '{username}' removed")
            else:
                print("User removal cancelled")
        else:
            print("User not found")

        input("Press Enter to continue...")

    def change_password(self):
        users = self.config.get("users", {})
        if not users:
            input("No users configured. Press Enter to continue...")
            return

        print("\nCHANGE PASSWORD")
        username = input("Username: ").strip()

        if username not in users:
            print("User not found")
            return

        print("Input will not be visible as you type for security reasons")
        new_password = getpass("New Password: ")
        confirm_password = getpass("Confirm New Password: ")

        if new_password != confirm_password:
            print("Passwords do not match")
            return

        if not new_password:
            print("Password cannot be empty")
            return

        hashed_password = self.hash_password(new_password)

        if isinstance(users[username], dict):
            self.config["users"][username]["password"] = hashed_password
        else:
            self.config["users"][username] = hashed_password

        print(f"Password for '{username}' updated successfully")
        input("Press Enter to continue...")

    def edit_permissions(self):
        users = self.config.get("users", {})
        if not users:
            input("No users configured. Press Enter to continue...")
            return

        print("\nEDIT USER PERMISSIONS")
        username = input("Username: ").strip()

        if username not in users:
            print("User not found")
            return

        user_data = users[username]
        if not isinstance(user_data, dict):
            user_data = {"password": user_data}
            self.config["users"][username] = user_data

        print(f"\nCurrent permissions for '{username}':")
        print(f"  Upload: {user_data.get('can_upload', True)}")
        print(f"  Download: {user_data.get('can_download', True)}")
        print(f"  Preview: {user_data.get('can_see_preview', True)}")
        print(f"  Delete: {user_data.get('can_delete', True)}")

        print("\nNew permissions (press Enter to keep current):")
        can_upload_input = input("Allow file upload? (Y/n): ").strip().lower()
        can_download_input = input("Allow file download? (Y/n): ").strip().lower()
        can_see_preview_input = input("Allow file preview? (Y/n): ").strip().lower()
        can_delete_input = input("Allow file deletion? (Y/n): ").strip().lower()

        if can_upload_input:
            user_data["can_upload"] = can_upload_input in ["", "y", "yes"]
        if can_download_input:
            user_data["can_download"] = can_download_input in ["", "y", "yes"]
        if can_see_preview_input:
            user_data["can_see_preview"] = can_see_preview_input in ["", "y", "yes"]
        if can_delete_input:
            user_data["can_delete"] = can_delete_input in ["", "y", "yes"]

        print(f"Permissions for '{username}' updated successfully")
        input("Press Enter to continue...")

    def manage_cors(self):
        while True:
            self.clear_screen()
            print("CORS ORIGIN MANAGEMENT\n")

            origins = self.config.get("allow_origins", [])
            print("Current allowed origins:")
            if not origins:
                print("  No origins configured (server will not work with frontend)")
            else:
                for i, origin in enumerate(origins, 1):
                    print(f"  {i}. {origin}")

            print("\nOptions:")
            print("0. What is CORS? (Help)")
            print("1. Use Default (Recommended)")
            print("2. Add Custom Origin")
            print("3. Remove Origin")
            print("4. Clear All Origins")
            print("5. Back to Main Menu")

            choice = input("\nEnter your choice (0-5): ").strip()

            if choice == "0":
                self.cors_help()
            elif choice == "1":
                self.use_default_origins()
            elif choice == "2":
                self.add_origin()
            elif choice == "3":
                self.remove_origin()
            elif choice == "4":
                if input("Clear all origins? (y/N): ").lower() == "y":
                    self.config["allow_origins"] = []
                    print("All origins cleared - server will not work with frontend!")
                input("Press Enter to continue...")
            elif choice == "5":
                break
            else:
                input("Invalid choice. Press Enter to continue...")

    def cors_help(self):
        self.clear_screen()
        print("CORS HELP - What is CORS?\n")
        print("CORS (Cross-Origin Resource Sharing) controls which websites")
        print("can access your file server from a web browser.\n")
        print("IMPORTANT: With authentication enabled:")
        print("• Wildcard '*' origins are BLOCKED by browsers")
        print("• You must specify exact frontend URLs\n")
        print("Recommended: Use 'Use Default' option which includes:")
        print("• https://quickserve.noman.qzz.io")
        print("• https://8gudbits.github.io")
        print("\nIf hosting your own frontend, add your exact website URL.")
        input("\nPress Enter to continue...")

    def use_default_origins(self):
        print("\nSETTING DEFAULT ORIGINS")
        default_origins = [
            "https://quickserve.noman.qzz.io",
            "https://8gudbits.github.io",
        ]

        self.config["allow_origins"] = default_origins
        print("Default origins set:")
        for origin in default_origins:
            print(f"  ✓ {origin}")
        print("\nThese are the official QuickServe frontend URLs.")
        input("Press Enter to continue...")

    def add_origin(self):
        print("\nADD CUSTOM ORIGIN")
        print("Format examples:")
        print("• https://yourwebsite.com")
        print("• http://localhost:3000")
        print("• https://subdomain.example.com")

        origin = input("\nEnter origin: ").strip()

        if not origin:
            print("Origin cannot be empty")
            input("Press Enter to continue...")
            return

        if not origin.startswith(("http://", "https://")):
            print("Error: Origin must start with http:// or https://")
            input("Press Enter to continue...")
            return

        if "allow_origins" not in self.config:
            self.config["allow_origins"] = []

        if origin in self.config["allow_origins"]:
            print("Origin already exists")
        else:
            self.config["allow_origins"].append(origin)
            print(f"Origin '{origin}' added")

        input("Press Enter to continue...")

    def remove_origin(self):
        origins = self.config.get("allow_origins", [])
        if not origins:
            input("No origins to remove. Press Enter to continue...")
            return

        print("\nREMOVE CORS ORIGIN")
        print("Current origins:")
        for i, origin in enumerate(origins, 1):
            print(f"  {i}. {origin}")

        try:
            choice = int(input("Enter number of origin to remove: "))
            if 1 <= choice <= len(origins):
                removed_origin = origins[choice - 1]
                self.config["allow_origins"].pop(choice - 1)
                print(f"Origin '{removed_origin}' removed")
            else:
                print("Invalid selection")
        except ValueError:
            print("Please enter a valid number")

        input("Press Enter to continue...")

    def view_config(self):
        self.clear_screen()
        print("CURRENT CONFIGURATION\n")

        print(f"Port: {self.config.get('port', 5000)}")
        print(f"Use Recycle Bin: {self.config.get('use_recycle_bin', True)}")

        origins = self.config.get("allow_origins", [])
        print("Allowed Origins:")
        if not origins:
            print("  None configured (server will not work with frontend)")
        else:
            for origin in origins:
                print(f"  {origin}")

        users = self.config.get("users", {})
        print(f"Users: {len(users)} user(s) configured")
        for username, user_data in users.items():
            if isinstance(user_data, dict):
                permissions = []
                if user_data.get("can_upload", True):
                    permissions.append("upload")
                if user_data.get("can_download", True):
                    permissions.append("download")
                if user_data.get("can_see_preview", True):
                    permissions.append("preview")
                if user_data.get("can_delete", True):
                    permissions.append("delete")
                print(f"  {username} [Permissions: {', '.join(permissions)}]")
            else:
                print(f"  {username} [All permissions]")

        input("\nPress Enter to continue...")


def main():
    try:
        configurator = QuickServeConfig()
        configurator.main_menu()
    except KeyboardInterrupt:
        print("\nConfiguration cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

