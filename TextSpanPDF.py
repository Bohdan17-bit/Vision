
class TextSpanPDF:

    distance_to_next_span = 0

    text_span = ""

    font_span = None
    size = None
    color = ""
    background_color = ""
    flags = None

    coord_x_start = 0
    coord_y_start = 0

    coord_x_end = 0
    coord_y_end = 0

    def set_background_color(self, bg_color):
        self.background_color = bg_color

    def set_color_text(self, text_color):
        self.color = text_color

    def set_size_text(self, size_text):
        self.size = size_text

    def set_flags(self, flags):
        self.flags = flags

    def set_distance_to_next_span(self, distance):
        self.distance_to_next_span = distance

    def set_text(self, text):
        self.text_span = text

    def set_font(self, font):
        self.font_span = font

    def set_coords(self, x0, y0, x1, y1):
        self.coord_x_start = x0
        self.coord_x_end = x1
        self.coord_y_start = y0
        self.coord_y_end = y1
