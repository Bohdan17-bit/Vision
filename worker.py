import re

from FontsManager import FontsManager
from model import Model

import os.path
import requests
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QThread
import time
from utils import FrequencyDictionary


class Worker(QThread):
    def __init__(self):
        super().__init__()
        self.freq_dict = FrequencyDictionary()
        self.fontsManager = FontsManager()
        self.freq_dict.start()
        self.model = Model()
        self.words_spans = {}

    updated_ppi_rounded = pyqtSignal(str)

    progress_signal = pyqtSignal(str)
    data_signal = pyqtSignal(str, str)

    final_result = pyqtSignal(str)

    def reset_results(self):
        self.model.reset_results()

    def receive_data_from_ui(self, data):
        if data["width_px"] and data["height_px"] and data["distance_cm"] and data["diagonal_inches"]:
            self.model.set_width_px(int(data["width_px"]))
            self.model.set_height_px(int(data["height_px"]))
            self.model.set_distance_to_display(float(data["distance_cm"]))
            self.model.set_diagonal_inches(float(data["diagonal_inches"]))

    def update_url(self, path):
        self.model.set_path(path)

    def run(self):
        self.prepare_to_read()

    @pyqtSlot()
    def prepare_to_read(self):

        self.reset_results()

        print("Starting data processing...")

        path = self.model.path

        if path == "":
            self.data_signal.emit("Warning", "Path to file or webpage is missing!")
            return

        if url_is_correct(path) is False:
            self.data_signal.emit("Warning", "Website or file not found!")
            return

        if (self.model.height_px <= 0 and self.model.width_px <= 0 and self.model.distance_to_display <= 0
                and self.model.PPI <= 0 and self.model.diagonal_inches <= 0):
            self.data_signal.emit("Error", "Please fill in all fields!")
            return

        self.model.calculate_ppi()

        self.updated_ppi_rounded.emit(str(round(self.model.PPI, 0)))

        self.progress_signal.emit("Loading frequency dictionary...")

        time.sleep(3)

        if not self.freq_dict.sheet:
            self.progress_signal.emit("Frequency dictionary not found!")
            return

        if "html" in path or "htm" in path and "http" not in path and "https" not in path:
            if url_is_correct(path) is not False:
                self.model.set_path(path)
                self.progress_signal.emit("Analyzing website structure...")
                self.model.read_text_from_site(path)

        elif "http" in path or "https" in path:
            self.model.set_path(path)
            self.progress_signal.emit("Analyzing website structure...")
            self.model.read_text_from_site(path)

        else:
            if "docx" in path or "doc" in path:
                self.progress_signal.emit("Converting document to PDF...")
                self.model.convert_word_to_pdf(path)
            else:
                self.model.set_path(path)
            self.model.read_text_from_pdf()

        self.progress_signal.emit("Processing started...\n")

        self.words_spans = self.model.get_text_list_spans()

        self.start_analyze()

    def format_font_name(self, font_name):
        if font_name is None:
            return False, "Times New Roman"

        formatted_name = re.sub(r'(?<!^)(?=[A-Z])', ' ', font_name)

        formatted_name = re.sub(r'\b[A-Z]\b', '', formatted_name)

        formatted_name = re.split(r'\s*-\s*', formatted_name)[0]

        formatted_name = ' '.join(formatted_name.split())

        return True, formatted_name

    def word_contain_digit(self, word):
        for char in word.text_span:
            if char.isdigit():
                return True
        return False

    def clean_word(self, word):
        word.replace("’", "'").replace("’", "'")
        return re.sub(r'[,!?;:]+$', '', word)

    def start_analyze(self):
        rest_letters = 0
        state = "updated"
        biggest_value_freq = self.freq_dict.get_biggest_frequency()

        for word in self.words_spans:
            print("----",word.text_span)
            if re.match(r'^[.,!?;:]+$', word.text_span):
                continue

            cleaned_word = self.clean_word(word.text_span)
            self.progress_signal.emit(f"Next word : {cleaned_word}")

            if rest_letters > 5:
                rest_letters = 5

            index_chose = 0
            word.size = int(word.size)
            found, word.font_span = self.format_font_name(word.font_span)

            if not found:
                self.progress_signal.emit(f"Font not found! Times New Roman, 14 will be used")
            else:
                self.progress_signal.emit(f"Font properties : {word.font_span}, {int(word.size)}")

            coefficient = self.fontsManager.get_coefficient_font_letter(word.font_span, word.size, self.model.PPI)
            dict_probability = self.model.calculate_probability_landing(cleaned_word, rest_letters, coefficient)

            self.progress_signal.emit(f"Calculating index of the word : <{cleaned_word}>")

            if state == "updated":
                index_chose = self.model.calculate_final_pos_fixation(dict_probability)

                if len(cleaned_word) >= 4 or cleaned_word.isdigit():
                    if index_chose >= len(cleaned_word):
                        index_chose = len(cleaned_word) - 1
                else:
                    if index_chose == len(cleaned_word):
                        self.progress_signal.emit("Word was skipped! Landing on the next character!\n")
                        rest_letters = 0
                        continue

                    if index_chose > len(cleaned_word):
                        self.progress_signal.emit("Word was skipped! Landing 2 symbols after the word!\n")
                        rest_letters = 0
                        state = "2 symbols after word"
                        continue

            self.progress_signal.emit(
                f"Fixation in word <{cleaned_word}> on character '{cleaned_word[index_chose]}' at index {index_chose + 1}.")

            index_saved = index_chose

            if state == "2 symbols after word":
                index_chose = 0
                state = "updated"

            if word.distance_to_next_span > 0:
                index_chose = len(word.text_span) - 1

            if word.is_last_in_line:
                index_chose = len(word.text_span) - 1

            if index_chose == len(word.text_span):
                self.progress_signal.emit("Word was skipped! Landing on the next character!\n")
                rest_letters = 0

            elif index_chose > len(word.text_span):
                self.progress_signal.emit("Word was skipped! Landing 2 symbols after the word!\n")
                rest_letters = 0
                state = "2 symbols after word"

            else:
                rest_letters = len(word.text_span) - index_chose
                prob_refix = self.model.calculate_probability_refixation(word.text_span, index_saved)
                self.progress_signal.emit(f"Probability of refixation = {round(prob_refix, 3)}")

                if self.model.should_refixate(prob_refix):
                    self.progress_signal.emit("------------------Refixation required------------------")
                    time_refix = self.model.make_refixation(word.text_span, index_saved + 1)
                    self.progress_signal.emit(f"Refixation delay time = {round(time_refix, 3)}")
                    time_refix_sd = self.model.calculate_sd(time_refix)
                    self.model.increase_general_time(time_refix)
                    self.model.increase_general_time_sd(time_refix_sd)
                else:
                    self.progress_signal.emit("Refixation not required...")

                time_estimated_per_str = 0
                time_to_read_sd = 0

                print("next span", word.text_span)

                if self.word_contain_digit(word) or any(char in word.text_span for char in
                                                        "-'`.") or word.text_span.lower() in self.freq_dict.abbreviations or word.text_span.lower() in self.freq_dict.contraction_map:
                    # Special handling for "etc"
                    if word.text_span.lower() == "etc":
                        parsed_word = "et cetera"
                        freq = self.freq_dict.find_freq_for_word(self.freq_dict.sheet, self.freq_dict.column, "etc")
                        self.progress_signal.emit(f"Frequency of word: <etc> per million: {int(freq)}")
                        time_per_segment = self.model.calculate_time_reading("etc", len("etc") / 2, biggest_value_freq,
                                                                             freq)
                        time_to_read_sd += self.model.calculate_sd(time_per_segment)
                        time_estimated_per_str += time_per_segment
                    else:
                        # Check if it's a number and convert to words
                        if word.text_span.isdigit():
                            parsed_word = self.freq_dict.number_to_words(word.text_span)
                        else:
                            parsed_word = self.freq_dict.mixed_word_to_words(word.text_span)

                        for segment in parsed_word.split():
                            segment_lower = segment.lower()
                            freq = self.freq_dict.find_freq_for_word(self.freq_dict.sheet, self.freq_dict.column,
                                                                     segment_lower)
                            self.progress_signal.emit(f"Frequency of word: <{segment}> per million: {int(freq)}")
                            time_per_segment = self.model.calculate_time_reading(segment_lower, len(segment) / 2,
                                                                                 biggest_value_freq, freq)
                            time_to_read_sd += self.model.calculate_sd(time_per_segment)
                            time_estimated_per_str += time_per_segment

                    self.progress_signal.emit(f"Pronounced: {parsed_word}")
                    self.progress_signal.emit(
                        f"Time required for reading word <{word.text_span}> = {int(time_estimated_per_str)}")
                else:
                    word_original = word.text_span
                    word_lower = word.text_span.lower()
                    freq = self.freq_dict.find_freq_for_word(self.freq_dict.sheet, self.freq_dict.column, word_lower)
                    self.progress_signal.emit(f"Frequency of word <{word_original}> per million: {int(freq)}")
                    time_for_word = int(
                        self.model.calculate_time_reading(word_lower, index_saved, biggest_value_freq, freq))
                    time_estimated_per_str += time_for_word
                    self.progress_signal.emit(
                        f"Time required for reading word <{word_original}> = {int(time_estimated_per_str)}")
                    time_to_read_sd += self.model.calculate_sd(time_for_word)

                time_to_read_sd = self.model.calculate_sd(time_estimated_per_str)
                dispersion = self.model.calculate_normal_distribution(time_estimated_per_str, time_to_read_sd)
                self.model.increase_general_time(dispersion)
                self.model.increase_general_time_sd(time_to_read_sd)

                self.progress_signal.emit("Performing saccade...")

            self.model.add_average_latency_time()
            self.model.add_standard_deviation_latency_time()

            if word.distance_to_next_span > 0:
                time_saccade = self.model.calculate_time_saccade(word.distance_to_next_span)
                self.progress_signal.emit(f"\nMoving to the next block... Time required {int(time_saccade)} ms\n")
                self.model.increase_general_time(time_saccade)

        final_result = self.get_time_to_read(self.model.get_sum_time_reading(), self.model.get_sum_standard_deviation())
        self.final_result.emit(final_result)
        self.progress_signal.emit("Analysis completed.")
        self.reset_results()

    def get_time_to_read(self, time: float, sd_time: float) -> str:
        min = int(time // 60000)
        sec = int((time % 60000) // 1000)
        ms = int((time % 1000) / 10)

        min_sd = int(sd_time // 60000)
        sec_sd = int((sd_time % 60000) // 1000)
        ms_sd = int((sd_time % 1000) / 10)

        if min > 0:
            final_result = f"Required: {min}:{sec:02d} min for reading."
        else:
            final_result = f"Required: {sec}.{ms:02d} s for reading."

        if min_sd > 0:
            path = f"\nStandard deviation is: {min_sd}:{sec_sd:02d} min."
        else:
            path = f"\nStandard deviation is: {sec_sd}.{ms_sd:02d} s."

        final_result += path
        return final_result


def url_is_correct(path):
    if os.path.exists(path):
        return "file"
    if requests.head(path).status_code == 200:
        return "site"
    return False
