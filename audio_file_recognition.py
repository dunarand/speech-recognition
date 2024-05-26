"""
Includes functions for transcribing audio files specified by the user

Functions:
    transcribe_audio
    validate_audio_file
    transcribe
    transcribe_single_file
    transcribe_directory
    main
"""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import speech_recognition as sr
from utils import setup_logger, select_language

# Setup logger
logger = setup_logger()

def transcribe_audio(audio_file: str) -> str:
    """
    Transcribe audio file using SpeechRecognition.

    Args:
    audio_file (str): Path to the audio file.

    Returns:
    str: Transcribed text.
    """
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
        return recognizer.recognize_google(audio_data)
    except sr.UnknownValueError:
        logger.error("Speech Recognition could not understand audio.")
    except sr.RequestError as e:
        logger.error(
            "Could not request results from Google Speech Recognition" +\
                " service; %s", e
        )
    except FileNotFoundError:
        logger.error("Audio file not found: %s", audio_file)
    except Exception as e:
        logger.error("An unexpected error occurred: %s", e)
    return ""

def validate_audio_file(audio_file: str) -> bool:
    """
    Validate audio file format.

    Args:
    audio_file (str): Path to the audio file.

    Returns:
    bool: True if the audio file format is supported, False otherwise.
    """
    supported_formats = [".wav", ".mp3"]
    return os.path.splitext(audio_file)[1].lower() in supported_formats

def transcribe(audio_file: str):
    """
    Transcribe an audio file and log the result.

    Args:
    audio_file (str): Path to the audio file.
    """
    logger.info("Transcribing audio file: %s", audio_file)
    transcribed_text = transcribe_audio(audio_file)
    if transcribed_text:
        logger.info("Transcription successful for file: %s", audio_file)
        logger.info("Transcribed Text: %s", transcribed_text)
    else:
        logger.info("Transcription failed for file: %s", audio_file)

def transcribe_single_file(audio_file: str):
    """
    Transcribe a single audio file.

    This function validates the audio file, selects the language for 
    transcription, and transcribes the audio file while logging the process.

    Args:
    audio_file (str): Path to the audio file.
    """
    if not os.path.exists(audio_file):
        logger.error("Audio file not found.")
        return

    if not validate_audio_file(audio_file):
        logger.error(
            "Unsupported audio file format. Supported formats: WAV, MP3"
        )
        return

    language = select_language()
    logger.info("Selected language for transcription: %s", language)
    transcribe(audio_file)

def transcribe_directory(directory: str):
    """
    Transcribe all supported audio files within a directory.

    This function validates the directory, selects the language for
    transcription, and transcribes each audio file in the directory using
    multiple threads while logging the process.

    Args:
    directory (str): Path to the directory containing audio files.
    """
    if not os.path.exists(directory):
        logger.error("Directory not found.")
        return

    supported_formats = [".wav", ".mp3"]
    audio_files = [
        os.path.join(directory, f) for f in os.listdir(directory)
        if os.path.isfile(os.path.join(directory, f)) and \
            os.path.splitext(f)[1].lower() in supported_formats
    ]

    if not audio_files:
        logger.error("No supported audio files found in the directory.")
        return

    language = select_language()
    logger.info("Selected language for transcription: %s", language)

    with ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(transcribe, audio_file): audio_file \
                for audio_file in audio_files
        }
        for future in as_completed(futures):
            audio_file = futures[future]
            try:
                future.result()
            except Exception as e:
                logger.error(
                    "An error occurred while transcribing file: %s; %s",
                    audio_file, e
                )

def audio_file_transcription():
    """
    Main function for audio transcription.
    """
    option = input(
        "Transcribe a single audio file (1) or all audio files within a " +\
            "directory (2)? Enter 1 or 2: "
    )

    if option == '1':
        audio_file = input("Enter the path to the audio file: ")
        transcribe_single_file(audio_file)
    elif option == '2':
        directory = input(
            "Enter the path to the directory containing audio files: "
        )
        transcribe_directory(directory)
    else:
        logger.error("Invalid option. Please enter either 1 or 2.")
