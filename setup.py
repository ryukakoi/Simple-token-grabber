import sys
import subprocess
import importlib

def check_and_install(package, pip_name=None):
    try:
        importlib.import_module(package)
        print(f"[✓] {package} already installed")
    except ImportError:
        pip_name = pip_name or package
        print(f"[!] {package} not found, installing...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", pip_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print(f"[✓] Successfully installed {package}")
        except subprocess.CalledProcessError:
            print(f"[X] Failed to install {package}")
            sys.exit(1)

def main():
    requirements = [
        ("win32crypt", "pypiwin32"),
        ("Crypto", "pycryptodome"),
        ("requests", None),  
        ("psutil", None),
        ("urllib3", None)
    ]

    print("Checking and installing dependencies...")
    for package, pip_name in requirements:
        check_and_install(package, pip_name)

    print("\nAll dependencies installed successfully!")
    print("You can now run the main application.")

if __name__ == "__main__":
    main()