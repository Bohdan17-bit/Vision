import re

from PIL import ImageFont
import json
from jsonhandler import JSONHandler


class FontsManager:
    def __init__(self):
        self.dict_names_path = {}
        self.json_handler = JSONHandler()
        self.path = "FontsPath.txt"
        self.alphabet = "abcdefghijklmnopqrstuvwxyz"
        self.read_fonts_from_file()
        self.calculate_default_font_and_size()

    def parse_fonts(self, font_data):
        for line in font_data:
            if 'C:\\' in line:
                parts = line.split('C:\\', 1)
                font_name = parts[0].strip()  # Назва шрифту
                font_path = 'C:\\' + parts[1].strip()  # Шлях до шрифту з C:\
                self.dict_names_path[font_name] = font_path
                print(f"Назва шрифту: {font_name}, Шлях: {font_path}")
            else:
                print(f"Не вдалося розпарсити рядок: {line}")

    def read_fonts_from_file(self):
        try:
            with open(self.path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                return self.parse_fonts(lines)
        except FileNotFoundError:
            print(f"Файл {self.path} не знайдено.")
            return []
        except Exception as e:
            print(f"Помилка: {e}")
            return []

    def calculate_default_font_and_size(self):
        self.json_handler.create_file_if_does_not_exist()
        if self.json_handler.find_combination_font("Times New Roman", 14, 100):
            return
        else:
            w_basic, h_basic = self.get_average_size_letters_font_and_size("Times New Roman", 14, 100)
            self.json_handler.save_new("Times New Roman", 14, w_basic, h_basic, 100)

    def get_coefficient_font_letter(self, font_name, font_size, new_dpi):

        standard_times_14 = self.json_handler.find_combination_font("Times New Roman", 14, 100)
        print(standard_times_14)

        standard_w = standard_times_14["size_width"]
        standard_h = standard_times_14["size_height"]

        found_combination = self.json_handler.find_combination_font(font_name, font_size, new_dpi)

        if found_combination:

            found_w = found_combination["size_width"]
            found_h = found_combination["size_height"]

            if found_combination["font_name"] == standard_times_14["font_name"] and found_combination["font_size"] == standard_times_14["font_size"]:

                if found_combination["dpi"] == standard_times_14["dpi"]:

                    return 1

                else:

                    standard_average_size = (standard_w + standard_h) / 2
                    found_average_size = (found_w + found_h) / 2

                    cf = standard_times_14["dpi"] / found_combination["dpi"]

                    standard_average_size *= cf

                    coefficient = found_average_size / standard_average_size

                    return coefficient

        w_cm_letter, h_cm_letter = self.get_average_size_letters_font_and_size(font_name, font_size, new_dpi)

        if w_cm_letter is None or w_cm_letter == 0:
            return 1

        self.json_handler.save_new(font_name, font_size, w_cm_letter, h_cm_letter, new_dpi)

        found_average_size = (w_cm_letter + h_cm_letter) / 2
        standard_average_size = (standard_w + standard_h) / 2

        cf = standard_times_14["dpi"] / new_dpi

        standard_average_size *= cf

        coefficient = standard_average_size / found_average_size

        return coefficient

    def get_average_size_letters_font_and_size(self, new_font, new_size, new_dpi):
        total_w_cm = 0
        total_h_cm = 0
        for letter in self.alphabet:
            w_letter, h_letter = self.get_size_letter_into_cm(letter, new_font, new_size, new_dpi)
            total_w_cm += w_letter
            total_h_cm += h_letter
        average_w_letter = total_w_cm / len(self.alphabet)
        average_h_letter = total_h_cm / len(self.alphabet)
        return average_w_letter, average_h_letter

    def get_size_letter_into_cm(self, letter, font, size, dpi):
        width_px, height_px = self.calculate_size_letter(letter, font, size)
        width_cm = (width_px / dpi) * 2.54
        height_cm = (height_px / dpi) * 2.54
        return width_cm, height_cm

    def calculate_size_letter(self, letter, font, size):
        complex_path = self.dict_names_path[font]
        font = ImageFont.truetype(complex_path, size)
        bbox = font.getbbox(letter)
        width_px = bbox[2] - bbox[0]
        height_px = bbox[3] - bbox[1]
        return width_px, height_px


