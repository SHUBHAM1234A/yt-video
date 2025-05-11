import keyboard

def highlight_text(text, color_code):
    return f"\033[{color_code}m{text}\033[0m"

if not __import__("sys").stdout.isatty():
    for _ in dir():
        if isinstance(_, str) and _[0] != "_":
            locals()[_] = ""
else:
    if __import__("platform").system() == "Windows":
        kernel32 = __import__("ctypes").windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        del kernel32

class Menu:
    def __init__(self, title, options):
        self.title = title
        self.options = options
        self.selected_index = 0
        self.display()

    def clear_menu(self):
        space = 0
        for i in self.options:
            if len(i) > space:
                space = len(i)
        print(f"\033[{len(self.options) + 1}F", end='')
        for _ in range(len(self.options) + 1):
            print(" " * (space + 3))
        print(f"\033[{len(self.options) + 1}F", end='')
    def display(self, redraw=False):
        if redraw:
            print(f"\033[{len(self.options) + 1}F", end='')
        print(self.title)

        for index, option in enumerate(self.options):
            if index == self.selected_index:
                print(f"{highlight_text('>', 31)}  {highlight_text(option, 7)}")
            else:
                print(f"   {option}")

    def handle_input(self):
        while True:
            event = keyboard.read_event(suppress=True)
            if event.event_type == keyboard.KEY_DOWN:
                if event.name == 'down':
                    self.selected_index = (self.selected_index + 1) % len(self.options)
                    self.display(redraw=True)
                elif event.name == 'up':
                    self.selected_index = (self.selected_index - 1) % len(self.options)
                    self.display(redraw=True)
                elif event.name == 'enter':
                    self.clear_menu()
                    return self.selected_index
                elif event.name == 'esc':
                    self.clear_menu()
                    return -1