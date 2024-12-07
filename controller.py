import os
from screeninfo import get_monitors
import json
import requests

class Controller:
    def __init__(self):
        self.config = {
            'program': 'notepad.exe',
            'title': 'Notatnik',
            'path': os.path.dirname(os.path.realpath(__file__)) + r'\ruchy',
            'key':'key.home',
            'monitor': 1,
            'first_person_view': False,
            'record_screen': False,
            'compress_image': True,
            'save_format': "jpg",
            'quality': 75,
            'res_x': 1280,
            'res_y': 720,
            "use_terminal": False,
        }
        self.load_json()
        self.set_variables()
        self.main_ui=True
        self.found_title=""
    def set_variables(self):
        self.config['path'] = self.config['path'].strip()
        self.config['width'] = get_monitors()[self.config['monitor'] - 1].width
        self.config['height'] = get_monitors()[self.config['monitor'] - 1].height

    def download_file_from_google_drive(self,file_id, destination):
        URL = "https://drive.google.com/uc?export=download"
        session = requests.Session()
        response = session.get(URL, params={'id': file_id}, stream=True)
        for key, value in response.cookies.items():
            if key.startswith('download_warning'):
                response = session.get(URL, params={'id': file_id, 'confirm': value}, stream=True)
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(1024):
                if chunk:
                    f.write(chunk)

    def load_json(self):
        if not os.path.isfile('config.json'):
            with open('config.json', 'w') as f:
                json.dump(self.config, f, indent=2)
        try:
            with open('config.json', 'r') as f:
                self.config = json.load(f)
        except:
            raise FileNotFoundError('config.json has problems!')

        if not os.path.isfile("clock.wav"):
            try:
                self.download_file_from_google_drive("1xcBbdgl9pfl0ME0Gp7hrlp0rlomCN2TX",'clock.wav')
            except:
                raise Exception("'clock.wav' doesn't exist and can't be downloaded!")

    def save_json(self):
        with open('config.json', 'w') as f:
            json.dump(self.config, f, indent=2)