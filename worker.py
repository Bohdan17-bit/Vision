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

    progress_signal: pyqtSignal = pyqtSignal(str)
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
        word.text_span.replace("’’", "'")
        word.text_span.replace("`", "'")
        word.text_span.replace("’", "'")

        if not any(char.isdigit() for char in word.text_span):
            word.text_span = re.sub(r'\.$', '', word.text_span)

        re.sub(r'[,!?;:]+$', '', word.text_span)
        return word

    def process_long_word(self, word, cleaned_word, size_step, last_word):

        start_index = last_word["index"]

        if not last_word["same"]:
            start_index = 0

        if last_word["rest"] >= 10:
            last_word["rest"] = 10

        max_index = size_step + start_index

        if len(cleaned_word) < size_step + start_index:
            max_index = len(cleaned_word)
            last_word["read"] = True
            last_word["same"] = False
            last_word["rest"] = 0
            last_word["skip"] = True
            last_word["index"] = 0

        text = cleaned_word[start_index: max_index]
        index_landing = self.calculate_index_landing(text, last_word["rest"], 1)

        print("Start index: ", start_index, "End index: ", max_index)

        self.progress_signal.emit(f"Calculating index of the word: <{word}>")

        if index_landing + start_index >= len(cleaned_word):
            index_landing = len(cleaned_word) - start_index - 1

        last_word["index"] = last_word["index"] + index_landing

        print(last_word)

        self.show_fixation_on_long_word(word, index_landing + start_index)
        self.progress_signal.emit("\n")
        return last_word

    def process_short_word(self):
        pass

    def word_time_reading(self, word, biggest_value_freq):

        time_estimated_per_str = 0
        time_to_read_sd = 0

        if self.word_contain_digit(word) or any(char in word.text_span for char in
                                                "-'’`.") or word.text_span.lower() in self.freq_dict.abbreviations:

            word_cleaned = word.text_span.lower().replace("’", "'").replace("`", "'").replace(".", "")

            # Special handling for "etc"
            if "etc" in word.text_span.lower():
                parsed_word = "et cetera"
                freq = self.freq_dict.find_freq_for_word(self.freq_dict.sheet, self.freq_dict.column, "etc")
                self.progress_signal.emit(f"Frequency of word: <etc> per million: {int(freq)}")
                time_per_segment = self.model.calculate_time_reading("etc", len("etc") / 2, biggest_value_freq,
                                                                     freq)
                time_to_read_sd += self.model.calculate_sd(time_per_segment)
                time_estimated_per_str += time_per_segment

            elif word_cleaned in self.freq_dict.abbreviations:

                parsed_word = self.freq_dict.abbreviations[word_cleaned]

                for segment in parsed_word.split():
                    segment_lower = segment.lower()
                    freq = self.freq_dict.find_freq_for_word(self.freq_dict.sheet, self.freq_dict.column,
                                                             segment_lower)

                    self.progress_signal.emit(f"Frequency of word: <{segment}> per million: {int(freq)}")
                    time_per_segment = self.model.calculate_time_reading(segment_lower, len(segment) / 2,
                                                                         biggest_value_freq, freq)
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
                    time_per_segment = self.model.calculate_time_reading(segment_lower, len(segment) / 2,
                                                                         biggest_value_freq, freq)
                    self.progress_signal.emit(f"Frequency of word: <{segment}> per million: {int(freq)}")
                    time_to_read_sd += self.model.calculate_sd(time_per_segment)
                    time_estimated_per_str += time_per_segment

            self.progress_signal.emit(f"Pronounced: {parsed_word}")
            self.progress_signal.emit(
                f"Time required for reading text <{word.text_span}> = {int(time_estimated_per_str)} ms"
            )
        else:
            word_original = word.text_span
            word_lower = word.text_span.lower()
            freq = self.freq_dict.find_freq_for_word(self.freq_dict.sheet, self.freq_dict.column, word_lower)
            self.progress_signal.emit(f"Frequency of word <{word_original}> per million: {int(freq)}")
            time_for_word = int(
                self.model.calculate_time_reading(word_lower, int(len(word_lower) / 4), biggest_value_freq, freq)
            )
            time_estimated_per_str += time_for_word
            self.progress_signal.emit(
                f"Time required for reading word <{word_original}> = {int(time_estimated_per_str)} ms"
            )
            time_to_read_sd += self.model.calculate_sd(time_for_word)

        time_to_read_sd = self.model.calculate_sd(time_estimated_per_str)
        self.model.increase_general_time(time_estimated_per_str)
        self.model.increase_general_time_sd(time_to_read_sd)

        self.progress_signal.emit("Performing saccade...\n")

        if word.distance_to_next_span > 0:
            time_saccade = self.model.calculate_time_saccade(word.distance_to_next_span)
            self.progress_signal.emit(f"Moving to the next block... Time required {int(time_saccade)} ms\n")
            self.model.increase_general_time(time_saccade)

    def start_analyze(self):

        most_frequency_value = self.freq_dict.get_biggest_frequency()

        size_step = 15

        last_word = {
            "skip": False,
            "same": False,
            "read": False,
            "rest": 0,
            "index": 0,
        }

        for word in self.words_spans:

            if re.match(r'^[.,!?;:]+$', word.text_span):
                continue

            cleaned_word = self.clean_word(word)

            if word.long:

                last_word["same"] = False
                last_word["read"] = False

                while last_word["read"] is False:

                    print("Current word :", word.text_span)
                    last_word = self.process_long_word(word.text_span, cleaned_word.text_span, size_step, last_word)
                    last_word["same"] = True

            else:

                self.process_short_word()

            self.word_time_reading(cleaned_word, most_frequency_value)

        self.progress_signal.emit("Analysis completed.\n")

    def calculate_index_landing(self, partial_word, rest_letters, coefficient):
        dict_probability = self.model.calculate_probability_landing(partial_word, rest_letters, coefficient)
        return round(self.model.calculate_final_pos_fixation(dict_probability))

    def obtain_rest_on_short_word(self, index_landing, short_word):
        if index_landing < len(short_word):
            self.progress_signal.emit(
                f"Fixation in word <{short_word}> on character '{short_word[index_landing]}' at index {index_landing}.")
            return len(short_word) - (index_landing + 1)
        elif index_landing == len(short_word):
            self.progress_signal.emit(f"Word was skipped! Landing on the next character!\n")
            return 0
        else:
            self.progress_signal.emit(f"Word was skipped! Landing on 2 symbols after the word!\n")
            return 0

    def show_fixation_on_long_word(self, word, index):
        self.progress_signal.emit(f"Fixation in word <{word}> on character '{word[index]}' at index {index}.")

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
    try:
        response = requests.head(path)
        if response.status_code == 200:
            return "site"
        else:
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error while checking the URL: {e}")
        return False
