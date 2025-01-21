import math
import random
import urllib

import numpy as np

from ParserWeb import ParserWeb
from pdf_parser import ParserPDF
import re

from docx2pdf import convert
import os


class Model:

    list_text_spans = []

    average_saccade_latency = 150
    standard_deviation_latency = 50

    distance_to_display = 0
    width_px = 0
    height_px = 0
    DPI = 0
    diagonal_inches = 0

    path = ""
    PPI = 0

    def __init__(self):
        self.__full_time_to_read = 0
        self.__full_time_standard_deviation = 0
        self.parserPDF = ParserPDF()
        self.parserWeb = ParserWeb()

    def reset_results(self):
        self.__full_time_to_read = 0
        self.__full_time_standard_deviation = 0

    def read_text_from_pdf(self):
        self.reset_results()
        if not os.path.isfile(self.path):
            raise FileNotFoundError(f"The file {self.path} does not exist.")
        self.list_text_spans = self.parserPDF.start(self.path)

    def read_text_from_site(self, url):
        self.reset_results()
        self.list_text_spans = self.parserWeb.parse_webpage(url)

    def set_distance_to_display(self, distance_in_cm):
        self.distance_to_display = distance_in_cm

    def calculate_ppi(self):
        diagonal_pixels = math.sqrt((self.width_px * self.width_px + self.height_px * self.height_px))
        self.PPI = diagonal_pixels / self.diagonal_inches

    def set_diagonal_inches(self, size_in_inches):
        self.diagonal_inches = size_in_inches

    def set_width_px(self, width):
        self.width_px = width

    def set_height_px(self, height):
        self.height_px = height

    def set_path(self, user_path):
        self.path = user_path

    def convert_word_to_pdf(self, file_docx):
        try:
            if not file_docx.lower().endswith(".docx"):
                raise ValueError("File is not .docx")

            decoded_path = os.path.normpath(file_docx)
            new_name = os.path.splitext(decoded_path)[0] + ".pdf"

            if os.path.exists(new_name):
                print(f"Existing file is deleting...: {new_name}")
                os.remove(new_name)

            print(f"Converting the file: {decoded_path}")

            convert(decoded_path, new_name)

            self.set_path(new_name)

            print(f"The file was successfully converted: {new_name}")
            return new_name

        except Exception as e:
            print(f"Error was occurred! The file was not converted! Error: {e}")
            return e

    def split_string(self, text):
        pattern = r'\w+|\s*[^\w\s]+\s*|\s+'
        split_text = re.findall(pattern, text)
        return split_text

    def get_text_list_spans(self):
        return self.list_text_spans

    def add_average_latency_time(self):
        self.__full_time_to_read += self.average_saccade_latency

    def add_standard_deviation_latency_time(self):
        self.__full_time_standard_deviation += self.standard_deviation_latency

    def increase_general_time(self, time):
        self.__full_time_to_read += time

    def increase_general_time_sd(self, time):
        self.__full_time_standard_deviation += time

    def get_sum_time_reading(self):
        return self.__full_time_to_read

    def get_sum_standard_deviation(self):
        return self.__full_time_standard_deviation

    def calculate_launch_distance(self, next_word, prev_length):
        word_length = len(next_word)
        center_in_next_word = -word_length / 2
        launch_distance = center_in_next_word - prev_length
        return launch_distance

    def calculate_average_landing_position(self, word, d, k):
        m = 3.3 + 0.49 * d * k
        return m

    def calculate_standard_deviation(self, d, word):
        sd = 1.318 + 0.000518 * d ** 3
        return sd

    def calculate_probability_letter_landing(self, x, m, sd):
        q = math.sqrt(2 * math.pi) * sd
        ch = (x - m) ** 2
        zn = 2 * (sd * sd)
        prob = 1 / q * math.exp(-ch / zn)
        return prob

    def calculate_probability_landing(self, target_word, rest_letters, k):
        d = self.calculate_launch_distance(target_word, rest_letters)
        m = self.calculate_average_landing_position(target_word, d, k)
        sd = self.calculate_standard_deviation(d, target_word)
        word_length = len(target_word)
        center_pos = word_length / 2
        m_position = center_pos + m
        word_dict_probability = {}
        # print(f"For word <{target_word}> m position = {m_position}")
        for index, letter in enumerate(target_word):
            x = m_position - index
            # print(f"For letter {letter} in word <{target_word}> x = {round(x, 3)}")
            landing_prob = self.calculate_probability_letter_landing(x, m, sd)
            # print(f"For letter {letter} in word <{target_word}> probability = {round(landing_prob, 3)}")
            word_dict_probability[index] = landing_prob

        x = m_position - word_length
        prob = self.calculate_probability_letter_landing(x, m, sd)
        word_dict_probability[word_length] = prob
        # print(f"After word first symbol has probability : {round(prob, 3)}")

        x = m_position - word_length - 1
        prob = self.calculate_probability_letter_landing(x, m, sd)
        word_dict_probability[word_length + 1] = prob
        # print(f"After word second symbol has probability : {round(prob, 3)}")

        return word_dict_probability

    def calculate_probability_refixation(self, word, position):
        a = self.calculate_min_point_a(word)
        x = self.calculate_deviation_x(word, position)
        y = a + (0.03 * (x ** 2))
        return max(0, min(1, y))

    def calculate_deviation_x(self, word, position):
        opt_position = len(word) / 2 - 0.5
        deviation = abs(opt_position - position)
        return deviation

    def calculate_min_point_a(self, word):
        L = len(word)
        a = 0.15 * L * 0.1 - 0.0034
        return a

    def make_refixation(self, word, loc):
        time = self.calculate_mean_delay(word, loc)
        return time

    def calculate_mean_delay(self, word, loc):
        base = 80
        range = 150
        word_length = len(word)
        middle = word_length / 2
        ch = abs(loc - middle)
        zn = word_length / 2
        m = base + range * (1 - (ch / zn))
        return m

    def calculate_time_reading(self, word, loc, most_freq_word, frequency_word):
        if word.isdigit() and int(word) > 9999:
            min_time = len(word) * 400
            return min_time
        else:
            return self.calculate_lex_ident_letter(word, loc, most_freq_word, frequency_word)

    def calculate_lex_ident_general(self, word, biggest_freq, frequency_word):
        base5 = 150
        frequency_word /= biggest_freq
        word_length = len(word)
        m_ = base5 + 15 * (word_length - 5) + 40 * (1 - frequency_word)
        return m_

    def calculate_lex_ident_letter(self, word, loc, most_freq_word, frequency_word):
        range = 100
        m_ = self.calculate_lex_ident_general(word, most_freq_word, frequency_word)

        word_length = len(word)
        middle = word_length / 2
        m = m_ + range / (word_length / 2) * abs(loc - middle)

        if m < 80:
            m = 80

        return m

    def calculate_final_pos_fixation(self, dict_probability):
        keys = list(dict_probability.keys())
        values = list(dict_probability.values())
        if sum(values) < 0:
            return 0.9
        chosen_key = random.choices(keys, weights=values, k=1)[0]
        return chosen_key

    def calculate_sd(self, m):
        return 0.1 * m

    def should_refixate(self, probability_refixation):
        return random.random() < probability_refixation

    def calculate_normal_distribution(self, m, sd):
        return np.random.normal(m, sd)

    def calculate_time_saccade(self, distance_in_cm):
        amplitude = self.calculate_amplitude(distance_in_cm)
        return 2.2 * (amplitude - 5) + 21

    def calculate_amplitude(self, distance_between_words):
        b = self.distance_to_display
        a = distance_between_words
        tg_alpha = a / b
        amplitude = int(math.atan(tg_alpha) * 180 / math.pi)
        return amplitude
