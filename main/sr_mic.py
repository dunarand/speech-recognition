import speech_recognition as sr

def listen_loop(rcg: sr.Recognizer) -> None:
    """Main function for speech recognition using microphone in a while loop

    Args:
        rcg (sr.Recognizer): Instance of a Recognize class object from the 
        speech_recognition library.
    
    Returns:
        None
    """
    with sr.Microphone() as source:
        while True:
            rcg.adjust_for_ambient_noise(source, duration=2)
            print('Waiting for you to speak...')
            audio = rcg.listen(source)
            print(rcg.recognize_google(audio))

def listen(rcg: sr.Recognizer) -> str:
    """Main function for speech recognition using microphone

    Args:
        rcg (sr.Recognizer): Instance of a Recognize class object from the 
        speech_recognition library.

    Returns:
        str: Transcribed string
    """
    with sr.Microphone() as source:
        rcg.adjust_for_ambient_noise(source, duration=2)
        print('Waiting for you to speak...')
        audio = rcg.listen(source)
        return rcg.recognize_google(audio)

if __name__ == '__main__':
    r = sr.Recognizer()
    print(listen(r))
