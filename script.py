import threading
from queue import Queue, Empty
import collections

from datetime import datetime
import logging
from typing import Iterator

import numpy as np
import pyaudio
import webrtcvad
import speech_recognition as sr

log_filename = datetime.now().strftime("speech_recognition_%Y-%m-%d-%H-%M-%S.log")

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(
                            filename=f'./logs/{log_filename}',
                            encoding='utf-8'
                        ),
                        logging.StreamHandler()
                    ])
logger = logging.getLogger(__name__)

def audio_to_vad_format(audio_data: sr.AudioData) -> np.ndarray:
    return np.frombuffer(audio_data.frame_data, dtype=np.int16)

def vad_collector(
        sample_rate: int,
        frame_duration_ms: int,
        padding_duration_ms: int,
        vad: webrtcvad.Vad,
        frames: list
) -> Iterator[bytes]:
    num_padding_frames = int(padding_duration_ms / frame_duration_ms)
    ring_buffer = collections.deque(maxlen=num_padding_frames)
    triggered = False
    voiced_frames = []

    for frame in frames:
        is_speech = vad.is_speech(frame.bytes, sample_rate)

        if not triggered:
            ring_buffer.append((frame, is_speech))
            num_voiced = len([f for f, speech in ring_buffer if speech])
            if num_voiced > 0.9 * ring_buffer.maxlen:
                triggered = True
                voiced_frames.extend([f for f, s in ring_buffer])
                ring_buffer.clear()
        else:
            voiced_frames.append(frame)
            ring_buffer.append((frame, is_speech))
            num_unvoiced = len([f for f, speech in ring_buffer if not speech])
            if num_unvoiced > 0.9 * ring_buffer.maxlen:
                triggered = False
                yield b''.join([f.bytes for f in voiced_frames])
                ring_buffer.clear()
                voiced_frames = []

    if voiced_frames:
        yield b''.join([f.bytes for f in voiced_frames])

class Frame:
    def __init__(self, bytes: bytes, timestamp: float, duration: float):
        self.bytes = bytes
        self.timestamp = timestamp
        self.duration = duration

def frame_generator(
        frame_duration_ms: int,
        audio: np.ndarray,
        sample_rate: int
) -> Iterator[bytes]:
    n = int(sample_rate * (frame_duration_ms / 1000.0) * 2)
    offset = 0
    timestamp = 0.0
    duration = (float(n) / sample_rate) / 2.0
    while offset + n < len(audio):
        yield Frame(audio[offset:offset + n], timestamp, duration)
        timestamp += duration
        offset += n

def recognize_audio(
        rcg: sr.Recognizer,
        audio_queue: Queue,
        results_queue: Queue,
        stop_event: threading.Event,
        language: str
) -> None:
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

def list_input_devices() -> list:
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

def main() -> None:
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

