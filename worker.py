import copy
import random
import re

from FontsManager import FontsManager
from model import Model

import os.path
import requests
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QThread
import time


class Worker(QThread):
    def __init__(self, freq_dictionary):
        super().__init__()
        self.freq_dict = freq_dictionary
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

        try:
            self.model.set_width_px(int(data["width_px"]))
        except (ValueError, TypeError):
            pass

        try:
            self.model.set_height_px(int(data["height_px"]))
        except (ValueError, TypeError):
            pass

        try:
            self.model.set_distance_to_display(int(data["distance_cm"]))
        except (ValueError, TypeError):
            pass

        try:
            self.model.set_diagonal_inches(int(data["diagonal_inches"]))
        except (ValueError, TypeError):
            pass

        self.model.set_visible_width()

    def update_url(self, path):
        self.model.set_path(path)

    def run(self):
        self.prepare_to_read()

    @pyqtSlot()
    def prepare_to_read(self):

        self.reset_results()

        path = self.model.path

        if path == "":
            self.data_signal.emit("Warning", "Path to file or webpage is missing!")
            return

        if url_is_correct(path) is False:
            self.data_signal.emit("Warning", "Website or file not found!")
            return

        if url_is_correct(path) == "blocked":
            self.data_signal.emit("Warning", "Program detected as a Bot, Access denied!")
            return

        if (self.model.height_px <= 0 or self.model.width_px <= 0 or self.model.distance_to_display <= 0
                or self.model.diagonal_inches <= 0):
            self.data_signal.emit("Error", "Please fill in all fields!")
            return

        self.model.calculate_ppi()

        self.updated_ppi_rounded.emit(str(round(self.model.PPI, 0)))

        self.progress_signal.emit("Loading frequency dictionary...")

        while not self.freq_dict.sheet:
            time.sleep(2)

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

    def word_is_number(self, word):
        for char in word.text_span:
            if not char.isdigit():
                return False
        return True

    def long_word_contain_digit(self, word):
        for char in word:
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

    def word_time_reading(self, word, biggest_value_freq, index_landing, show_freq_or_not):
        time_estimated_per_str = 0

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
                time_estimated_per_str += time_per_segment

            elif word_cleaned in self.freq_dict.abbreviations:

                parsed_word = self.freq_dict.abbreviations[word_cleaned]

                for segment in parsed_word.split():
                    segment_lower = segment.lower()
                    freq = self.freq_dict.find_freq_for_word(self.freq_dict.sheet, self.freq_dict.column,
                                                             segment_lower)

                    if show_freq_or_not:
                        self.progress_signal.emit(f"Frequency of word: <{segment}> per million: {int(freq)}")
                    time_per_segment = self.model.calculate_time_reading(segment_lower,
                                                                         random.randint(0, len(segment) // 2),
                                                                         biggest_value_freq, freq)
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
                    time_per_segment = self.model.calculate_time_reading(segment_lower,
                                                                         random.randint(0, len(segment) // 2),
                                                                         biggest_value_freq, freq)
                    if show_freq_or_not:
                        self.progress_signal.emit(f"Frequency of word: <{segment}> per million: {int(freq)}")
                    time_estimated_per_str += time_per_segment

            self.progress_signal.emit(f"Pronounced: {parsed_word}")
            self.progress_signal.emit(
                f"Time required for reading complex text <{word.text_span}> = {int(time_estimated_per_str)} ms"
            )
        else:
            word_original = word.text_span
            word_lower = word.text_span.lower()
            freq = self.freq_dict.find_freq_for_word(self.freq_dict.sheet, self.freq_dict.column, word_lower)
            if show_freq_or_not:
                self.progress_signal.emit(f"Frequency of word <{word_original}> per million: {int(freq)}")
            if index_landing == 0:
                time_for_word = int(
                    self.model.calculate_time_reading(word_lower, 0, biggest_value_freq, freq)
                )
            else:
                time_for_word = int(
                    self.model.calculate_time_reading(word_lower, index_landing+1, biggest_value_freq, freq)
                )
            time_estimated_per_str += time_for_word

        time_to_read_sd = self.model.calculate_sd(time_estimated_per_str)
        self.model.increase_general_time(time_estimated_per_str)
        self.model.increase_general_time_sd(time_to_read_sd)

        return time_estimated_per_str

    def font_cf_handler(self, word):
        word.size = int(word.size)

        found, word.font_span = self.format_font_name(word.font_span)

        if not found:
            self.progress_signal.emit("Font Name not found! Times New Roman will be used")
            if word.size:
                self.progress_signal.emit(f"Font size found: {word.size}")
        else:
            self.progress_signal.emit(f"Font properties: {word.font_span}, {int(word.size)}")

        if 13.5 < word.size < 14.5:
            word.size = 14

        coefficient = self.fontsManager.get_coefficient_font_letter(word.font_span, word.size, self.model.PPI)

        coefficient = round(coefficient, 1)

        if coefficient > 1:
            self.progress_signal.emit(f"The font size is smaller than standard by a factor of {coefficient:.2f}x")
        elif coefficient == 1:
            self.progress_signal.emit(f"The identified font size is standard.")
        else:
            self.progress_signal.emit(f"The font size is larger than standard by a factor of {(1 / coefficient):.2f}x")

        return coefficient

    def make_init_saccade(self):
        distance = self.model.parserPDF.get_distance_to_first_span()

        if distance > 0:
            time_saccade = self.model.calculate_time_saccade(distance)
            self.progress_signal.emit(f"Moving to the first block... Time required {int(time_saccade)} ms\n")
            self.model.increase_general_time(int(time_saccade))

    def start_analyze(self):

        most_frequency_value = self.freq_dict.get_biggest_frequency()

        default_size_step = 15 * self.model.calculate_distance_cf()
        self.progress_signal.emit(
            "Standard shift to the right: 14-15 letters for 14 points Times New Roman (distance: 55 cm).")
        self.progress_signal.emit(
            f"Calculated shift to the right: {int(default_size_step)} letters for 14 points Times New Roman (distance: {int(self.model.distance_to_display)}cm).\n"
        )

        last_word = {
            "rest": 0,
            "index": 0,
            "time": 0,
            "state": None
        }

        self.make_init_saccade()

        saccade_is_extended = False

        for i in range(len(self.words_spans)):
            word = self.words_spans[i]

            if re.match(r'^[.,!?\-;:]+$', word.text_span):
                continue

            if saccade_is_extended is True:
                saccade_is_extended = False
                self.progress_signal.emit(f"Next word <{word.text_span}> was skipped due early word identification.\n")
                continue

            cleaned_word = self.clean_word(copy.deepcopy(word))
            self.progress_signal.emit(f"Next word: {word.text_span}")

            cf = self.font_cf_handler(word)

            last_word = self.read(word, cleaned_word, last_word, cf, default_size_step, most_frequency_value)

            word_time = 0

            if last_word["state"] != "skip":
                if last_word["time"] != 0:
                    word_time = last_word["time"]
                    last_word["time"] = 0
                else:
                    word_time += self.word_time_reading(cleaned_word, most_frequency_value, last_word["index"], True)

            else:
                continue

            self.progress_signal.emit(
                f"Total time required for reading word : {word.text_span} = {int(word_time)} ms")

            if i + 1 < len(self.words_spans):
                self.progress_signal.emit("Programming a saccade...")
                latency = self.latency_before_saccade()

                next_word = self.words_spans[i + 1]

                if len(next_word.text_span) < 4:
                    quick_time = int(self.get_quick_check_time_word(next_word, most_frequency_value))

                    if latency + 25 >= quick_time and i + 2 < len(self.words_spans) and not next_word.text_span.isdigit():
                        self.progress_signal.emit("Saccade to word n+1 was canceled due to early word identification.")
                        self.progress_signal.emit("New saccade programmed to word n+2.")

                        saccade_is_extended = True

                        next_next_word = self.words_spans[i + 2]
                        distance_cm = self.model.parserPDF.calculate_distance(
                            word.get_coords(),
                            next_next_word.get_coords()
                        )
                        time_saccade = self.model.calculate_time_saccade(distance_cm) * 2
                        self.progress_signal.emit("\nPerforming saccade...")
                        self.progress_signal.emit(f"Moving to the next word. Time required {int(time_saccade)} ms\n")
                        self.model.increase_general_time(time_saccade)

                    elif latency < quick_time:
                        saccade_is_extended = False
                        self.performing_saccade(word)

                    else:
                        time_saccade = self.model.calculate_time_saccade(word.distance_to_next_span)
                        self.progress_signal.emit("\nPerforming saccade...")
                        self.progress_signal.emit(f"Moving to the next word. Time required {int(time_saccade)} ms\n")
                        self.model.increase_general_time(time_saccade)

                else:
                    time_saccade = self.model.calculate_time_saccade(word.distance_to_next_span)
                    self.progress_signal.emit("\nPerforming saccade...")
                    self.progress_signal.emit(f"Moving to the next word. Time required {int(time_saccade)} ms\n")
                    self.model.increase_general_time(time_saccade)

        self.show_final_results()

    def read(self, word, cleaned_word, last_word, coefficient, default_size_step, most_frequency_value):

        if self.word_is_number(word):
            last_word["index"] = 0
            last_word["rest"] = 1
            last_word["state"] = "read"
            return last_word

        default_size_step += 1
        if default_size_step < 2:
            default_size_step = 2

        if not word.text_span or not cleaned_word.text_span:
            last_word["state"] = "skip"
            last_word["rest"] = 0
            last_word["index"] = 0
            return last_word

        # -------- short word that can be overflown ----------
        if len(word.text_span) < 4:
            if last_word["state"] == "skip":
                last_word["index"] = 0
                last_word["rest"] = len(word.text_span) - 1
                last_word["state"] = "read"
                self.show_fixation_in_word(0, word.text_span)
                return last_word
            else:
                dict_probability = self.model.calculate_probability_landing(
                    cleaned_word.text_span, last_word["rest"], coefficient
                )
                index_chose = self.model.calculate_final_pos_fixation(dict_probability)
                index_chose = min(index_chose, len(word.text_span))
                index_chose = max(index_chose, 0)

                try:
                    result = self.get_and_show_rest_of_word(index_chose, word.text_span)
                except IndexError:
                    last_word["state"] = "skip"
                    last_word["rest"] = 0
                    last_word["index"] = 0
                    return last_word

                last_word["index"] = index_chose
                if result == -1:
                    last_word["state"] = "skip"
                    last_word["rest"] = 0
                else:
                    last_word["state"] = "read"
                    last_word["rest"] = result
                return last_word

        # -------- regular word that longer 3 symbols ----------
        else:
            if coefficient * default_size_step >= len(word.text_span):
                if last_word["state"] == "skip":
                    index_landing = 0
                else:
                    min_index = 0
                    max_index = len(word.text_span) - 1
                    index_landing = self.calculate_index_landing(
                        word.text_span[min_index:max_index],
                        last_word["rest"],
                        coefficient
                    )
                    index_landing = min(index_landing, 5)

                self.get_and_show_rest_of_word(index_landing, word.text_span)
                last_word["index"] = index_landing
                last_word["state"] = "read"
                last_word["rest"] = len(word.text_span) - 1 - index_landing
                return last_word

            # -------- if we need a few fixations to read a word -------
            else:
                word_not_read = True
                min_index = 0
                visible_zone = max(2, int(coefficient * default_size_step))
                total_reading_time = 0
                previous_global_index = -1
                first_fixation = True
                fixation_count = 0

                while word_not_read:
                    max_index = min(min_index + visible_zone, len(word.text_span))

                    index_landing = self.calculate_index_landing(
                        word.text_span[min_index:max_index],
                        last_word["rest"],
                        coefficient
                    )

                    local_index = min(index_landing, max_index - min_index - 1)
                    global_index = min_index + local_index
                    global_index = min(global_index, len(word.text_span) - 1)

                    if first_fixation and global_index > 2:
                        global_index = 2
                    first_fixation = False

                    if global_index == previous_global_index:
                        break

                    # === Розрахунок зміщення та сакади ===
                    if previous_global_index != -1:
                        shift_letters = global_index - previous_global_index
                        if shift_letters > 0:
                            time_saccade = self.make_short_saccade(word, shift_letters)
                            total_reading_time += time_saccade

                    previous_global_index = global_index
                    last_word["index"] = global_index
                    fixation_count += 1

                    is_single_fixation = (fixation_count == 1 and max_index >= len(word.text_span))
                    fixation_time = self.word_time_reading(
                        cleaned_word, most_frequency_value, global_index, is_single_fixation
                    )
                    total_reading_time += fixation_time

                    self.get_and_show_rest_of_word(global_index, word.text_span)

                    rest = len(word.text_span) - (global_index + 1)
                    last_word["rest"] = max(0, rest)

                    if rest <= 0:
                        word_not_read = False
                    else:
                        min_index = global_index + 1

                last_word["time"] = total_reading_time
                last_word["state"] = "read"
                freq = self.freq_dict.find_freq_for_word(self.freq_dict.sheet, self.freq_dict.column, word.text_span.lower())
                self.progress_signal.emit(f"Frequency of word <{word.text_span}> per million: {int(freq)}")

                return last_word

    def make_short_saccade(self, word, shift_letters):
        self.progress_signal.emit("Performing saccade...")
        w, h = self.fontsManager.get_size_letter_into_cm('D', word.font_span, int(word.size), 100)
        distance_cm = w * shift_letters
        time_saccade = self.model.calculate_time_saccade(distance_cm)
        self.progress_signal.emit(f"Moving to the next part of word. Time required {int(time_saccade)} ms")
        self.model.increase_general_time(time_saccade)
        return time_saccade

    def get_and_show_rest_of_word(self, index_landing, word):
        if index_landing < len(word):
            self.progress_signal.emit(
                f"Fixation in word <{word}> on character '{word[index_landing]}' at index {index_landing + 1}.")
            self.refixation_check(word, index_landing)
            return len(word) - index_landing
        else:
            self.progress_signal.emit(f"Word was skipped! Landing on the next character!\n")
            return -1

    def show_fixation_in_word(self, index_landing, word):
        if index_landing < len(word):
            self.progress_signal.emit(
                f"Fixation in word <{word}> on character '{word[index_landing]}' at index {index_landing + 1}.")
            self.refixation_check(word, index_landing)
        else:
            self.progress_signal.emit(
                f"Fixation in word <{word}> on character '{word[index_landing]}' at index {index_landing}.")
            self.refixation_check(word, index_landing)

    def latency_before_saccade(self):
        time_latency = self.model.calculate_average_latency_time()
        if time_latency < 50:
            time_latency = 50
        self.progress_signal.emit(f"Saccade delay calculated: {int(time_latency)} ms")
        self.model.increase_general_time(int(time_latency))
        self.model.increase_general_time_sd(self.model.calculate_sd(self.model.standard_deviation_latency))
        return int(time_latency)

    def get_quick_check_time_word(self, word, biggest_value_freq):
        word_lower = word.text_span.lower()
        freq = self.freq_dict.find_freq_for_word(self.freq_dict.sheet, self.freq_dict.column, word_lower)
        time_for_word = int(
            self.model.calculate_time_reading(word_lower, random.randint(0, len(word_lower) // 2), biggest_value_freq,
                                              freq))
        return time_for_word

    def performing_saccade(self, prev_word):

        self.progress_signal.emit("\nPerforming saccade...")

        if prev_word.distance_to_next_span > 0:
            time_saccade = self.model.calculate_time_saccade(prev_word.distance_to_next_span)
            self.progress_signal.emit(f"Moving to the next word. Time required {int(time_saccade)} ms\n")
            self.model.increase_general_time(time_saccade)

    def show_final_results(self):
        self.progress_signal.emit("\nAnalysis completed.\n")
        final_result = self.get_time_to_read(self.model.get_sum_time_reading(), self.model.get_sum_standard_deviation())
        self.final_result.emit(final_result)
        self.reset_results()

    def calculate_index_landing(self, partial_word, rest_letters, coefficient):
        dict_probability = self.model.calculate_probability_landing(partial_word, rest_letters, coefficient)
        return round(self.model.calculate_final_pos_fixation(dict_probability))

    def refixation_check(self, word, index_chose):
        prob_refix = self.model.calculate_probability_refixation(word, index_chose)
        self.progress_signal.emit(f"Probability of refixation = {round(prob_refix, 3)}")
        if self.model.should_refixate(prob_refix):
            self.progress_signal.emit("------------------Refixation required------------------")
            time_refix = self.model.make_refixation(word, index_chose + 1)
            self.progress_signal.emit(f"Refixation delay time = {int(time_refix)} ms")
            time_refix_sd = self.model.calculate_sd(time_refix)
            self.model.increase_general_time(time_refix)
            self.model.increase_general_time_sd(time_refix_sd)
        else:
            self.progress_signal.emit("Refixation not required...")

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
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    if os.path.exists(path):
        return "file"
    try:
        response = requests.get(path, headers=headers, stream=True, timeout=5)
        if response.status_code == 200:
            return "site"
        elif response.status_code == 403:
            return "blocked"
        else:
            return False
    except requests.exceptions.RequestException:
        pass
    return False
