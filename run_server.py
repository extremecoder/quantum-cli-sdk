#!/usr/bin/env python3
import subprocess
import sys
import os

def main():
    """Install required packages and run the server."""
    print("Installing required packages...")
    
    # Install minimal dependencies for running
    subprocess.check_call([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn", "qiskit"])
    
    print("Packages installed successfully.")
    
    # Run the server
    print("Starting the server...")
    subprocess.check_call([sys.executable, "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"])

if __name__ == "__main__":
    main() 