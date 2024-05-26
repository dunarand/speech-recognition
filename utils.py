""""
Includes functions to handle logging, selecting input and language

Functions:
    setup_logger
    list_input_devices
    select_language
"""

import os
from datetime import datetime
import logging

import pyaudio

def setup_logger():
    """
    Setup logging configuration.
    Creates the ./logs directory if it doesn't exist.
    """
    # Create the logs directory if it doesn't exist
    logs_dir = './logs'
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    # Generate log filename with current date and time
    log_filename = datetime.now().strftime(
        "speech_recognition_%Y-%m-%d-%H-%M-%S.log"
    )

    # Configure logging
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[
                            logging.FileHandler(
                                filename=os.path.join(logs_dir, log_filename),
                                encoding='utf-8'
                            ),
                            logging.StreamHandler()
                        ])
    return logging.getLogger(__name__)

def list_input_devices() -> list:
    """
    List available input devices.

    Returns:
    list: A list of tuples containing device index and name.
    """
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    devices = []
    for i in range(numdevices):
        device_info = p.get_device_info_by_host_api_device_index(0, i)
        if device_info.get('maxInputChannels') > 0:
            devices.append((i, device_info.get('name')))
    p.terminate()
    return devices

def select_language() -> str:
    """
    Select the language for speech recognition.

    Returns:
    str: The language code for recognition.
    """
    print("Select the language for speech recognition:")
    print("1: English")
    print("2: Turkish")
    choice = input("Enter the number of your choice: ")
    if choice == "1":
        return "en-US"
    elif choice == "2":
        return "tr-TR"
    else:
        print("Invalid choice. Defaulting to English.")
        return "en-US"
