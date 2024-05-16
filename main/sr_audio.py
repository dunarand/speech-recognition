import speech_recognition as sr

def audio_transcriber(rcg: sr.Recognizer, src: str) -> str:
    """Transcribes a prerecoded audio file

    Args:
        rcg (sr.Recognizer): Instance of a Recognize class object from the 
        speech_recognition library.
        src (str): Path to the source file

    Returns:
        str: Transcribtion of the given audio file
    """
    with sr.WavFile(src) as source:
        audio = rcg.record(source)

    text = rcg.recognize_google(audio)
    return text

if __name__ == '__main__':
    pass
