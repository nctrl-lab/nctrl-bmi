import datetime
import subprocess

def tprint(text):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    print(f'[{timestamp}] {text}')

def kill_existing_processes():
    try:
        subprocess.run(["fuser", "-k", "/dev/xillybus_fet_clf_32"], check=True)
        tprint("Successfully killed existing processes.")
    except subprocess.CalledProcessError:
        tprint("Failed to kill existing processes. Continuing anyway.")
    except FileNotFoundError:
        tprint("fuser command not found. Make sure it's installed.")
    except Exception as e:
        tprint(f"An unexpected error occurred: {str(e)}")