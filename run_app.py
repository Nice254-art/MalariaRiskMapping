# run_app.py
import subprocess
import sys

def install_requirements():
    """Install required packages"""
    print("Installing requirements...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def run_streamlit():
    """Run the Streamlit app"""
    print("Starting Streamlit app...")
    subprocess.check_call(["streamlit", "run", "app.py"])

if __name__ == "__main__":
    install_requirements()
    run_streamlit()