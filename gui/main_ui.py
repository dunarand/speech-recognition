import tkinter as tk
import os

from utils.center_ui import center

class SpeechRecognitionUI(tk.Frame):

    def __init__(self, parent):

        self.mic_state = 1
        self.path = os.getcwd()

        tk.Frame.__init__(self, parent)
        self.parent = parent

        geometry = center(parent, 512, 384)
        parent.title('Wordle')
        parent.resizable(False, False)
        parent.config(bg = '#C7C7C7')
        parent.geometry(
            f'{geometry[0]}x{geometry[1]}+{geometry[2]}+{geometry[3]}'
        )

        button_1 = tk.Label(

            text = 'Open Mic',
            font = ('lato', 12, 'bold'),
            width = 7,
            height = 1,
            background = "#292929",
            foreground = '#C7C7C7'

        )
        button_2 = tk.Label(

            text = 'Close Mic',
            font = ('lato', 12, 'bold'),
            width = 7,
            height = 1,
            background = "#292929",
            foreground = '#C7C7C7'

        )

        mic_button = tk.Button(
            parent,
            #image = tk.PhotoImage(file = self.icon_select()),
            command = self.switch_mic_state
        )
        mic_button.pack()
        #button_1.place(x = 0, y = 0)
        #button_2.place(x = 85, y = 0)

    def icon_select(self):
        if self.mic_state == 1:
            return os.path.join(self.path, 'sources/microphone-342.png')

    def switch_mic_state(self):
        print('button works')

    def select_input_device(self):
        pass

    def load_file(self):
        pass

    def translate(self):
        pass

    def options(self):
        pass
