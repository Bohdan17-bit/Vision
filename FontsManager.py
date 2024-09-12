from PIL import ImageFont


class FontsManager:
    def __init__(self):
        self.font_path = "C:/Windows/Fonts/"
        self.name = "Times New Roman"
        self.suffix = ".ttf"
        self.size = 0
        self.dpi = 0
        self.screen_pixels_in_width = 0
        self.screen_inches_in_width = 0

    def set_screen_settings(self, number_pixels, size_inches):
        self.screen_pixels_in_width = number_pixels
        self.screen_inches_in_width = size_inches

    def set_dpi(self, dpi):
        self.dpi = dpi

    def calculate_ppi(self):
        self.dpi = self.screen_pixels_in_width / self.screen_inches_in_width
        return self.dpi

    def get_size_letter_into_cm(self, width_px, height_px):
        width_cm = (width_px / self.dpi) * 2.54
        height_cm = (height_px / self.dpi) * 2.54
        return width_cm, height_cm

    def set_font(self, custom_name, custom_size):
        self.name = custom_name + self.suffix
        self.size = custom_size

    def calculate_size_letter(self, letter):
        font = ImageFont.truetype(self.font_path, self.size)
        bbox = font.getbbox(letter)
        width_px = bbox[2] - bbox[0]
        height_px = bbox[3] - bbox[1]
        return width_px, height_px


