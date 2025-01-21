import json
import os


class JSONHandler:

    def __init__(self):
        self.data = []
        self.path = "fonts.json"
        self.create_file_if_does_not_exist()
        self.read_fonts()

    def read_fonts(self):
        try:
            with open(self.path, 'r') as file:
                self.data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            self.data = []

    def find_combination_font(self, font_name, font_size, dpi):
        for font in self.data:
            if font["font_name"] == font_name and font["font_size"] == font_size and font["dpi"] == dpi:
                return font
        return []

    def save_new(self, name, size, w_cm, h_cm, dpi):
        data_to_save = {
            "font_name": name,
            "font_size": size,
            "size_width": round(w_cm, 2),
            "size_height": round(h_cm, 2),
            "dpi": dpi
        }

        self.data.append(data_to_save)

        with open(self.path, 'w') as file:
            json.dump(self.data, file, indent=4)

    def create_file_if_does_not_exist(self):
        with open(self.path, "w") as file:
            json.dump([], file)
