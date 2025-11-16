import os
import json
import sys
import hashlib
import bcrypt

from getpass import getpass


class QuickServeConfig:
    def __init__(self):
        self.config_file = "config.json"
        self.current_directory = os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(self.current_directory, self.config_file)
        self.config = self.load_existing_config()

    def load_existing_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    return json.load(f)
            except:
                print("Existing config file is corrupted. Creating new configuration.")

        return {"port": 5000, "allow_origins": [], "users": {}}

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
            print("4. View Current Configuration")
            print("5. Save and Exit")
            print("6. Exit Without Saving")

            choice = input("\nEnter your choice (1-6): ").strip()

            if choice == "1":
                self.quick_setup()
            elif choice == "2":
                self.manage_users()
            elif choice == "3":
                self.manage_cors()
            elif choice == "4":
                self.view_config()
            elif choice == "5":
                self.save_config()
                print("Configuration completed! You can now run your server.")
                break
            elif choice == "6":
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

    def manage_users(self):
        while True:
            self.clear_screen()
            print("USER MANAGEMENT\n")

            users = self.config.get("users", {})
            if users:
                print("Current users:")
                for i, username in enumerate(users.keys(), 1):
                    print(f"  {i}. {username}")
            else:
                print("No users configured.")

            print("\nOptions:")
            print("1. Add User")
            print("2. Remove User")
            print("3. Change Password")
            print("4. Back to Main Menu")

            choice = input("\nEnter your choice (1-4): ").strip()

            if choice == "1":
                self.add_user()
            elif choice == "2":
                self.remove_user()
            elif choice == "3":
                self.change_password()
            elif choice == "4":
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

        if "users" not in self.config:
            self.config["users"] = {}

        hashed_password = self.hash_password(password)
        self.config["users"][username] = hashed_password
        print(f"User '{username}' added successfully")

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
        self.config["users"][username] = hashed_password
        print(f"Password for '{username}' updated successfully")
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

        # Basic validation
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

        origins = self.config.get("allow_origins", [])
        print("Allowed Origins:")
        if not origins:
            print("  None configured (server will not work with frontend)")
        else:
            for origin in origins:
                print(f"  {origin}")

        users = self.config.get("users", {})
        print(f"Users: {len(users)} user(s) configured")
        for username in users.keys():
            print(f"  {username}")

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

