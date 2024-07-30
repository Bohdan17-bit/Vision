import math
import random
import numpy as np
from TextSpanPDF import TextSpanPDF
from pdf_parser import ParserPDF
import re


class Model:

    list_text_spans = []

    average_saccade_latency = 150
    standard_deviation_latency = 50

    distance_to_display = 0

    def __init__(self):
        self.__full_time_to_read = 0
        self.__full_time_standard_deviation = 0
        self.parserPDF = ParserPDF()

    def read_text_from_pdf(self, filename):
        self.list_text_spans = self.parserPDF.start(filename)

    def set_distance_to_display(self, distance_in_cm):
        self.distance_to_display = distance_in_cm

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
        # print(f"For word <{next_word}> d = {launch_distance}")
        return launch_distance

    def calculate_average_landing_position(self, word, d):
        m = 3.3 + 0.49 * d
        # print(f"For word <{word}> m = {round(m, 3)}")
        return m

    def calculate_standard_deviation(self, d, word):
        sd = 1.318 + 0.000518 * d ** 3
        # print(f"For word <{word}> standard deviation = {round(sd, 3)}")
        return sd

    def calculate_probability_letter_landing(self, x, m, sd):
        q = math.sqrt(2 * math.pi) * sd
        ch = (x - m) ** 2
        zn = 2 * (sd * sd)
        prob = 1 / q * math.exp(-ch / zn)
        return prob

    def calculate_probability_landing(self, target_word, rest_letters):
        d = self.calculate_launch_distance(target_word, rest_letters)
        m = self.calculate_average_landing_position(target_word, d)
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
        return y

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
        print(f"Time for delay refixation = {round(time, 3)}")
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
        print("Calculating time recognizing...")
        time_needed = self.calculate_lex_ident_letter(word, loc, most_freq_word, frequency_word)
        print(f"For word <{word}> time, needed to read = {round(time_needed, 3)}")
        return time_needed

    def calculate_lex_ident_general(self, word, biggest_freq, frequency_word):
        base5 = 150
        if frequency_word == "not found!":
            print(f"The word <{word}> was not found!")
            return 0
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
        chosen_key = random.choices(keys, weights=values, k=1)[0]
        print(f"Index <{chosen_key}> was chose!")
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

