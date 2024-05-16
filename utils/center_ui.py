"""A function for centeralizing the GUI window"""

def center(master: "tkinter.Tk", width: int, height: int) -> list[int]:
    """A function for centeralizing the GUI window

    Args:
        master (tkinter.Tk): tkinter.Tk instance
        width (int): Width of the GUI window
        height (int): Height of the GUI window

    Returns:
        list[int]: list of width, height, x-coordinate and y-coordinate to set
        the window
    """
    screen_width = master.winfo_screenwidth()
    screen_height = master.winfo_screenheight()

    x_coord = int((screen_width / 2) - (width / 2))
    y_coord = int((screen_height / 2) - (height / 2))

    return [width, height, x_coord, y_coord]
