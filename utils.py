from openpyxl import load_workbook
from PyQt5.QtCore import QThread, pyqtSignal
import re


class FrequencyDictionary(QThread):
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.workbook = None
        self.sheet = None
        self.column = None

        self.ones = [
            "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"
        ]
        self.teens = [
            "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
            "sixteen", "seventeen", "eighteen", "nineteen"
        ]
        self.tens = [
            "", "", "twenty", "thirty", "forty", "fifty",
            "sixty", "seventy", "eighty", "ninety"
        ]
        self.thousands = ["", "thousand"]

    def run(self):
        self.load_dictionary()

    def load_dictionary(self):
        self.workbook = self.get_frequency_dictionary('data/wordFrequency.xlsx')
        self.sheet = self.get_sheet_workbook(self.workbook, "4 forms (219k)")
        self.column = self.get_column_by_sheet('B')
        self.finished.emit()

    def get_frequency_dictionary(self, path):
        return load_workbook(path)

    def get_sheet_workbook(self, workbook, sheet):
        list_sheets = workbook.sheetnames
        if sheet in list_sheets:
            return workbook[sheet]
        else:
            return None

    def find_freq_for_word(self, sheet, column, word):
        for cell in column:
            if word == cell.value:
                return sheet.cell(row=cell.row, column=15).value
        return 0

    def get_biggest_frequency(self):
        return self.sheet.cell(row=2, column=15).value

    def get_column_by_sheet(self, col):
        return self.sheet[col]

    def parse_hundreds(self, num):
        if num == 0:
            return ""
        if num < 10:
            return self.ones[num]
        elif num < 20:
            return self.teens[num - 10]
        else:
            result = self.tens[num // 10]
            if num % 10 != 0:
                result += " " + self.ones[num % 10]
            return result

    def number_to_words(self, n):
        if n < 0:
            return "negative"

        if n <= 9999:
            words = []
            if n >= 1000:
                words.append(self.ones[n // 1000] + " " + self.thousands[1])
                n %= 1000
            if n >= 100:
                words.append(self.ones[n // 100] + " hundred")
                n %= 100
            if n > 0:
                words.append(self.parse_hundreds(n))

            return " ".join(words).strip()

        else:
            words = []
            for digit in str(n):  # Розбиваємо число на окремі цифри
                words.append(self.ones[int(digit)])  # Перетворюємо цифру у слово
            return " ".join(words)

    def split_mixed_word(self, text):
        segments = re.findall(r'[a-zA-Z]+|\d+|[^\w\s]', text)
        return segments

    def mixed_word_to_words(self, text):

        segments = self.split_mixed_word(text)
        result = []

        for segment in segments:
            if segment.isdigit():
                result.append(self.number_to_words(int(segment)))
            else:
                result.append(segment)

        return " ".join(result)
