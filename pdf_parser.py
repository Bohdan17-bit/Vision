import json
import fitz
import re
from TextSpanPDF import TextSpanPDF
from PIL import Image
import io


class ParserPDF:

    def __init__(self):
        self.list_spans = []

    def flags_decomposer(self, flags):
        """Make font flags human readable."""
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
        """Calculate distance between two points."""
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
        word = ""
        word_bbox = [None, None, None, None]

        previous_word_coords = None

        for block in text["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        font = span["font"]
                        size = span["size"]
                        color = span["color"]
                        color_hex = self.convert_color_to_hex(color)
                        flags = self.flags_decomposer(span["flags"])

                        for char in span["chars"]:
                            character = char["c"]
                            bbox = char["bbox"]

                            pixel_x = int(bbox[2] * zoom_f) - 5
                            pixel_y = int(bbox[3] * zoom_f) - 5
                            bgcolor_hex = self.get_pixel_color(image, pixel_x, pixel_y)

                            if character.isspace() or re.match(r'[^\w\s]', character):
                                if word:
                                    text_span = TextSpanPDF()
                                    word = word.lower()
                                    text_span.set_text(word)
                                    text_span.set_coords(word_bbox[0], word_bbox[2], word_bbox[1], word_bbox[3])
                                    text_span.set_font(current_font)
                                    text_span.set_size_text(current_size)
                                    text_span.set_color_text(current_color)
                                    text_span.set_background_color(current_bgcolor)
                                    text_span.set_flags(current_flags)

                                    if previous_word_coords:
                                        distance = self.calculate_distance(previous_word_coords, word_bbox)
                                        # Store distance in the next span
                                        self.list_spans[-1].set_distance_to_next_span(distance)
                                    else:
                                        text_span.set_distance_to_next_span(0)

                                    self.list_spans.append(text_span)
                                    previous_word_coords = word_bbox
                                    word = ""
                                    word_bbox = [None, None, None, None]

                                text_span = TextSpanPDF()
                                character = character.lower()
                                text_span.set_text(character)
                                text_span.set_coords(bbox[0], bbox[2], bbox[1], bbox[3])
                                text_span.set_font(font)
                                text_span.set_size_text(size)
                                text_span.set_color_text(color_hex)
                                text_span.set_background_color(bgcolor_hex)
                                text_span.set_flags(flags)
                                text_span.set_distance_to_next_span(0)
                                self.list_spans.append(text_span)

                            else:
                                if not word:
                                    word_bbox[0] = bbox[0]
                                    word_bbox[1] = bbox[1]
                                    current_font = font
                                    current_size = size
                                    current_color = color_hex
                                    current_bgcolor = bgcolor_hex
                                    current_flags = flags

                                word += character
                                word_bbox[2] = bbox[2]
                                word_bbox[3] = bbox[3]

        if word:
            text_span = TextSpanPDF()
            word = word.lower()
            text_span.set_text(word)
            text_span.set_coords(word_bbox[0], word_bbox[2], word_bbox[1], word_bbox[3])
            text_span.set_font(current_font)
            text_span.set_size_text(current_size)
            text_span.set_color_text(current_color)
            text_span.set_background_color(current_bgcolor)
            text_span.set_flags(current_flags)

            if previous_word_coords:
                distance = self.calculate_distance(previous_word_coords, word_bbox)
                # Store distance in the next span
                self.list_spans[-1].set_distance_to_next_span(distance)
            else:
                text_span.set_distance_to_next_span(0)

            self.list_spans.append(text_span)

    def start(self, filename):
        self.list_spans = []
        doc = fitz.open(filename)
        zoom_factor = 3
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            mat = fitz.Matrix(zoom_factor, zoom_factor)
            pix = page.get_pixmap(matrix=mat)
            image = Image.open(io.BytesIO(pix.tobytes("png")))
            self.extract_text_elements_with_coordinates(page, image, zoom_factor)
        doc.close()
        return self.list_spans