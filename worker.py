import re

from openpyxl import load_workbook

from model import Model
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QFileDialog
import os.path
import requests
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QThread
from PyQt5.QtWidgets import QMainWindow, QApplication, QPlainTextEdit, QVBoxLayout, QWidget
import time
from utils import FrequencyDictionary


class Worker(QThread):
    def __init__(self):
        super().__init__()
        self.freq_dict = FrequencyDictionary()
        self.freq_dict.start()
        self.model = Model()
        self.words_spans = {}

    updated_ppi_rounded = pyqtSignal(str)

    progress_signal = pyqtSignal(str)
    data_signal = pyqtSignal(str, str)

    final_result = pyqtSignal(str)

    def receive_data_from_ui(self, data):
        if data["width_px"] and data["height_px"] and data["distance_cm"] and data["diagonal_inches"]:
            self.model.set_width_px(int(data["width_px"]))
            self.model.set_height_px(int(data["height_px"]))
            self.model.set_distance_to_display(int(data["distance_cm"]))
            self.model.set_diagonal_inches(int(data["diagonal_inches"]))

    def update_url(self, path):
        self.model.set_path(path)

    def run(self):
        self.prepare_to_read()

    @pyqtSlot()
    def prepare_to_read(self):

        print("Починаємо обробку даних...")

        path = self.model.path

        if path == "":
            self.data_signal.emit("Попередження", "Відсутній шлях до файлу чи веб-сторінки!")
            return

        if url_is_correct(path) is not True:
            self.data_signal.emit("Попередження", "Сайт або файл не знайдено!")
            return

        if (self.model.height_px <= 0 and self.model.width_px <= 0 and self.model.distance_to_display <= 0
                and self.model.PPI <= 0 and self.model.diagonal_inches <= 0):
            self.data_signal.emit("Помилка", "Будь ласка, заповніть усі поля!")
            return

        self.model.calculate_ppi()

        self.updated_ppi_rounded.emit(str(round(self.model.PPI, 0)))

        self.progress_signal.emit("Завантаження частотного словника...")

        if not self.freq_dict.sheet:
            self.progress_signal.emit("Частотний словник не знайдено!")
            return

        if "http" in path or "https" in path:
            self.model.set_path(path)
            self.progress_signal.emit("Аналіз структури сайту...")
            self.model.read_text_from_site(path)

        else:
            if "docx" in path or "doc" in path:
                self.progress_signal.emit("Конвертація документу в PDF...")
                self.model.convert_word_to_pdf(path)
            else:
                self.model.set_path(path)
            self.model.read_text_from_pdf()

        self.progress_signal.emit("Починається обробка...")

        self.words_spans = self.model.get_text_list_spans()

        self.start_analyze()

    def start_analyze(self):

        rest_letters = 0
        state = "updated"
        biggest_value_freq = self.freq_dict.get_biggest_frequency()

        for word in self.words_spans:

            if '<' in word.text_span or '>' in word.text_span:
                continue

            if word.text_span.isalpha():

                self.progress_signal.emit(f"Наступне слово : {word.text_span}")

                time.sleep(0.05)

                self.progress_signal.emit(f"Властивості шрифту : {word.font_span}, {int(word.size)}")

                if rest_letters > 3:
                    rest_letters = 3

                index_chose = 0

                dict_probability = self.model.calculate_probability_landing(word.text_span, rest_letters)

                self.progress_signal.emit(f"Розрахунок індекса слова : <{word.text_span}>")

                if state == "updated":
                    index_chose = self.model.calculate_final_pos_fixation(dict_probability)
                    self.progress_signal.emit(f"Індекс <{index_chose}> було обрано!")

                if state == "2 symbols after word":
                    index_chose = 0
                    state = "updated"

                if word.distance_to_next_span > 0:
                    index_chose = len(word.text_span) - 1
                    self.progress_signal.emit("Кінець цього слова...")

                if word.is_last_in_line:
                    index_chose = len(word.text_span) - 1
                    self.progress_signal.emit("Кінець рядку...")

                if index_chose == len(word.text_span):
                    self.progress_signal.emit("Слово було пропущене! Приземлення на наступний символ!")
                    rest_letters = 0

                elif index_chose > len(word.text_span):
                    self.progress_signal.emit("Слово пропущене! Приземлення на 2 символа після слова!")
                    rest_letters = 0
                    state = "2 symbols after word"

                else:
                    self.progress_signal.emit(f"Фіксація в слові <{word.text_span}> на слові {word.text_span[index_chose]}!")
                    rest_letters = len(word.text_span) - index_chose
                    prob_refix = self.model.calculate_probability_refixation(word.text_span, index_chose)
                    self.progress_signal.emit(f"Вірогідність рефіксації = {round(prob_refix, 3)}")

                    if self.model.should_refixate(prob_refix):
                        self.progress_signal.emit("------------------Необхідна рефіксація------------------")

                        time_refix = self.model.make_refixation(word.text_span, index_chose + 1)
                        self.progress_signal.emit(f"Час затримки рефіксації = {round(time_refix, 3)}")

                        time_refix_sd = self.model.calculate_sd(time_refix)

                        self.model.increase_general_time(time_refix)
                        self.model.increase_general_time_sd(time_refix_sd)

                    else:
                        self.progress_signal.emit("Рефіксація не потрібна...")

                    freq = self.freq_dict.find_freq_for_word(self.freq_dict.sheet, self.freq_dict.column, word.text_span)
                    self.progress_signal.emit("Обчислення часу лексичної ідентифікації...")

                    time_word_reading = self.model.calculate_time_reading(word.text_span, index_chose + 1,
                                                                     biggest_value_freq,
                                                                     freq)
                    self.progress_signal.emit(f"Для слова <{word.text_span}> необхідний час читання = {round(time_word_reading, 3)}")

                    time_to_read_sd = self.model.calculate_sd(time_word_reading)
                    dispersion = self.model.calculate_normal_distribution(time_word_reading, time_to_read_sd)

                    self.model.increase_general_time(dispersion)

                    self.progress_signal.emit("Виконання сакади...")

                self.model.add_average_latency_time()
                self.model.add_standard_deviation_latency_time()

            else:
                rest_letters += len(word.text_span)

            if word.distance_to_next_span > 0:
                time_saccade = self.model.calculate_time_saccade(word.distance_to_next_span)
                self.progress_signal.emit(f"Перехід на наступний блок... Необхідно часу {time_saccade} ms\n")
                self.model.increase_general_time(time_saccade)

        final_result = self.get_time_to_read(self.model.get_sum_time_reading(), self.model.get_sum_standard_deviation())
        self.final_result.emit(final_result)
        self.progress_signal.emit("Аналіз завершено.")

    def get_time_to_read(self, time, sd_time):
        min = time // 60000
        sec = (time % 60000) // 1000
        ms = time % 1000

        min = int(min)
        sec = int(sec)

        min_sd = sd_time // 60000
        sec_sd = (sd_time % 60000) // 1000
        ms_sd = sd_time % 1000

        min_sd = int(min_sd)
        sec_sd = int(sec_sd)

        if min > 0:
            final_result = f"Необхідно: {min},{int(sec_sd) % 100} хв. для читання."
        else:
            final_result = f"Необхідно: {sec},{int(ms) % 100} с. для читання."

        if min_sd > 0:
            path = f"\nСтандартне відхилення складає: {min_sd},{sec_sd} хв."
        else:
            path = f"\nСтандартне відхилення складає: {sec_sd},{int(ms_sd) % 100} с."

        final_result += path

        return final_result


def url_is_correct(path):
    if os.path.isfile(path):
        return True
    if requests.head(path).status_code == 200:
        return True
    return False
