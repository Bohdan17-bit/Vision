# -*- coding: utf-8 -*-
import time

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal, QRegularExpression
from PyQt5.QtGui import QRegularExpressionValidator
from PyQt5.QtWidgets import QFileDialog
from utils import FrequencyDictionary


from worker import Worker


class Ui_MainWindow(QtWidgets.QMainWindow):
    url_changed = pyqtSignal(str)
    data_sended = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.freq_dict = FrequencyDictionary()
        self.worker = Worker(self.freq_dict)

    def start_thread(self):
        self.worker.progress_signal.connect(self.add_text_to_process_textedit)
        self.worker.final_result.connect(self.set_total_time_textedit)
        self.worker.updated_ppi_rounded.connect(self.update_ppi_textedit)
        self.worker.data_signal.connect(self.show_messagebox)
        self.url_changed.connect(self.worker.update_url)
        self.URL_lineEdit.textChanged.connect(self.worker.update_url)

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1600, 900)
        font = QtGui.QFont()
        font.setPointSize(12)
        MainWindow.setFont(font)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(12)
        font.setBold(True)
        self.label.setFont(font)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.URL_lineEdit = QtWidgets.QLineEdit(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(14)
        self.URL_lineEdit.setFont(font)
        self.URL_lineEdit.setText("")
        self.URL_lineEdit.setObjectName("URL_lineEdit")
        self.verticalLayout.addWidget(self.URL_lineEdit)
        self.ChooseFile_btn = QtWidgets.QPushButton(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ChooseFile_btn.sizePolicy().hasHeightForWidth())
        self.ChooseFile_btn.setSizePolicy(sizePolicy)
        self.ChooseFile_btn.setMinimumSize(QtCore.QSize(0, 70))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.ChooseFile_btn.setFont(font)
        self.ChooseFile_btn.setStyleSheet("QPushButton {\n"
"    background-color: #f0d54a;\n"
"}")
        self.ChooseFile_btn.setObjectName("ChooseFile_btn")
        self.verticalLayout.addWidget(self.ChooseFile_btn)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)
        self.verticalLayout_5 = QtWidgets.QVBoxLayout()
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.label_7 = QtWidgets.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(12)
        font.setBold(True)
        self.label_7.setFont(font)
        self.label_7.setAlignment(QtCore.Qt.AlignCenter)
        self.label_7.setWordWrap(True)
        self.label_7.setObjectName("label_7")
        self.verticalLayout_5.addWidget(self.label_7)
        self.verticalLayout_4 = QtWidgets.QVBoxLayout()
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.plainTextEdit = QtWidgets.QPlainTextEdit(self.centralwidget)
        self.plainTextEdit.setObjectName("plainTextEdit")
        self.plainTextEdit.setReadOnly(True)
        self.verticalLayout_4.addWidget(self.plainTextEdit)
        self.label_8 = QtWidgets.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(12)
        font.setBold(True)
        self.label_8.setFont(font)
        self.label_8.setAlignment(QtCore.Qt.AlignCenter)
        self.label_8.setWordWrap(True)
        self.label_8.setObjectName("label_8")
        self.verticalLayout_4.addWidget(self.label_8)
        self.TotalTime_lineEdit = QtWidgets.QTextEdit(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.TotalTime_lineEdit.setFont(font)
        self.TotalTime_lineEdit.setFixedHeight(80)
        self.TotalTime_lineEdit.setText("")
        self.TotalTime_lineEdit.setReadOnly(True)
        self.TotalTime_lineEdit.setObjectName("TotalTime_lineEdit")
        self.verticalLayout_4.addWidget(self.TotalTime_lineEdit)
        self.verticalLayout_5.addLayout(self.verticalLayout_4)
        self.gridLayout.addLayout(self.verticalLayout_5, 0, 1, 4, 1)
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(12)
        font.setBold(True)
        self.label_2.setFont(font)
        self.label_2.setAlignment(QtCore.Qt.AlignCenter)
        self.label_2.setWordWrap(True)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label_3 = QtWidgets.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(12)
        self.label_3.setFont(font)
        self.label_3.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_3.setWordWrap(True)
        self.label_3.setObjectName("label_3")
        self.verticalLayout_2.addWidget(self.label_3)
        self.label_4 = QtWidgets.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(12)
        self.label_4.setFont(font)
        self.label_4.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_4.setWordWrap(True)
        self.label_4.setObjectName("label_4")
        self.verticalLayout_2.addWidget(self.label_4)
        self.label_9 = QtWidgets.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(12)
        self.label_9.setFont(font)
        self.label_9.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_9.setWordWrap(True)
        self.label_9.setObjectName("label_9")
        self.verticalLayout_2.addWidget(self.label_9)
        self.label_5 = QtWidgets.QLabel(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_5.sizePolicy().hasHeightForWidth())
        self.label_5.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(12)
        self.label_5.setFont(font)
        self.label_5.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_5.setWordWrap(True)
        self.label_5.setObjectName("label_5")
        self.verticalLayout_2.addWidget(self.label_5)
        self.label_6 = QtWidgets.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(12)
        self.label_6.setFont(font)
        self.label_6.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_6.setWordWrap(True)
        self.label_6.setObjectName("label_6")
        self.verticalLayout_2.addWidget(self.label_6)
        self.horizontalLayout.addLayout(self.verticalLayout_2)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.Diagonal_LineEdit = QtWidgets.QLineEdit(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.Diagonal_LineEdit.sizePolicy().hasHeightForWidth())

        regex = QRegularExpression("^[1-9][0-9]*$")
        validator = QRegularExpressionValidator(regex)

        self.Diagonal_LineEdit.setSizePolicy(sizePolicy)
        self.Diagonal_LineEdit.setValidator(validator)

        font = QtGui.QFont()
        font.setPointSize(14)
        self.Diagonal_LineEdit.setFont(font)
        self.Diagonal_LineEdit.setText("")
        self.Diagonal_LineEdit.setObjectName("Diagonal_LineEdit")
        self.verticalLayout_3.addWidget(self.Diagonal_LineEdit)
        self.Distance_LineEdit_2 = QtWidgets.QLineEdit(self.centralwidget)
        self.Distance_LineEdit_2.setValidator(validator)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.Distance_LineEdit_2.sizePolicy().hasHeightForWidth())
        self.Distance_LineEdit_2.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(14)
        self.Distance_LineEdit_2.setFont(font)
        self.Distance_LineEdit_2.setText("")
        self.Distance_LineEdit_2.setObjectName("Distance_LineEdit_2")
        self.verticalLayout_3.addWidget(self.Distance_LineEdit_2)
        self.Distance_LineEdit_3 = QtWidgets.QLineEdit(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.Distance_LineEdit_3.sizePolicy().hasHeightForWidth())
        self.Distance_LineEdit_3.setSizePolicy(sizePolicy)
        self.Distance_LineEdit_3.setValidator(validator)

        font = QtGui.QFont()
        font.setPointSize(14)
        self.Distance_LineEdit_3.setFont(font)
        self.Distance_LineEdit_3.setText("")
        self.Distance_LineEdit_3.setObjectName("Distance_LineEdit_3")
        self.verticalLayout_3.addWidget(self.Distance_LineEdit_3)
        self.Distance_LineEdit = QtWidgets.QLineEdit(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.Distance_LineEdit.sizePolicy().hasHeightForWidth())
        self.Distance_LineEdit.setSizePolicy(sizePolicy)
        self.Distance_LineEdit.setValidator(validator)
        font = QtGui.QFont()
        font.setPointSize(14)
        self.Distance_LineEdit.setFont(font)
        self.Distance_LineEdit.setText("")
        self.Distance_LineEdit.setObjectName("Distance_LineEdit")
        self.verticalLayout_3.addWidget(self.Distance_LineEdit)
        self.DPI_LineEdit = QtWidgets.QLineEdit(self.centralwidget)
        self.DPI_LineEdit.setValidator(validator)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.DPI_LineEdit.sizePolicy().hasHeightForWidth())
        self.DPI_LineEdit.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(14)
        self.DPI_LineEdit.setFont(font)
        self.DPI_LineEdit.setText("")
        self.DPI_LineEdit.setObjectName("DPI_LineEdit")
        self.verticalLayout_3.addWidget(self.DPI_LineEdit)
        self.horizontalLayout.addLayout(self.verticalLayout_3)
        self.gridLayout.addLayout(self.horizontalLayout, 2, 0, 1, 1)
        self.Start_btn = QtWidgets.QPushButton(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.Start_btn.sizePolicy().hasHeightForWidth())
        self.Start_btn.setSizePolicy(sizePolicy)
        self.Start_btn.setMinimumSize(QtCore.QSize(0, 70))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.Start_btn.setFont(font)
        self.Start_btn.setStyleSheet("QPushButton {\n"
"    background-color: #69cc64;\n"
"}")
        self.Start_btn.setObjectName("Start_btn")
        self.gridLayout.addWidget(self.Start_btn, 3, 0, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 676, 24))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.clear_button = QtWidgets.QPushButton("Clear", self.centralwidget)
        self.clear_button.setMinimumSize(QtCore.QSize(0, 70))
        self.clear_button.setFont(QtGui.QFont("Segoe UI", 12))
        self.clear_button.setStyleSheet("QPushButton { background-color: #4a90e2; color: black; }")

        self.clear_button.clicked.connect(self.on_clear_button_clicked)

        self.button_layout = QtWidgets.QHBoxLayout()
        self.button_layout.addWidget(self.Start_btn)
        self.button_layout.addWidget(self.clear_button)

        self.gridLayout_2.addLayout(self.button_layout, 3, 0, 1, 1)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        self.setObjectName("MainWindow")

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Program"))
        self.label.setText(_translate("MainWindow", "Enter the file path or paste the URL link:"))
        self.ChooseFile_btn.setText(_translate("MainWindow", "Choose File"))
        self.label_7.setText(_translate("MainWindow", "Intermediate Outcomes"))
        self.label_8.setText(_translate("MainWindow", "Total Reading Time"))
        self.label_2.setText(_translate("MainWindow", "User Settings"))
        self.label_3.setText(_translate("MainWindow", "Monitor Diagonal (inches)"))
        self.label_4.setText(_translate("MainWindow", "Display Width (px)"))
        self.label_9.setText(_translate("MainWindow", "Display Height (px)"))
        self.label_5.setText(_translate("MainWindow", "Distance to Screen (cm)"))
        self.label_6.setText(_translate("MainWindow", "Pixel Density (DPI)"))
        self.Start_btn.setText(_translate("MainWindow", "Start Analysis"))

        self.DPI_LineEdit.setDisabled(True)
        self.DPI_LineEdit.setStyleSheet("""
            QLineEdit {
                background-color: #f0f0f0; /* Світліший фон */
                color: #a0a0a0; /* Світліший текст */
                border: 1px solid gray; /* Світла рамка */
            }
        """)

    def add_text_to_process_textedit(self, text):
        self.plainTextEdit.appendPlainText(text)

    def on_clear_button_clicked(self):
        self.plainTextEdit.clear()
        self.TotalTime_lineEdit.clear()

    def set_total_time_textedit(self, text):
        self.TotalTime_lineEdit.setText(text)

    def update_ppi_textedit(self, text):
        self.DPI_LineEdit.setText(text)

    def show_messagebox(self, name, text):
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle(name)
        msg.setText(text)
        msg.exec_()

    def get_path_chose_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog

        file_filter = "Word Files (*.doc *.docx);;PDF Files (*.pdf);; HTML Files (*.html *htm)"

        file_path, _ = QFileDialog.getOpenFileName(None, "Select File", "", file_filter, options=options)

        return file_path

    def on_choose_file_clicked(self):
        file_path = self.get_path_chose_file()
        self.URL_lineEdit.setText(file_path)
        self.url_changed.emit(file_path)
        if file_path:
            self.url_changed.emit(file_path)

    def send_data_to_worker(self):
        data = {"width_px": self.Distance_LineEdit_3.text(), "height_px": self.Distance_LineEdit_2.text(),
                "diagonal_inches": self.Diagonal_LineEdit.text(), "distance_cm": self.Distance_LineEdit.text()}
        self.data_sended.emit(data)
        time.sleep(0.02)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()

    ui.Start_btn.clicked.connect(ui.worker.start)
    ui.ChooseFile_btn.clicked.connect(ui.on_choose_file_clicked)
    ui.data_sended.connect(ui.worker.receive_data_from_ui)

    ui.Distance_LineEdit.textChanged.connect(ui.send_data_to_worker)
    ui.Distance_LineEdit_2.textChanged.connect(ui.send_data_to_worker)
    ui.Distance_LineEdit_3.textChanged.connect(ui.send_data_to_worker)
    ui.Diagonal_LineEdit.textChanged.connect(ui.send_data_to_worker)

    ui.start_thread()

    sys.exit(app.exec_())
