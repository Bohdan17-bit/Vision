import logging
from PIL import ImageFont
from jsonhandler import JSONHandler

# Налаштування логування
logging.basicConfig(
    level=logging.DEBUG,
    filename='fonts_manager_logs.txt',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class FontsManager:
    def __init__(self):
        self.dict_names_path = {}
        self.json_handler = JSONHandler()
        self.path = "FontsPath.txt"
        self.alphabet = "abcdefghijklmnopqrstuvwxyz"
        logging.info("Initializing FontsManager...")
        self.read_fonts_from_file()
        self.calculate_default_font_and_size()

    def parse_fonts(self, font_data):
        for line in font_data:
            if 'C:\\' in line:
                parts = line.split('C:\\', 1)
                font_name = parts[0].strip()
                font_path = 'C:\\' + parts[1].strip()
                self.dict_names_path[font_name] = font_path
                logging.debug(f"Parsed font: {font_name}, Path: {font_path}")
            else:
                logging.warning(f"Cannot parse the string: {line}")

    def read_fonts_from_file(self):
        try:
            logging.info(f"Reading fonts from file: {self.path}")
            with open(self.path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                self.parse_fonts(lines)
        except FileNotFoundError:
            logging.error(f"The file {self.path} was not found!")
        except Exception as e:
            logging.error(f"Error reading fonts file: {e}")

    def calculate_default_font_and_size(self):
        self.json_handler.create_file_if_does_not_exist()
        if self.json_handler.find_combination_font("Times New Roman", 14, 100):
            logging.info("Default font 'Times New Roman' with size 14 already exists.")
        else:
            logging.info("Calculating default font and size...")
            w_basic, h_basic = self.get_average_size_letters_font_and_size("Times New Roman", 14, 100)
            self.json_handler.save_new("Times New Roman", 14, w_basic, h_basic, 100)

    def get_coefficient_font_letter(self, font_name, font_size, new_dpi):
        try:
            standard_times_14 = self.json_handler.find_combination_font("Times New Roman", 14, 100)

            standard_w = standard_times_14["size_width"]
            standard_h = standard_times_14["size_height"]

            found_combination = self.json_handler.find_combination_font(font_name, font_size, new_dpi)

            if found_combination:
                found_w = found_combination["size_width"]
                found_h = found_combination["size_height"]
                logging.debug(f"Found font in JSON: {found_combination}")

                if found_combination["font_name"] == standard_times_14["font_name"] and found_combination["font_size"] == standard_times_14["font_size"]:
                    if found_combination["dpi"] == standard_times_14["dpi"]:
                        logging.debug("Font matches default configuration. Coefficient=1")
                        return 1
                    else:
                        standard_average_size = (standard_w + standard_h) / 2
                        found_average_size = (found_w + found_h) / 2
                        cf = standard_times_14["dpi"] / found_combination["dpi"]
                        standard_average_size *= cf
                        coefficient = found_average_size / standard_average_size
                        logging.debug(f"Calculated coefficient: {coefficient}")
                        return coefficient

            w_cm_letter, h_cm_letter = self.get_average_size_letters_font_and_size(font_name, font_size, new_dpi)
            if w_cm_letter is None or w_cm_letter == 0:
                logging.warning(f"Width of letters for font {font_name} is zero or None.")
                return 1

            self.json_handler.save_new(font_name, font_size, w_cm_letter, h_cm_letter, new_dpi)
            found_average_size = (w_cm_letter + h_cm_letter) / 2
            standard_average_size = (standard_w + standard_h) / 2
            cf = standard_times_14["dpi"] / new_dpi
            standard_average_size *= cf
            coefficient = standard_average_size / found_average_size
            logging.debug(f"Final coefficient: {coefficient}")
            return coefficient
        except Exception as e:
            logging.error(f"Error calculating coefficient: {e}")
            return 1

    def get_average_size_letters_font_and_size(self, new_font, new_size, new_dpi):
        total_w_cm = 0
        total_h_cm = 0
        logging.info(f"Calculating average letter size for font: {new_font}, Size: {new_size}, DPI: {new_dpi}")
        for letter in self.alphabet:
            try:
                w_letter, h_letter = self.get_size_letter_into_cm(letter, new_font, new_size, new_dpi)
                total_w_cm += w_letter
                total_h_cm += h_letter
            except Exception as e:
                logging.error(f"Error calculating size for letter '{letter}': {e}")
        average_w_letter = total_w_cm / len(self.alphabet)
        average_h_letter = total_h_cm / len(self.alphabet)
        logging.debug(f"Average letter size: Width={average_w_letter}, Height={average_h_letter}")
        return average_w_letter, average_h_letter

    def get_size_letter_into_cm(self, letter, font, size, dpi):
        width_px, height_px = self.calculate_size_letter(letter, font, size)
        width_cm = (width_px / dpi) * 2.54
        height_cm = (height_px / dpi) * 2.54
        return width_cm, height_cm

    def calculate_size_letter(self, letter, font, size):
        try:
            if size is None or size <= 0:
                size = 14
            if not font:
                font = "Times New Roman"

            if font not in self.dict_names_path:
                logging.warning(f"Font {font} not found, defaulting to 'Times New Roman'.")
                font = "Times New Roman"

            complex_path = self.dict_names_path[font]

            if not letter:
                raise ValueError("The symbol was not found.")

            font_object = ImageFont.truetype(complex_path, size)
            bbox = font_object.getbbox(letter)
            width_px = bbox[2] - bbox[0]
            height_px = bbox[3] - bbox[1]
            return width_px, height_px
        except Exception as e:
            logging.error(f"Error calculating size for letter '{letter}' with font '{font}': {e}")
            return 0, 0
