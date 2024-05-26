"""
Includes functions to handle audio data

Classes:
    Frame

Functions:
    audio_to_vad_format
    vad_collector
    frame_generator
"""

import collections

from typing import Iterator

import numpy as np
import webrtcvad
import speech_recognition as sr

class Frame:
    """
    Represents a segment of audio data.

    Attributes:
        _bytes (bytes)
        timestamp (float)
        duration (float)

    Methods:
        __init__
    """
    def __init__(self, bytes: bytes, timestamp: float, duration: float):
        """
        Initialize a Frame object.
        
        Parameters:
        bytes_ (bytes): The audio data.
        timestamp (float): The timestamp of the frame.
        duration (float): The duration of the frame.
        """
        self.bytes = bytes
        self.timestamp = timestamp
        self.duration = duration

def audio_to_vad_format(audio_data: sr.AudioData) -> np.ndarray:
    """
    Convert audio data to the format expected by webrtcvad.
    
    Parameters:
    audio_data (sr.AudioData): The audio data to convert.

    Returns:
    np.ndarray: The audio data as a numpy array of 16-bit integers.
    """
    return np.frombuffer(audio_data.frame_data, dtype=np.int16)

def vad_collector(
        sample_rate: int,
        frame_duration_ms: int,
        padding_duration_ms: int,
        vad: webrtcvad.Vad,
        frames: list
) -> Iterator[bytes]:
    """
    Generator that yields segments of audio from frames.
    
    Parameters:
    sample_rate (int): The sample rate of the audio.
    frame_duration_ms (int): The frame duration in milliseconds.
    padding_duration_ms (int): The padding duration in milliseconds.
    vad (webrtcvad.Vad): The VAD object.
    frames (list): List of audio frames.

    Yields:
    Iterator[bytes]: Segments of audio data.
    """
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

def frame_generator(
        frame_duration_ms: int,
        audio: np.ndarray,
        sample_rate: int
) -> Iterator[bytes]:
    """
    Generate audio frames from raw audio data.
    
    Parameters:
    frame_duration_ms (int): The frame duration in milliseconds.
    audio (np.ndarray): The raw audio data.
    sample_rate (int): The sample rate of the audio.

    Yields:
    Iterator[bytes]: Frames of audio data.
    """
    n = int(sample_rate * (frame_duration_ms / 1000.0) * 2)
    offset = 0
    timestamp = 0.0
    duration = (float(n) / sample_rate) / 2.0
    while offset + n < len(audio):
        yield Frame(audio[offset:offset + n], timestamp, duration)
        timestamp += duration
        offset += n
