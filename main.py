from controller import Controller
import curses
from views import main_ui
from views_gui import main
if __name__ == '__main__':
    controller = Controller()
    if controller.config["use_terminal"]:
        curses.wrapper(main_ui, controller)
    else:
        main()