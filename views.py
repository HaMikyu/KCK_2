from pynput import keyboard
import curses
from unidecode import unidecode
from browserTerminal import CodeBrowser
from program import Program

def main_ui(stdscr, controller):
    curses.curs_set(0)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    stdscr.clear()
    options = ['View Current Settings', 'Edit Settings', 'Start Recording', 'Search directory','Save and Exit']
    current_option = 0

    while True:
        if controller.main_ui==False:
            continue
        stdscr.clear()
        stdscr.addstr(0, 0, "Select an Option:")

        for idx, option in enumerate(options):
            if idx == current_option:
                stdscr.addstr(idx + 2, 0, f"> {option.capitalize()}", curses.color_pair(1))
            else:
                stdscr.addstr(idx + 2, 0, f"  {option.capitalize()}")

        stdscr.addstr(len(options) + 2, 0, "Press 'Escape' to exit the menu without saving.")

        stdscr.refresh()
        try:
            key = stdscr.getkey()
        except curses.error:
            key = ''

        if key == 'KEY_DOWN' and current_option < len(options) - 1:
            current_option += 1
        elif key == 'KEY_UP' and current_option > 0:
            current_option -= 1
        elif key == '\n':
            if current_option == 0:
                view_settings(stdscr, controller)
            elif current_option == 1:
                edit_settings(stdscr, controller)
            elif current_option == 2:
                stdscr.clear()
                controller.main_ui = False
                program = Program(controller, stdscr)
                program.start()
                curses.endwin()

            elif current_option == 3:
                controller.main_ui =False
                CodeBrowser(controller.config['path']).run()
                controller.main_ui = True
            elif current_option == 4:
                controller.save_json()
                curses.endwin()
                break
        elif key == '\x1b':
            curses.endwin()
            exit()


def view_settings(stdscr, controller):
    curses.start_color()
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    stdscr.clear()
    stdscr.addstr(0, 0, "Current Settings:")
    for idx, (key, value) in enumerate(controller.config.items()):
        stdscr.addstr(idx + 1, 0, f"{key.capitalize()}: {value}")
    stdscr.addstr(len(controller.config) + 2, 0, "Press any key to return to menu.")
    stdscr.refresh()
    key=''
    while key =='':
        try:
            key = stdscr.getkey()
        except curses.error:
            key = ''

def edit_settings(stdscr, controller):
    curses.start_color()
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    stdscr.clear()
    stdscr.addstr(0, 0, "Edit Settings (Use arrow keys to navigate, Enter to edit, Escape to exit):")
    keys = list(controller.config.keys())
    current_edit = 0
    current_subedit = 0
    current_input = ""
    current_submenu=""
    editing = False
    sub_menu=False
    photo_formats=['png','jpg','jpeg']
    bools=['true','false']

    def on_press(key):
        nonlocal current_input, editing
        print(key)
        key_str = format(key)
        key_str = key_str.lower().strip()

        # sometimes weird characters appear
        if key_str.startswith(r"\\"):
            return

        key_str = key_str.replace("'", "")
        print(key_str)
        if len(key_str) == 3:
            key_str = key_str[1:-1]
        key_str = unidecode(key_str)

        if key_str in ['#', '@']:
            return

        current_input = key_str
        controller.config[keys[current_edit]] = key_str
        editing=False
        curses.curs_set(0)
        return False

    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "Edit Settings (Use arrow keys to navigate, Enter to edit, Escape to exit):")

        for idx, key in enumerate(keys):
            if idx == current_edit % len(keys):
                stdscr.addstr(idx + 1, 0, f"-> {key.capitalize()}: {controller.config[key]}", curses.color_pair(1))
            else:
                stdscr.addstr(idx + 1, 0, f"  {key.capitalize()}: {controller.config[key]}")

        if editing:
            if current_input.lower() in bools:
                curses.curs_set(0)
                sub_menu=True
                if current_subedit==-1:
                    current_subedit=bools.index(current_input.lower())
                for x1 in range(1,len(bools)+1):
                    if x1-1 == current_subedit % len(bools):
                        stdscr.addstr(x1+ 1+len(keys), 0, f"-> {bools[x1-1].capitalize()}",
                                      curses.color_pair(1))
                        current_submenu = bools[x1-1].lower() =='true'
                    else:
                        stdscr.addstr(x1+ 1+len(keys), 0, f"{bools[x1-1].capitalize()}")

            elif current_input.lower() in photo_formats:
                curses.curs_set(0)
                sub_menu = True
                if current_subedit == -1:
                    current_subedit = photo_formats.index(current_input.lower())
                for x1 in range(1, len(photo_formats) + 1):
                    if x1 - 1 == current_subedit % len(photo_formats):
                        stdscr.addstr(x1 + 1 + len(keys), 0, f"-> {photo_formats[x1 - 1]}",
                                      curses.color_pair(1))
                        current_submenu = photo_formats[x1 - 1].lower()
                    else:
                        stdscr.addstr(x1 + 1 + len(keys), 0, f"{photo_formats[x1 - 1]}")
            elif keys[current_edit]=='key':
                curses.curs_set(0)
                stdscr.addstr(len(keys) + 2, 0, f"Press a new button: {current_input}")
            else:
                stdscr.addstr(len(keys) + 2, 0, f"Current input: {current_input}")
                stdscr.move(len(keys) + 2, len(f"Current input: {current_input}"))

        stdscr.refresh()

        if editing and keys[current_edit] == 'key':
            with keyboard.Listener(
                    on_press=on_press) as listener:
                listener.join()
        else:
            try:
                key = stdscr.getkey()
            except curses.error:
                key = ''

        if key == 'KEY_DOWN':
            curses.curs_set(0)
            if not sub_menu:
                editing = False
                current_edit += 1
            else:
                current_subedit += 1

        elif key == 'KEY_UP':
            curses.curs_set(0)
            if not sub_menu:
                editing = False
                current_edit -= 1
            else:
                current_subedit -= 1

        if "KEY_" in key:
            key = ""

        if key == '\n' and not editing:
            curses.curs_set(1)
            current_input = str(controller.config[keys[current_edit]])
            editing = True
            current_subedit = -1
        elif key == '\n' and editing:
            if not sub_menu:
                controller.config[keys[current_edit]] = current_input
            else:
                controller.config[keys[current_edit]] = current_submenu
            current_input = ""
            editing = False
            sub_menu = False
            curses.curs_set(0)
        elif key == '\x1b':
            if editing:
                curses.curs_set(0)
                editing = False
                sub_menu = False
            else:
                break
        elif key == '\b':
            if current_input and not sub_menu:
                current_input = current_input[:-1]
        elif key.isprintable() and editing and keys[current_edit] != 'key':
            current_input += key

    curses.curs_set(0)