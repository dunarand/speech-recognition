"""
Includes functions to recognize configured audio

Functions:
    recognize_audio
    listen_and_process_audio
    main
"""

import threading
from queue import Queue, Empty

import webrtcvad
import speech_recognition as sr

from utils import setup_logger, list_input_devices, select_language
from audio import audio_to_vad_format, vad_collector, frame_generator

logger = setup_logger()

def recognize_audio(
        rcg: sr.Recognizer,
        audio_queue: Queue,
        results_queue: Queue,
        stop_event: threading.Event,
        language: str
) -> None:
    """
    Function to recognize audio from the queue in a separate thread.
    
    Parameters:
    rcg (sr.Recognizer): The recognizer object.
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

        try:
            audio_segment = sr.AudioData(audio, 16000, 2)
            transcription = rcg.recognize_google(audio_segment, language=language)
            results_queue.put(transcription)
            logger.info(f"Transcription: {transcription}")
        except sr.UnknownValueError:
            error_msg = "Google Speech Recognition could not understand audio"
            results_queue.put(error_msg)
            logger.warning(error_msg)
        except sr.RequestError as e:
            error_msg = f"Failed to fetch from Google Speech Recognition service; {e}"
            results_queue.put(error_msg)
            logger.error(error_msg)
        except Exception as e:
            error_msg = f"Error recognizing audio: {e}"
            results_queue.put(error_msg)
            logger.error(error_msg)
        finally:
            audio_queue.task_done()

def listen_and_process_audio(
        rcg: sr.Recognizer,
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
    rcg (sr.Recognizer): The recognizer object.
    audio_queue (Queue): The queue to put audio data.
    vad (webrtcvad.Vad): The VAD object.
    sample_rate (int): The sample rate of the audio.
    frame_duration_ms (int): The frame duration in milliseconds.
    padding_duration_ms (int): The padding duration in milliseconds.
    results_queue (Queue): The queue to put recognition results.
    stop_event (threading.Event): Event to signal when to stop.
    device_index (int): The index of the audio input device.
    """
    with sr.Microphone(sample_rate=sample_rate, device_index=device_index) as source:
        rcg.adjust_for_ambient_noise(source)
        logger.info('Waiting for you to speak...')
        while not stop_event.is_set():
            try:
                audio_data = rcg.listen(source, timeout=1)
            except sr.WaitTimeoutError:
                continue

            try:
                audio = audio_to_vad_format(audio_data)
                frames = list(frame_generator(
                    frame_duration_ms,
                    audio,
                    sample_rate
                ))
                segments = vad_collector(
                    sample_rate,
                    frame_duration_ms,
                    padding_duration_ms,
                    vad,
                    frames
                )

                for segment in segments:
                    audio_queue.put(segment)
            except Exception as e:
                error_msg = f"Error processing audio: {e}"
                results_queue.put(error_msg)
                logger.error(error_msg)

def main() -> None:
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

    vad = webrtcvad.Vad(3)  # Set aggressiveness level: 0 (least) to 3 (most)
    sample_rate = 16000
    frame_duration_ms = 30
    padding_duration_ms = 300

    try:
        # Start the thread for recognizing audio
        recognize_thread = threading.Thread(
            target=recognize_audio,
            args=(
                recognizer,
                audio_queue,
                results_queue,
                stop_event,
                language
            ),
            daemon=True
        )
        recognize_thread.start()

        # Start listening and processing audio
        listen_thread = threading.Thread(
            target=listen_and_process_audio,
            args=(
                recognizer,
                audio_queue,
                vad, sample_rate,
                frame_duration_ms,
                padding_duration_ms,
                results_queue,
                stop_event,
                device_index
            ), daemon=True
        )
        listen_thread.start()

        while not stop_event.is_set():
            try:
                result = results_queue.get(timeout=1)
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

if __name__ == "__main__":
    main()
