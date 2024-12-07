import sys
import threading
import pygame
from controller import Controller
from program import Program
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PyQt5.QtWidgets import QFileDialog, QComboBox, QLineEdit, QFormLayout, QPushButton, QDialog
from unidecode import unidecode
from pynput import keyboard
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices
import os

class ConfigDialog(QDialog):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setWindowTitle("Edit Config Options")

        layout = QFormLayout()

        self.inputs = {}
        for key, value in self.controller.config.items():
            if key == 'path':
                path_button = QPushButton(f"Select {key}", self)
                path_button.clicked.connect(self.select_path)
                layout.addRow(f"{key}:", path_button)
                self.inputs[key] = path_button
            elif key == 'key':
                mock_button = QPushButton(f"{value}", self)
                mock_button.clicked.connect(self.mockup_function)
                layout.addRow(f"{key}:", mock_button)
                self.inputs[key] = mock_button
            elif isinstance(value, bool) or str(value).lower() == "true" or str(value).lower() == "false":
                combo_box = QComboBox()
                combo_box.addItems(["True", "False"])
                combo_box.setCurrentText("True" if str(value).lower() == "true" else "False")
                combo_box.currentTextChanged.connect(self.on_text_changed)
                layout.addRow(f"{key}:", combo_box)
                self.inputs[key] = combo_box
            elif value in ['png', 'jpg', 'jpeg']:
                combo_box = QComboBox()
                combo_box.addItems(['png', 'jpg', 'jpeg'])
                combo_box.setCurrentText(value)
                combo_box.currentTextChanged.connect(self.on_text_changed)
                layout.addRow(f"{key}:", combo_box)
                self.inputs[key] = combo_box
            else:
                line_edit = QLineEdit(str(value))
                line_edit.textChanged.connect(self.on_text_changed)
                layout.addRow(f"{key}:", line_edit)
                self.inputs[key] = line_edit
        save_button = QPushButton("Save JSON")
        save_button.clicked.connect(self.save_json)
        layout.addWidget(save_button)

        self.setLayout(layout)

    def select_path(self):
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.Directory)
        file_dialog.setOption(QFileDialog.ShowDirsOnly, True)
        if file_dialog.exec_():
            selected_path = file_dialog.selectedFiles()[0]
            self.controller.config['path'] = selected_path
            self.inputs['path'].setText(selected_path)

    def mockup_function(self):

        def on_press(key):
            key_str = format(key)
            key_str = key_str.lower().strip()

            if key_str.startswith(r"\\"):
                return

            key_str = key_str.replace("'", "")
            print(key_str)
            if len(key_str) == 3:
                key_str = key_str[1:-1]
            key_str = unidecode(key_str)

            if key_str in ['#', '@']:
                return

            self.controller.config['key'] = key_str
            return False

        with keyboard.Listener(
                on_press=on_press) as listener:
            listener.join()

        class MyDialog(QDialog):
            def __init__(self,key):
                super().__init__()
                self.key = key
                self.setWindowTitle('Key was set!')
                label = QLabel(f"You have set {self.key} as a stop key!\nClose this window to refresh settings.", self)
                ok_button = QPushButton("OK", self)
                ok_button.clicked.connect(self.accept)
                layout = QVBoxLayout()
                layout.addWidget(label)
                layout.addWidget(ok_button)
                self.setLayout(layout)

        dialog = MyDialog(self.controller.config['key'])
        dialog.exec_()


    def on_text_changed(self):
        for key, input_field in self.inputs.items():
            if isinstance(input_field, QComboBox):
                new_value = input_field.currentText()
                if new_value == "True":
                    new_value = True
                elif new_value == "False":
                    new_value = False
            else:
                new_value = input_field.text()

            self.controller.config[key] = str(new_value)

    def save_json(self):
        self.controller.save_json()


class WorkerThread(QThread):
    update_signal = pyqtSignal(str)

    def __init__(self, program):
        super().__init__()
        self.program = program

    def run(self):
        self.program.start()


class MainUI(QWidget):
    def __init__(self):
        super().__init__()
        self.controller = Controller()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Recording Program')
        self.setGeometry(100, 100, 400, 300)
        layout = QVBoxLayout()
        self.label = QLabel("Program is ready to start", self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("""
            color: white;
            background-color: #333333;
            font-size: 16px;
            padding: 10px;
            border-radius: 8px;
        """)
        layout.addWidget(self.label)
        self.start_button = QPushButton('Start Program', self)
        self.start_button.setStyleSheet("""
            background-color: #4CAF50;
            color: white;
            font-size: 14px;
            padding: 10px;
            border-radius: 8px;
        """)
        self.start_button.clicked.connect(self.start_program)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton('Stop Recording', self)
        self.stop_button.setStyleSheet("""
            background-color: #f44336;
            color: white;
            font-size: 14px;
            padding: 10px;
            border-radius: 8px;
        """)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_recording)
        layout.addWidget(self.stop_button)

        self.config_button = QPushButton('Edit Config', self)
        self.config_button.setStyleSheet("""
            background-color: #2196F3;
            color: white;
            font-size: 14px;
            padding: 10px;
            border-radius: 8px;
        """)
        self.config_button.clicked.connect(self.open_config_dialog)
        layout.addWidget(self.config_button)

        self.open_config_path_button = QPushButton('Open Config Path', self)
        self.open_config_path_button.setStyleSheet("""
            background-color: #9C27B0;
            color: white;
            font-size: 14px;
            padding: 10px;
            border-radius: 8px;
        """)
        self.open_config_path_button.clicked.connect(self.open_config_path)
        layout.addWidget(self.open_config_path_button)

        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        self.setLayout(layout)

    def update_labels(self, x, y, left_button, right_button, pressed_keys, fps, time):
        if self.program.is_running:
            self.label.setText(f"X: {x}\t Y: {y}\n Left: {left_button}\t Right: {right_button}\n"
                               f"Keys: {pressed_keys}\n FPS: {round(fps, 2)}\t Time: {round(time, 2)}")
        else:
            self.inner_stop()

    def start_program(self):
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.label.setText("Program is starting...")

        self.program = Program(self.controller, window=self)

        self.worker_thread = WorkerThread(self.program)
        self.worker_thread.update_signal.connect(self.update_labels)
        self.worker_thread.start()

    def inner_stop(self):
        self.stop_button.setEnabled(False)
        self.label.setText("Recording saved.")
        self.start_button.setEnabled(True)

    def stop_recording(self):
        if hasattr(self, 'program') and self.program:
            self.program.stop_recording()
            self.stop_button.setEnabled(False)
            self.label.setText("Recording saved.")
            self.start_button.setEnabled(True)

    def open_config_dialog(self):
        dialog = ConfigDialog(self.controller)
        dialog.exec_()

    def open_config_path(self):
        config_path = self.controller.config['path']

        if os.path.exists(config_path):

            os.startfile(config_path)
        else:
            self.label.setText("Config path not found.")


def main():
    app = QApplication(sys.argv)
    main_ui = MainUI()
    main_ui.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
