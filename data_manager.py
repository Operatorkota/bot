# data_manager.py
import json
import os
import threading

class DataManager:
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = {}
        self._lock = threading.Lock()
        self.load_data()

    def load_data(self):
        with self._lock:
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    try:
                        self.data = json.load(f)
                    except json.JSONDecodeError:
                        self.data = {}
            else:
                self.data = {}

    def save_data(self):
        with self._lock:
            temp_file_path = self.file_path + ".tmp"
            with open(temp_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
            os.replace(temp_file_path, self.file_path)

    def get(self, key, default=None):
        return self.data.get(str(key), default)

    def set(self, key, value):
        self.data[str(key)] = value
        self.save_data()

    def get_all(self):
        return self.data.copy()

    def update_all(self, data):
        self.data = data
        self.save_data()
