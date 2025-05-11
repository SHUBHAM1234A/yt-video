import msvcrt

def highlight_text(text, color_code):
    return f"\033[{color_code}m{text}\033[0m"

class Menu:
    def __init__(self, title, options):
        self.title = title
        self.options = options
        self.selected_index = 0
        self.display()

    def display(self, redraw=False):
        if redraw:
            print(f"\033[{len(self.options) + 1}F", end='')
        print(self.title)
        for index, option in enumerate(self.options):
            prefix = highlight_text(">", 31) if index == self.selected_index else " "
            option = highlight_text(option, 7) if index == self.selected_index else option
            print(f"{prefix}  {option}")

    def clear_menu(self):
        space = 0
        for i in self.options:
            if len(i) > space:
                space = len(i)
        print(f"\033[{len(self.options) + 1}F", end='')
        for _ in range(len(self.options) + 1):
            print(" " * (space + 3))
        print(f"\033[{len(self.options) + 1}F", end='')

    def read_key(self):
        key = msvcrt.getch()
        if key == b'\xe0':
            key = msvcrt.getch()
            return key
        return key

    def handle_input(self):
        while True:
            key = self.read_key()
            if key == b'H':  # Up arrow
                self.selected_index = (self.selected_index - 1) % len(self.options)
                self.display(redraw=True)
            elif key == b'P':  # Down arrow
                self.selected_index = (self.selected_index + 1) % len(self.options)
                self.display(redraw=True)
            elif key == b'\r':  # Enter
                self.clear_menu()
                return self.selected_index
            elif key == b'\x1b':  # ESC
                self.clear_menu()
                return -1