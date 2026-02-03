import json
import os

class Config:
    def __init__(self, path="config.json"):
        self.path = path
        self.data = {
            "download_path": "~/Downloads",
            "cookies_path": "",
            "safe_mode": True
        }
        self.load()

    def load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    # Merge missing keys
                    for k, v in self.data.items():
                        if k not in loaded_data:
                            loaded_data[k] = v
                    self.data = loaded_data
            except (json.JSONDecodeError, OSError):
                self.save()
        else:
            self.save()

    def save(self):
        try:
            with open(self.path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4)
        except OSError:
            pass

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value):
        self.data[key] = value
        self.save()
