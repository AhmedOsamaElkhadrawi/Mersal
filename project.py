import sys
import cv2
from ultralytics import YOLO
import functions
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QFileDialog, QFrame, QMessageBox, QGridLayout, QScrollArea, QStackedLayout, QComboBox
from PyQt5.QtGui import QImage, QPixmap, QIcon, QFont, QPalette, QBrush
from PyQt5.QtCore import QTimer, Qt, QSize
from gtts import gTTS
import pygame
import os
import threading
from deep_translator import GoogleTranslator

yolo_model_arabic = YOLO(r"D:\مشروع\models\best_ASL.pt")
yolo_model_english = YOLO(r"D:\مشروع\models\best.pt")

yolo_arabic_index = {
    0: 'ع', 1: 'ال', 2: 'ا', 3: 'ب', 4: 'د', 5: 'ظ', 6: 'ض', 7: 'ف', 8: 'ق', 9: 'غ', 10: 'ه',
    11: 'ح', 12: 'ج', 13: 'ك', 14: 'خ', 15: ' ', 16: 'ل', 17: 'م', 18: 'ن', 19: 'ر', 20: 'ص',
    21: 'س', 22: 'ش', 23: 'ت', 24: 'ط', 25: 'ث', 26: 'ذ', 27: 'و', 28: 'ي', 29: 'ز'
}

yolo_english_index = {
    0: 'A', 1: 'B', 2: 'C', 3: 'D', 4: 'E', 5: 'F', 6: 'G', 7: 'H', 8: 'I', 9: 'J',
    10: 'K', 11: 'L', 12: 'M', 13: 'N', 14: 'O', 15: 'P', 16: 'Q', 17: 'R', 18: 'S',
    19: 'T', 20: 'U', 21: 'V', 22: 'W', 23: 'X', 24: 'Y', 25: 'Z'
}

class ASLApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("مرسال")
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowIcon(QIcon("icon.png"))
        self.initUI()
        self.cap = None
        self.detection_active = False
        self.captured_letters = []
        self.formatted_sentence = ''
        self.shot_counter = 0
        self.char_check_dic = {'previous': 0, 'current': 0}
        self.flash_timer = QTimer()
        self.flash_timer.timeout.connect(self.reset_flash)
        self.flash_active = False
        self.current_language = 'arabic'
        pygame.mixer.init()
        self.translator = GoogleTranslator(source='auto', target='en')
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(central_widget)
        self.setCentralWidget(scroll_area)
        palette = QPalette()
        background_image = QImage(r"C:\Users\OO529\OneDrive\Desktop\pres\back_ground.jpg")
        background_image = background_image.scaled(1200, 800, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        palette.setBrush(QPalette.Background, QBrush(background_image))
        central_widget.setPalette(palette)
        layout = QVBoxLayout()
        header_layout = QHBoxLayout()
        header_layout.setAlignment(Qt.AlignRight | Qt.AlignTop)
        self.logo_label = QLabel(self)
        logo_image = QImage(r"C:\Users\OO529\OneDrive\Desktop\pres\logo.jpg")
        logo_image = logo_image.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo_pixmap = QPixmap.fromImage(logo_image)
        self.logo_label.setPixmap(logo_pixmap)
        self.logo_label.setAlignment(Qt.AlignRight)
        header_layout.addWidget(self.logo_label)
        title_label = QLabel("مرسال", self)
        title_label.setStyleSheet("""
            font-size: 48px;
            font-weight: bold;
            color: black;
            background-color: transparent;
            padding: 0px;
        """)
        title_label.setFont(QFont("Arial", 48, QFont.Bold))
        title_label.setAlignment(Qt.AlignRight)
        header_layout.addWidget(title_label)
        layout.addLayout(header_layout)
        self.video_label = QLabel(self)
        self.video_label.setStyleSheet("""
            background-color: transparent;
            border: none;
        """)
        layout.addWidget(self.video_label)
        self.sentence_label = QLabel("الجملة المكتشفة: ", self)
        self.sentence_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: black;
            background-color: transparent;
            padding: 20px;
            border: none;
        """)
        layout.addWidget(self.sentence_label)
        button_frame = QFrame()
        button_frame.setStyleSheet("""
            background-color: transparent;
            border: none;
        """)
        button_layout = QGridLayout()
        self.start_button = QPushButton("بدء الكشف", self)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: green;
                color: white;
                font-size: 18px;
                font-weight: bold;
                padding: 15px;
                border-radius: 10px;
                border: 2px solid #5E81AC;
            }
            QPushButton:hover {
                background-color: #81A1C1;
            }
            QPushButton:pressed {
                background-color: #4C566A;
            }
        """)
        self.start_button.clicked.connect(self.start_detection)
        button_layout.addWidget(self.start_button, 0, 0)
        self.stop_button = QPushButton("إيقاف الكشف", self)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: black;
                color: white;
                font-size: 18px;
                font-weight: bold;
                padding: 15px;
                border-radius: 10px;
                border: 2px solid #5E81AC;
            }
            QPushButton:hover {
                background-color: #81A1C1;
            }
            QPushButton:pressed {
                background-color: #4C566A;
            }
            QPushButton:disabled {
                background-color: #4C566A;
                color: #D8DEE9;
            }
        """)
        self.stop_button.setDisabled(True)
        self.stop_button.clicked.connect(self.stop_detection)
        button_layout.addWidget(self.stop_button, 0, 1)
        self.reset_button = QPushButton("إعادة تعيين", self)
        self.reset_button.setStyleSheet("""
            QPushButton {
                background-color: #5E81AC;
                color: white;
                font-size: 18px;
                font-weight: bold;
                padding: 15px;
                border-radius: 10px;
                border: 2px solid #5E81AC;
            }
            QPushButton:hover {
                background-color: #81A1C1;
            }
            QPushButton:pressed {
                background-color: #4C566A;
            }
        """)
        self.reset_button.clicked.connect(self.reset_sentence)
        button_layout.addWidget(self.reset_button, 0, 2)
        self.read_button = QPushButton("قراءة الجملة", self)
        self.read_button.setStyleSheet("""
            QPushButton {
                background-color: #5E81AC;
                color: white;
                font-size: 18px;
                font-weight: bold;
                padding: 15px;
                border-radius: 10px;
                border: 2px solid #5E81AC;
            }
            QPushButton:hover {
                background-color: #81A1C1;
            }
            QPushButton:pressed {
                background-color: #4C566A;
            }
        """)
        self.read_button.clicked.connect(self.read_sentence)
        button_layout.addWidget(self.read_button, 1, 0)
        self.translate_button = QPushButton("ترجمة الجملة", self)
        self.translate_button.setStyleSheet("""
            QPushButton {
                background-color: #5E81AC;
                color: white;
                font-size: 18px;
                font-weight: bold;
                padding: 15px;
                border-radius: 10px;
                border: 2px solid #5E81AC;
            }
            QPushButton:hover {
                background-color: #81A1C1;
            }
            QPushButton:pressed {
                background-color: #4C566A;
            }
        """)
        self.translate_button.clicked.connect(self.translate_sentence)
        button_layout.addWidget(self.translate_button, 1, 1)
        self.language_button = QPushButton("تبديل إلى الإنجليزية", self)
        self.language_button.setStyleSheet("""
            QPushButton {
                background-color: #5E81AC;
                color: white;
                font-size: 18px;
                font-weight: bold;
                padding: 15px;
                border-radius: 10px;
                border: 2px solid #5E81AC;
            }
            QPushButton:hover {
                background-color: #81A1C1;
            }
            QPushButton:pressed {
                background-color: #4C566A;
            }
        """)
        self.language_button.clicked.connect(self.toggle_language)
        button_layout.addWidget(self.language_button, 1, 2)
        self.delete_button = QPushButton("مسح الحرف الأخير", self)
        self.delete_button.setStyleSheet("""
            QPushButton {
                background-color: #5E81AC;
                color: white;
                font-size: 18px;
                font-weight: bold;
                padding: 15px;
                border-radius: 10px;
                border: 2px solid #5E81AC;
            }
            QPushButton:hover {
                background-color: #81A1C1;
            }
            QPushButton:pressed {
                background-color: #4C566A;
            }
        """)
        self.delete_button.clicked.connect(self.delete_last_char)
        button_layout.addWidget(self.delete_button, 2, 0)
        self.exit_button = QPushButton("إغلاق", self)
        self.exit_button.setStyleSheet("""
            QPushButton {
                background-color: #BF616A;
                color: white;
                font-size: 18px;
                font-weight: bold;
                padding: 15px;
                border-radius: 10px;
                border: 2px solid #BF616A;
            }
            QPushButton:hover {
                background-color: #D08770;
            }
            QPushButton:pressed {
                background-color: #A94442;
            }
        """)
        self.exit_button.clicked.connect(self.close)
        button_layout.addWidget(self.exit_button, 2, 1)
        button_frame.setLayout(button_layout)
        layout.addWidget(button_frame)
        central_widget.setLayout(layout)

    def toggle_language(self):
        if self.current_language == 'arabic':
            self.current_language = 'english'
            self.language_button.setText("تبديل إلى العربية")
        else:
            self.current_language = 'arabic'
            self.language_button.setText("تبديل إلى الإنجليزية")
        self.reset_sentence()

    def start_detection(self):
        self.detection_active = True
        self.start_button.setDisabled(True)
        self.stop_button.setDisabled(False)
        self.cap = cv2.VideoCapture(0)
        self.cap.set(3, 1200)
        self.cap.set(4, 720)
        self.timer.start(20)
        self.video_label.setVisible(True)
        self.sentence_label.setVisible(True)

    def stop_detection(self):
        self.detection_active = False
        self.start_button.setDisabled(False)
        self.stop_button.setDisabled(True)
        if self.cap:
            self.cap.release()
        self.timer.stop()

    def reset_sentence(self):
        self.captured_letters = []
        self.formatted_sentence = ''
        self.sentence_label.setText("الجملة المكتشفة: ")

    def reset_flash(self):
        self.flash_active = False
        self.flash_timer.stop()

    def read_sentence(self):
        if self.formatted_sentence:
            try:
                pygame.mixer.music.stop()
                pygame.mixer.quit()
                pygame.mixer.init()
                tts = gTTS(text=self.formatted_sentence, lang='ar' if self.current_language == 'arabic' else 'en')
                tts.save("output.mp3")
                pygame.mixer.music.load("output.mp3")
                pygame.mixer.music.play()
            except Exception as e:
                print(f"Error in read_sentence: {e}")

    def translate_sentence(self):
        if self.formatted_sentence:
            try:
                if self.current_language == 'arabic':
                    self.translator.target = 'en'
                    translated = self.translator.translate(self.formatted_sentence)
                else:
                    self.translator.target = 'ar'
                    translated = self.translator.translate(self.formatted_sentence)
                QMessageBox.information(self, "الترجمة", f"الترجمة: {translated}")
            except Exception as e:
                print(f"Error in translate_sentence: {e}")

    def delete_last_char(self):
        if self.captured_letters:
            self.captured_letters.pop()
            self.formatted_sentence = ''.join(self.captured_letters)
            self.sentence_label.setText(f"الجملة المكتشفة: {self.formatted_sentence}")

    def update_frame(self):
        if self.detection_active:
            ret, frame = self.cap.read()
            if ret:
                if self.current_language == 'arabic':
                    yolo_model = yolo_model_arabic
                    yolo_index = yolo_arabic_index
                else:
                    yolo_model = yolo_model_english
                    yolo_index = yolo_english_index
                yolo_result = yolo_model.predict(frame, device='cpu')
                if len(yolo_result[0].boxes.xyxy) > 0:
                    boxes = yolo_result[0].boxes.xyxy
                    class_ids = [int(i) for i in yolo_result[0].boxes.cls]
                    confidence = [float(i) for i in yolo_result[0].boxes.conf]
                    for box, conf, id in zip(boxes, confidence, class_ids):
                        if id not in yolo_index:
                            continue
                        if conf < 0.4:
                            continue
                        x1, y1, x2, y2 = map(int, box)
                        predicted_char = yolo_index[id]
                        self.char_check_dic, self.shot_counter = functions.Sequence_char_checker(id, self.char_check_dic, self.shot_counter)
                        if self.shot_counter >= 4:
                            self.captured_letters.append(predicted_char)
                            self.formatted_sentence = ''.join(self.captured_letters)
                            self.shot_counter = 0
                            self.flash_active = True
                            self.flash_timer.start(200)
                        if self.flash_active:
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
                        else:
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 0), 3)
                        word_on_box = functions.reshape(predicted_char)
                        frame = functions.Draw_arabic_text(frame, (x1, y1 - 50), word_on_box, 45, (0, 0, 0))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame.shape
                bytes_per_line = ch * w
                convert_to_Qt_format = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                self.video_label.setPixmap(QPixmap.fromImage(convert_to_Qt_format))
                self.sentence_label.setText(f"الجملة المكتشفة: {self.formatted_sentence}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ASLApp()
    window.show()
    sys.exit(app.exec_())