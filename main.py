import sys


from PyQt6 import uic
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import QApplication, QMainWindow, QDialog
from serial import Serial
import serial
import serial.tools.list_ports
from threading import Thread, Lock
from serial.tools.list_ports import comports
import subprocess

ICON_PATH = "images/"
arduino = Serial()
lock = Lock()
start_time = 0
buf = bytearray()


class Nanny(QMainWindow):
    def setup_icons(self):
        self.button_light.setIcon(QIcon(f"{ICON_PATH}light.png"))
        self.button_camera.setIcon(QIcon(f"{ICON_PATH}camera.png"))
        self.button_song.setIcon(QIcon(f"{ICON_PATH}music.png"))
        self.button_radio.setIcon(QIcon(f"{ICON_PATH}radio.png"))
        self.button_bed.setIcon(QIcon(f"{ICON_PATH}bed.png"))

        self.button_light.setIconSize(QSize(80, 80))
        self.button_camera.setIconSize(QSize(80, 80))
        self.button_song.setIconSize(QSize(80, 80))
        self.button_radio.setIconSize(QSize(80, 80))
        self.button_bed.setIconSize(QSize(80, 80))

        self.c = "no_c"
        self.l = "no_l"
        self.v = "no_v"
        self.r = "no_r"
        self.s = "no_s"

        def readline():
            global buf
            i = buf.find(b'\xff')
            if i >= 0:
                ret = buf[:i + 1]
                buf = buf[i + 1:]
                return ret
            while True:
                i = min(max(arduino.in_waiting, 1), 2048)
                data = arduino.read(i)
                i = data.find(b'\xff')
                if i >= 0:
                    r = buf + data[:i + 1]
                    buf[0:] = data[i + 1:]
                    return r
                buf.extend(data)

        def parse():
            global start_time, arduino, x, ecg_data, emg_data
            while True:

                if not arduino.is_open:
                    for p in comports():
                        if p.manufacturer and 'Arduino' in p.manufacturer:
                            while True:
                                try:
                                    arduino = Serial(p.device, 9600)
                                except:
                                    continue
                                break
                            print('Arduino подключена!', p.device)
                            continue
                    continue

                try:
                    data = readline()
                except:
                    start_time = 0
                    arduino.close()
                    print('Arduino отключена!')
                    x = []
                    ecg_data = []
                    emg_data = []

        Thread(target=parse).start()

    def __init__(self):
        super().__init__()
        uic.loadUi('nanny.ui', self)
        self.setWindowTitle('Управление умной няной')
        self.setFixedSize(700, 650)
        self.move(300, 90)

        self.setup_icons()

        self.wi = QMainWindow()

        self.light_turn_on = True
        self.song_turn_on = True
        self.radio_turn_on = True
        self.bed_is_shaking = True

        self.button_light.clicked.connect(self.light)
        self.button_camera.clicked.connect(self.camera)
        self.button_song.clicked.connect(self.song)
        self.button_radio.clicked.connect(self.radio)
        self.button_bed.clicked.connect(self.bed)

    def light(self):
        if self.light_turn_on:
            print('Я зажгла свет')
            self.l = "yes_l"
            message = f"{self.c}\n{self.l}\n{self.v}\n{self.r}\n{self.s}"
            self.send_to_arduino(message.encode())
        else:
            print('Я выключила свет')
            self.l = "no_l"
            message = f"{self.c}\n{self.l}\n{self.v}\n{self.r}\n{self.s}"
            self.send_to_arduino(message.encode())
        self.light_turn_on = not self.light_turn_on

    def camera(self):
        self.di = QDialog()
        uic.loadUi('camera.ui', self.di)
        self.di.show()
        self.di.setWindowTitle('Видеонаблюдение')

        self.di.btn.clicked.connect(self.cl)

    def cl(self):
        self.di.close()

    def song(self):
        if self.song_turn_on:
            print('Я спела песню')
            self.c = "yes_c"
            message = f"{self.c}\n{self.l}\n{self.v}\n{self.r}\n{self.s}"
            self.send_to_arduino(message.encode())
        else:
            print('Я прекратила петь песню')
            self.c = "no_c"
            message = f"{self.c}\n{self.l}\n{self.v}\n{self.r}\n{self.s}"
            self.send_to_arduino(message.encode())
        self.song_turn_on = not self.song_turn_on

    def radio(self):
        if self.radio_turn_on:
            print('Я работаю как радио няня')
            self.send_to_arduino(b"yes_r")

        else:
            print('Я уже не работаю как радио няня')
            self.send_to_arduino(b"no_r")
        self.radio_turn_on = not self.radio_turn_on

    def bed(self):
        if self.bed_is_shaking:
            print('Качаю кроватку')
            self.s = "yes_s"
            message = f"{self.c}\n{self.l}\n{self.v}\n{self.r}\n{self.s}"
            self.send_to_arduino(message.encode())
        else:
            print('Теперь не качаю')
            self.s = "no_s"
            message = f"{self.c}\n{self.l}\n{self.v}\n{self.r}\n{self.s}"
            self.send_to_arduino(message.encode())
        self.bed_is_shaking = not self.bed_is_shaking

    def send_to_arduino(self, data):
        try:
            arduino.write(data)  # Отправляем строку
            # Или для бинарных данных: arduino.write(bytes([data]))
            print(f"Отправлено: {data}")
        except Exception as e:
            print(f"Ошибка отправки: {e}")


def except_hook(cls, exception, traceback):
    sys.excepthook(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Nanny()
    ex.show()
    sys.exit(app.exec())