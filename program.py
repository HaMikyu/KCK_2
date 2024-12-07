import time
import os
import threading
import psutil
from pynput import keyboard, mouse
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import curses
from pygetwindow import getAllTitles as getAllWindows
from screeninfo import get_monitors
from pyautogui import click
from windows_capture import WindowsCapture, Frame, InternalCaptureControl
import cv2
from unidecode import unidecode
from timeit import default_timer as timer
import xlsxwriter
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import QTimer

class Program:
    def __init__(self, controller, window=None):
        self.controller = controller
        self.pressed_keys = []
        self.is_running = True
        self.x = 0
        self.y = 0
        self.fps = 0
        self.time = 0
        self.frames = 0
        self.right_button = False
        self.left_button = False
        self.counter = 2
        self.monitor = 1
        self.current_photo = "Null"
        pygame.mixer.init()
        self.config = controller.config
        self.use_terminal = self.config['use_terminal']
        self.width = get_monitors()[self.monitor - 1].width
        self.height = get_monitors()[self.monitor - 1].height
        self.middle_x = self.width / 2
        self.middle_y = self.height / 2
        if self.config['use_terminal']:
            self.stdscr = window
            self.stdscr.nodelay(True)
            self.stdscr.clear()
            self.stdscr.addstr(0, 0, f"You can run your program now!\n", curses.A_REVERSE)
            self.stdscr.refresh()
        else:
            self.window = window

    def start(self):
        if os.path.isdir(self.controller.config['path'])==False:
            os.mkdir(self.controller.config['path'])
        folder_contents = os.listdir(self.controller.config['path'])
        max_index = 0
        try:
            for item in folder_contents:
                if item.startswith("analiza-"):
                    if int(item[8:]) > max_index:
                        max_index = int(item[8:])
        except FileNotFoundError:
            print("I quess you have problem with folders.")
            exit()
        max_index = max_index + 1
        analysis_folder = os.path.join(self.controller.config['path'], f"analiza-{max_index}")
        self.frame_folder = os.path.join(analysis_folder, f"frames")
        os.mkdir(analysis_folder)
        os.mkdir(self.frame_folder)
        self.workbook = xlsxwriter.Workbook(os.path.join(analysis_folder, f"data.xlsx"))
        self.worksheet = self.workbook.add_worksheet()
        self.worksheet.write(f'A1', "Filename")
        self.worksheet.write(f'B1', "X")
        self.worksheet.write(f'C1', "Y")
        self.worksheet.write(f'D1', "LeftMouseButton")
        self.worksheet.write(f'E1', "RightMouseButton")
        self.worksheet.write(f'F1', "Keys")
        if self.config['use_terminal']:
            self.stdscr.addstr(1, 0, f"Waiting for {self.controller.config['program'][:-4]}...\n")
            self.stdscr.refresh()
        #print()
        lock = True
        while lock:
            if self.process_exists(True):
                lock = False

        lock = True
        while lock:
            result = self.get_title(self.controller.config['title'])
            if result is None:
                pass
            else:
                self.found_title = result
                lock = False
        #print()
        if self.config['use_terminal']:
            self.stdscr.addstr(2, 0, f"Found '{result}'!\n")
            self.stdscr.addstr(3, 0, f"Countdown...")
            self.stdscr.refresh()
        else:
            self.window.label.setText(f"Found '{result}'!\nCountdown...")
        self.countdown()

    def countdown(self):
        pygame.mixer.music.load("clock.wav")
        pygame.mixer.music.play(loops=0)
        time.sleep(4.5)
        click()
        self.start_time = timer()
        self.listener_k = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release)
        self.listener_k.start()

        self.mouse_thread = threading.Thread(target=self.mouse_listener)
        self.mouse_thread.start()

        self.record(self.found_title)

    def update_ui(self):
        if self.config['use_terminal'] and self.is_running:
            self.stdscr.clear()
            self.stdscr.addstr(0, 0, f"Recording Program - {self.found_title}")
            self.stdscr.addstr(2, 0, f"Mouse Position: ({int(self.x)}, {int(self.y)})")
            self.stdscr.addstr(3, 0, f"Left Mouse Button: {'Pressed' if self.left_button else 'Released'}")
            self.stdscr.addstr(4, 0, f"Right Mouse Button: {'Pressed' if self.right_button else 'Released'}")
            self.stdscr.addstr(5, 0, f"Keys Pressed: {str(self.pressed_keys)}")
            self.stdscr.addstr(6, 0, f"FPS: {round(self.fps, 2)}")
            self.stdscr.addstr(7, 0, f"Recording Time: {round(self.time, 2)} seconds")
            self.stdscr.refresh()
        else:
            self.window.update_labels(self.x, self.y, self.left_button, self.right_button, self.pressed_keys, self.fps,
                                      self.time)

    def on_press(self, key):
        key_str = format(key)
        key_str = key_str.lower().strip()

        # sometimes weird characters appear
        if key_str.startswith(r"\\"):
            return

        key_str = key_str.replace("'","")
        if len(key_str) == 3:
            key_str = key_str[1:-1]
        key_str = unidecode(key_str)

        if key_str in ['#', '@']:
            return

        if self.config['key'] in key_str:
            self.stop_recording()
            return

        for pressed_key in self.pressed_keys:
            if 'x0' in pressed_key:
                self.pressed_keys.remove(pressed_key)
            if 'x1' in pressed_key:
                self.pressed_keys.remove(pressed_key)

        if key_str not in self.pressed_keys:
            self.pressed_keys.append(key_str)

    def on_release(self, key):
        key_str = format(key)
        key_str = key_str.lower().strip()
        if len(key_str) == 3:
            key_str = key_str[1:-1]
        try:
            self.unidecode = unidecode(key_str)
            key_str = self.unidecode
            self.remove = self.pressed_keys.remove(key_str)
        except:
            pass

    def save_to_file(self):
        self.x1 = int(self.x)
        self.y1 = int(self.y)

        self.worksheet.write(f'A{self.counter}', self.current_photo)
        self.worksheet.write(f'B{self.counter}', self.x1)
        self.worksheet.write(f'C{self.counter}', self.y1)
        self.worksheet.write(f'D{self.counter}', self.left_button)
        self.worksheet.write(f'E{self.counter}', self.right_button)
        self.worksheet.write(f'F{self.counter}', str(self.pressed_keys))
        self.counter += 1
        if 'key.scroll_down' in self.pressed_keys:
            self.pressed_keys.remove('key.scroll_down')
        if 'key.scroll_up' in self.pressed_keys:
            self.pressed_keys.remove('key.scroll_up')

        self.update_ui()
        self.x = 0
        self.y = 0

    def mouse_listener(self):
        with mouse.Listener(on_move=self.on_move, on_click=self.on_click, on_scroll=self.on_scroll) as self.listener_m:
            self.listener_m.join()

    def process_exists(self, print_msg=False):
        process_name = self.controller.config['program']
        for proc in psutil.process_iter():
            try:
                if process_name[:-4].lower() in proc.name().lower():
                    if print_msg:
                        pass
                        #print(f"DETECTED {process_name[:-4]}")
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False

    def get_title(self, title):
        title = title.lower()
        title = title.strip()
        for window_title in getAllWindows():
            if title in window_title.lower().strip():
                return window_title.strip()

    def record(self, title):
        self.iHaveWorked = False
        if self.config['record_screen'] == False:
            capture = WindowsCapture(
                cursor_capture=None,
                draw_border=None,
                monitor_index=None,
                window_name=title,
            )
        else:
            capture = WindowsCapture(
                cursor_capture=None,
                draw_border=None,
                monitor_index=int(self.config['monitor']),
                window_name=None,
            )

        @capture.event
        def on_frame_arrived(frame: Frame, capture_control: InternalCaptureControl):
            if not self.is_running:
                if not self.iHaveWorked:
                    #print("Stopping recording")
                    self.iHaveWorked = True
                    capture_control.stop()
                return

            self.current_photo = os.path.join(self.frame_folder, f"{self.frames}.{self.config['save_format']}")

            if self.config['compress_image'] == True:
                cv2.imwrite(self.current_photo, cv2.resize(frame.frame_buffer,
                                                           (self.config['res_x'], self.config['res_y'])),
                            [cv2.IMWRITE_JPEG_QUALITY, self.config['quality']])
            elif self.config['compress_image'] == 'resize':
                cv2.imwrite(self.current_photo, cv2.resize(frame.frame_buffer,
                                                           (self.config['res_x'], self.config['res_y'])))
            else:
                cv2.imwrite(self.current_photo, frame.frame_buffer)

            self.frames += 1
            self.time = timer() - self.start_time
            self.fps = self.frames / self.time
            self.save_to_file()

        @capture.event
        def on_closed():
            self.stop_recording()

        capture.start_free_threaded()

    def on_move(self, x, y):
        self.x += x - self.middle_x
        self.y += y - self.middle_y

    def on_click(self, x, y, button, pressed):
        if pressed:
            if "left" in str(button):
                self.left_button = True
            else:
                self.right_button = True
        else:
            if "left" in str(button):
                self.left_button = False
            else:
                self.right_button = False

    def on_scroll(self, x, y, dx, dy):
        if dy < 0:
            if 'key.scroll_down' not in self.pressed_keys:
                self.pressed_keys.append('key.scroll_down')
        else:
            if 'key.scroll_up' not in self.pressed_keys:
                self.pressed_keys.append('key.scroll_up')

    def stop_recording(self):
        if self.use_terminal ==False:
            self.window.inner_stop()
        self.workbook.close()
        self.is_running = False
        self.listener_m.stop()
        self.listener_k.stop()
        self.controller.main_ui = True


