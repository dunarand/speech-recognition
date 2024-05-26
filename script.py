from live_recognition import live_transcription
from audio_file_recognition import audio_file_transcription

def main():
    """
    Main function to prompt the user for their choice and call the appropriate
    transcription function.
    """
    option = input(
        "Transcribe live using your microphone (1) or transcribe audio "+\
            "files (2)? Enter 1 or 2: "
    )

    if option == '1':
        live_transcription()
    elif option == '2':
        audio_file_transcription()
    else:
        print("Invalid option. Please enter either 1 or 2.")

if __name__ == "__main__":
    main()
