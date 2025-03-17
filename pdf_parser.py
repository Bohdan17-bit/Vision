import fitz
import re
from TextSpan import TextSpanPDF
from PIL import Image
import io
import logging

logging.basicConfig(filename='pdf_parser.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class ParserPDF:

    def __init__(self):
        self.list_spans = []
        self.abbreviations_keys = [
            "etc.", "etc", "Etc", "ETC.", "e.g.", "e.g", "i.e.", "i.e", "vs.", "vs", "a.m.", "p.m."
        ]

        self.abbreviations = {
            "etc.": "et cetera",
            "etc": "et cetera",
            "e.g.": "for example",
            "e.g": "for example",
            "i.e.": "that is",
            "i.e": "that is",
            "vs.": "versus",
            "vs": "versus",
            "a.m.": "am",
            "am": "am",
            "pm": "pm",
            "p.m.": "pm",
            "approx.": "approximately",
            "Dr.": "Doctor",
            "Mr.": "Mister",
            "Mrs.": "Mistress",
            "Ph.D.": "Doctor of Philosophy",
            "B.Sc.": "Bachelor of Science",
            "M.Sc.": "Master of Science",
            "Inc.": "Incorporated",
            "Ltd.": "Limited",
            "St.": "Saint",
            "Jr.": "Junior",
            "Sr.": "Senior",
        }

    def flags_decomposer(self, flags):
        l = []
        if flags & 2 ** 0:
            l.append("superscript")
        if flags & 2 ** 1:
            l.append("italic")
        if flags & 2 ** 2:
            l.append("serifed")
        else:
            l.append("sans")
        if flags & 2 ** 3:
            l.append("monospaced")
        else:
            l.append("proportional")
        if flags & 2 ** 4:
            l.append("bold")
        return ", ".join(l)

    def points_to_cm(self, points):
        inches = points / 72.0
        cm = inches * 2.54
        return cm

    def calculate_distance(self, coords1, coords2):
        _, _, x1, y1 = coords1
        x2, y2, _, _ = coords2
        distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        return self.points_to_cm(distance)  # Convert distance to centimeters

    def convert_color_to_hex(self, color):
        if isinstance(color, tuple):
            return "#%02x%02x%02x" % tuple(int(c) for c in color)
        elif isinstance(color, int):
            return "#%02x%02x%02x" % ((color >> 16) & 0xFF, (color >> 8) & 0xFF, color & 0xFF)
        return "#000000"

    def get_pixel_color(self, image, x, y):
        pixel = image.getpixel((x, y))
        return self.convert_color_to_hex(pixel)

    def extract_text_elements_with_coordinates(self, page, image, zoom_f=3):
        text = page.get_text("rawdict")
        previous_word_coords = None

        for block in text["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:

                        word = ""
                        word_bbox = [None, None, None, None]

                        font = span["font"]
                        size = span["size"]
                        color = span["color"]
                        color_hex = self.convert_color_to_hex(color)
                        flags = self.flags_decomposer(span["flags"])

                        current_font = font
                        current_size = size
                        current_color = color_hex
                        current_bgcolor = self.get_pixel_color(image, int(span["bbox"][2] * zoom_f) - 5,
                                                               int(span["bbox"][3] * zoom_f) - 5)
                        current_flags = flags

                        for char in span["chars"]:
                            character = char["c"]
                            bbox = char["bbox"]

                            pixel_x = int(bbox[2] * zoom_f) - 5
                            pixel_y = int(bbox[3] * zoom_f) - 5
                            bgcolor_hex = self.get_pixel_color(image, pixel_x, pixel_y)

                            # Якщо слово починається з точки, пропускаємо її тільки якщо це не дата чи число
                            if word == "" and character == ".":
                                if not re.match(r"^\d{1,2}\.\d{1,2}\.\d{4}$", word):  # перевірка на дату
                                    continue

                            # Якщо символ - це пробіл або розділовий знак
                            if character.isspace() or not (character.isalnum() or character in "-.'`’"):
                                if word:
                                    # Перевіряємо кількість розділових знаків у слові
                                    punctuation_count = len(re.findall(r"[-.'`’]", word))

                                    # Якщо більше двох розділових знаків - пропускаємо це слово
                                    if punctuation_count > 2:
                                        word = ""
                                        word_bbox = [None, None, None, None]
                                        continue

                                    # Заміна абревіатур
                                    word = self.replace_abbreviations(word)
                                    self.append_text_span(word, word_bbox, current_font, current_size, current_color,
                                                          current_bgcolor, current_flags, previous_word_coords)
                                    previous_word_coords = word_bbox
                                    word = ""
                                    word_bbox = [None, None, None, None]
                                continue

                            if not word:
                                word_bbox[0] = bbox[0]
                                word_bbox[1] = bbox[1]
                            word += character
                            word_bbox[2] = bbox[2]
                            word_bbox[3] = bbox[3]

                        if word:
                            punctuation_count = len(re.findall(r"[-.'`’]", word))

                            if punctuation_count <= 2:
                                word = self.replace_abbreviations(word)
                                self.append_text_span(word, word_bbox, current_font, current_size, current_color,
                                                      current_bgcolor, current_flags, previous_word_coords)
                                previous_word_coords = word_bbox
                            word = ""
                            word_bbox = [None, None, None, None]

    def replace_abbreviations(self, word):
        # Видалення точок перед цифрами або у числових значеннях (якщо це не дата)
        word = word.lstrip(".")

        # Перевірка, чи це не дата або число
        if re.match(r"^\d{1,2}\.\d{1,2}\.\d{4}$", word):  # дата формату dd.mm.yyyy
            return word

        # Перевірка на інші випадки
        if word in self.abbreviations:
            return word

        word_lower = word.lower()

        if word_lower in self.abbreviations:
            return word

        return word

    def append_text_span(self, text, bbox, font, size, color, bgcolor, flags, previous_coords):
        text_span = TextSpanPDF()
        text_span.set_text(text)
        text_span.set_coords(bbox[0], bbox[2], bbox[1], bbox[3])
        text_span.set_font(font)
        text_span.set_size_text(int(size))
        text_span.set_color_text(color)
        text_span.set_background_color(bgcolor)
        text_span.set_flags(flags)

        if len(text_span.text_span) > 14:
            text_span.long = True

        if previous_coords:
            distance = self.calculate_distance(previous_coords, bbox)
            self.list_spans[-1].set_distance_to_next_span(distance)
        else:
            text_span.set_distance_to_next_span(0)

        self.list_spans.append(text_span)

    def start(self, filename):
        self.list_spans = []
        try:
            doc = fitz.open(filename)
        except Exception as e:
            logging.error(f"Не вдалося відкрити PDF файл: {e}")
            return []

        zoom_factor = 3
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            mat = fitz.Matrix(zoom_factor, zoom_factor)
            pix = page.get_pixmap(matrix=mat)
            image = Image.open(io.BytesIO(pix.tobytes("png")))
            try:
                self.extract_text_elements_with_coordinates(page, image, zoom_factor)
            except Exception as e:
                logging.error(f"Помилка при обробці сторінки {page_num + 1}: {e}")

        doc.close()
        return self.list_spans
