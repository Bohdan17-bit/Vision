from openpyxl import load_workbook
from PyQt5.QtCore import QThread, pyqtSignal


class FrequencyDictionary(QThread):
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.workbook = None
        self.sheet = None
        self.column = None

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
                return sheet.cell(row=cell.row, column=21).value
        return "not found!"

    def get_biggest_frequency(self):
        return self.sheet.cell(row=2, column=21).value

    def get_column_by_sheet(self, col):
        return self.sheet[col]



