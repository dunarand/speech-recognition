"""
Includes functions for live transcription using micrphone input

Functions:
    recognize_audio
    handle_recognition_error
    listen_and_process_audio
    process_audio_data
    live_transcription
"""

import threading
from queue import Queue, Empty

import webrtcvad
import speech_recognition as sr

from utils import setup_logger, list_input_devices, select_language
from audio import audio_to_vad_format, vad_collector, frame_generator

logger = setup_logger()

MIN_AUDIO_LENGTH = 1000  # Minimum length of audio in milliseconds
MAX_RETRIES = 3  # Maximum number of retries for short audio clips

def recognize_audio(
    recognizer: sr.Recognizer,
    audio_queue: Queue,
    results_queue: Queue,
    stop_event: threading.Event,
    language: str
) -> None:
    """
    Recognize audio from the queue in a separate thread.
    
    Parameters:
    recognizer (sr.Recognizer): The recognizer object.
    audio_queue (Queue): The queue containing audio data.
    results_queue (Queue): The queue to put recognition results.
    stop_event (threading.Event): Event to signal when to stop.
    language (str): The language code for recognition.
    """
    while not stop_event.is_set():
        try:
            audio = audio_queue.get(timeout=1)
        except Empty:
            continue

        retries = 0
        while retries < MAX_RETRIES:
            try:
                audio_segment = sr.AudioData(audio, 16000, 2)
                transcription = recognizer.recognize_google(
                    audio_segment, language=language
                )
                results_queue.put(transcription)
                logger.info("Transcription: %s", transcription)
                break  # Exit retry loop on successful transcription
            except sr.UnknownValueError:
                handle_recognition_error(
                    "Google Speech Recognition could not understand audio",
                    results_queue
                )
            except sr.RequestError as e:
                handle_recognition_error(
                    "Failed to fetch from Google Speech Recognition"+\
                         f" service; {e}", results_queue
                )
            except Exception as e:
                handle_recognition_error(
                    f"Error recognizing audio: {e}", results_queue
                )
            finally:
                audio_queue.task_done()

            # If the audio is too short, retry
            if len(audio) < MIN_AUDIO_LENGTH:
                retries += 1
                logger.warning(
                    "Audio too short, retrying (%s/%s)", retries, MAX_RETRIES
                )
            else:
                break  # No need to retry if audio length is sufficient

        if retries == MAX_RETRIES:
            logger.error("Max retries reached for audio: %s", audio)

def handle_recognition_error(error_msg: str, results_queue: Queue) -> None:
    """
    Handle recognition errors by logging and putting error message to results
    queue.
    
    Parameters:
    error_msg (str): The error message to log and put in results queue.
    results_queue (Queue): The queue to put recognition results.
    """
    results_queue.put(error_msg)
    logger.error(error_msg)

def listen_and_process_audio(
    recognizer: sr.Recognizer,
    audio_queue: Queue,
    vad: webrtcvad.Vad,
    sample_rate: int,
    frame_duration_ms: int,
    padding_duration_ms: int,
    results_queue: Queue,
    stop_event: threading.Event,
    device_index: int
) -> None:
    """
    Listen and process audio in a separate thread.
    
    Parameters:
    recognizer (sr.Recognizer): The recognizer object.
    audio_queue (Queue): The queue to put audio data.
    vad (webrtcvad.Vad): The VAD object.
    sample_rate (int): The sample rate of the audio.
    frame_duration_ms (int): The frame duration in milliseconds.
    padding_duration_ms (int): The padding duration in milliseconds.
    results_queue (Queue): The queue to put recognition results.
    stop_event (threading.Event): Event to signal when to stop.
    device_index (int): The index of the audio input device.
    """
    with sr.Microphone(sample_rate=sample_rate, device_index=device_index) \
        as source:
        recognizer.adjust_for_ambient_noise(source)
        logger.info('Waiting for you to speak...')

        while not stop_event.is_set():
            try:
                audio_data = recognizer.listen(source, timeout=1)
                process_audio_data(
                    audio_data,
                    audio_queue,
                    vad,
                    sample_rate,
                    frame_duration_ms,
                    padding_duration_ms
                )
            except sr.WaitTimeoutError:
                continue
            except Exception as e:
                handle_recognition_error(
                    f"Error processing audio: {e}", results_queue
                )

def process_audio_data(
    audio_data: sr.AudioData,
    audio_queue: Queue,
    vad: webrtcvad.Vad,
    sample_rate: int,
    frame_duration_ms: int,
    padding_duration_ms: int,
) -> None:
    """
    Process audio data and put segments into the audio queue.
    
    Parameters:
    audio_data (sr.AudioData): The audio data to process.
    audio_queue (Queue): The queue to put audio data.
    vad (webrtcvad.Vad): The VAD object.
    sample_rate (int): The sample rate of the audio.
    frame_duration_ms (int): The frame duration in milliseconds.
    padding_duration_ms (int): The padding duration in milliseconds.
    """
    audio = audio_to_vad_format(audio_data)
    frames = list(frame_generator(frame_duration_ms, audio, sample_rate))
    segments = vad_collector(
        sample_rate, frame_duration_ms, padding_duration_ms, vad, frames
    )

    for segment in segments:
        audio_queue.put(segment)

def live_transcription() -> None:
    """
    Main function to run the speech recognition application.
    """
    devices = list_input_devices()
    print("Available input devices:")
    for idx, name in devices:
        print(f"{idx}: {name}")

    device_index = int(input("Select the device index you want to use: "))
    language = select_language()

    recognizer = sr.Recognizer()
    audio_queue = Queue()
    results_queue = Queue()
    stop_event = threading.Event()

    vad = webrtcvad.Vad(2)# Set aggressiveness level: 0 (least) to 2 (moderate)
    sample_rate = 16000
    frame_duration_ms = 20
    padding_duration_ms = 500

    recognize_thread = threading.Thread(
        target=recognize_audio,
        args=(recognizer, audio_queue, results_queue, stop_event, language),
        daemon=True
    )
    listen_thread = threading.Thread(
        target=listen_and_process_audio,
        args=(
            recognizer,
            audio_queue,
            vad,
            sample_rate,
            frame_duration_ms,
            padding_duration_ms,
            results_queue,
            stop_event,
            device_index
        ),
        daemon=True
    )

    recognize_thread.start()
    listen_thread.start()

    try:
        while not stop_event.is_set():
            try:
                results_queue.get(timeout=1)
            except Empty:
                continue
            else:
                results_queue.task_done()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt detected. Stopping...")
    finally:
        stop_event.set()
        recognize_thread.join()
        listen_thread.join()
        logger.info("Program terminated")
