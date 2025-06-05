import configparser
import os

CONFIG_FILE = 'config.ini'

def load_config():
    config = configparser.ConfigParser()
    if not os.path.exists(CONFIG_FILE):
        # สร้างไฟล์ config.ini พร้อมค่าเริ่มต้น
        with open(CONFIG_FILE, 'w') as f:
            f.write(
                "[Rendering]\n"
                "line_thickness = 1\n"
                "text_size = 1\n"
                "text_bold = 1\n"
                "point_size = 3\n\n"
                "[Grading]\n"
                "distance_threshold = 130\n"
                "adj = 10\n\n"
                "[Camera]\n"
                "fps = 30\n"
                "analysis_interval = 0.1\n"
            )
    config.read(CONFIG_FILE)

def save_config(config):
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)