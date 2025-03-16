import os
import sys
import subprocess
import webbrowser
from time import sleep

def check_requirements():
    """Check if requirements are installed"""
    try:
        import streamlit
        import requests
        import python_dotenv
        import pandas
        import numpy
        import pydub
        import speech_recognition
        import langdetect
        import googletrans
        import gtts
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Installing requirements...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        return False

def run_app():
    """Run the Streamlit app"""
    print("Starting Multilingual Loan Advisor...")
    
    # Check for .env file
    if not os.path.exists(".env"):
        print("No .env file found. Creating based on .env.example...")
        if os.path.exists(".env.example"):
            with open(".env.example", "r") as example_file:
                with open(".env", "w") as env_file:
                    env_file.write(example_file.read())
            print("Please edit the .env file with your API keys before continuing.")
            print("Press Enter when ready...")
            input()
        else:
            print("Warning: No .env.example file found. You may need to set up environment variables manually.")
    
    # Start the Streamlit app
    port = 8501
    url = f"http://localhost:{port}"
    
    print(f"Loan Advisor will be available at: {url}")
    print("Starting Streamlit server...")
    
    # Open browser after a short delay
    def open_browser():
        sleep(2)
        webbrowser.open(url)
    
    # Start browser in a separate thread
    import threading
    threading.Thread(target=open_browser).start()
    
    # Run Streamlit
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])

if __name__ == "__main__":
    if check_requirements():
        run_app()
    else:
        print("Please restart the script to run with installed dependencies.")
        sys.exit(1) 