import subprocess
import logging

logger = logging.getLogger(__name__)

def kill_existing_processes():
    try:
        subprocess.run(["fuser", "-k", "/dev/xillybus_fet_clf_32"], check=True)
        logger.info("Successfully killed existing processes.")
    except subprocess.CalledProcessError:
        logger.warning("Failed to kill existing processes. Continuing anyway.")
    except FileNotFoundError:
        logger.warning("fuser command not found. Make sure it's installed.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")