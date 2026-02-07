from tkinter import *
from matplotlib import *
from matplotlib.axes import Axes
from matplotlib.figure import *
import matplotlib.ticker as ticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from serial import Serial
from serial.tools.list_ports import comports
from threading import Thread, Lock
from time import time
from numpy.fft import fft, ifft
from scipy.signal import find_peaks
import numpy as np

display = Tk(className='Модуль А')
display.resizable(False, False)
display.focus_force()
T_X = 2


# region Формирование пользовательского интерфейса
def create_frame(col, row, width, height, cspan=1, rspan=1, cols=[0], rows=[0], border=1, master=display):
    frame = Frame(master, highlightbackground='black', highlightthickness=border)
    frame.grid(column=col, row=row, columnspan=cspan, rowspan=rspan)

    if len(cols):
        frame.columnconfigure(cols, minsize=width)
    if len(rows):
        frame.rowconfigure(rows, minsize=height)

    return frame


def create_label(frame, text, font='Times 24', justify='center', col=0, row=0, cspan=1, rspan=1):
    lbl = Label(frame, text=text, font=font, justify=justify)
    lbl.grid(column=col, row=row, columnspan=cspan, rowspan=rspan)
    return lbl


def min_mid_max(min, mid, max):
    return f'Мин. значение: {min}\nСр. значение: {mid}\nМакс. значение: {max}'


FONT = {'family': 'Times New Roman', 'size': 20}

create_label(ecg_fr := create_frame(0, 0, 350, 0), 'График ЭКГ')
ecg_figure = Figure((7, 7), 50)
ecg_canvas = FigureCanvasTkAgg(ecg_figure, ecg_fr)
ecg_canvas.get_tk_widget().grid(column=0, row=1)
ecg_axes: Axes = ecg_figure.add_axes(111)
ecg_axes.hlines([1000, 2000, 3000, 4000], [0, 0, 0, 0], [10000, 10000, 10000, 10000], 'gray')
ecg_axes.set_xlabel('Время, с', fontdict=FONT)
ecg_axes.set_ylabel('Напряжение, мВ', fontdict=FONT)
ecg_axes.set_xlim(0, T_X)
ecg_axes.set_ylim(0, 5000)
ecg_lines, = ecg_axes.plot([], [])
ecg_min_mid_max_lbl = create_label(ecg_fr, min_mid_max('', '', ''), 'Times 12', 'left', row=2)

create_label(emg_fr := create_frame(1, 0, 350, 0), 'График ЭМГ')
emg_figure = Figure((7, 7), 50)
emg_canvas = FigureCanvasTkAgg(emg_figure, emg_fr)
emg_canvas.get_tk_widget().grid(column=0, row=1)
emg_axes: Axes = emg_figure.add_axes(111)
emg_axes.set_xlabel('Частота, Гц', fontdict=FONT)
emg_axes.set_ylabel('Амплитуда', fontdict=FONT)
emg_axes.set_xlim(0, 200)
emg_axes.set_ylim(0, 100)
emg_lines, = emg_axes.plot([], [])
emg_min_mid_max_lbl = create_label(emg_fr, min_mid_max('', '', ''), 'Times 12', 'left', row=2)

arduino_lbl = create_label(create_frame(0, 2, 702, 0, 2), '')
# endregion

arduino = Serial()
lock = Lock()
start_time = 0
buf = bytearray()

x = []
ecg_data = []
emg_data = []


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
                            arduino = Serial(p.device, 250000)
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
            continue

        if len(data) != 3:
            continue

        if start_time == 0:
            start_time = time()
            continue

        lock.acquire()
        x.append(time() - start_time)
        ecg_data.append(data[0] / 255 * 5000)
        emg_data.append(data[1] / 255 * 5000)
        lock.release()

    xc = []
    ecgc = []
    emgc = []
    hrs = []
    hr_medians = []

    def copy_data():
        global xc, ecgc, emgc, x, ecg_data, emg_data
        lock.acquire()
        if (xl := x[-1]) - x[0] > T_X:
            for i, xi in enumerate(x):
                if xl - xi <= T_X:
                    break
            x = x[i:]
            ecg_data = ecg_data[i:]
            emg_data = emg_data[i:]

        xc = x.copy()
        ecgc = ecg_data.copy()
        emgc = emg_data.copy()
        lock.release()

    Thread(target=parse).start()

    def fft_data(data):
        f_data = fft(data)
        N = len(f_data)
        T = (max(xc) - min(xc)) / N
        xf = np.linspace(0, 1 / (2 * T), N // 2)

        return f_data, xf, N

    def plot_data():
        emg_fft, emgx, EMG_N = fft_data(emgc)
        emg_lines.set_data(emgx, emgy := 2 / EMG_N * np.abs(emg_fft)[:EMG_N // 2])

        if len(emgy) > 10:
            emg_min_mid_max_lbl['text'] = min_mid_max(
                int(min(emgy[1:200])),
                int(np.mean(emgy[1:200])),
                int(max(emgy[1:200]))
            )

        ecg_fft, ecgx, ECG_N = fft_data(ecgc)

        for i, f in enumerate(ecgx):
            if f > 30:
                ecg_fft[i] = ecg_fft[ECG_N - 1 - i] = 0

        ecg_ifft = np.real(ifft(ecg_fft))

        ecg_axes.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        ecg_axes.set_xlim(min(xc), max(max(xc), min(xc) + T_X))
        ecg_lines.set_data(xc, ecg_ifft)

        peaks = find_peaks(ecg_ifft, prominence=1500)[0]
        for text in ecg_axes.texts:
            text.remove()

        abs_distances = []
        hrs_ = []

        for i, p in enumerate(peaks):
            ecg_axes.annotate('R', (xc[p], 4000), font=FONT)

            if i:
                t = xc[p] - xc[peaks[i - 1]]
                hr = 60 / t
                if hr > 200 or hr < 30:
                    continue

                abs_distances.append(p - peaks[i - 1])
                hrs_.append(hr)

        if not len(hrs_):
            return

        d = int(np.median(abs_distances))
        l = len(xc)

        for p in peaks:
            if p - d // 3 >= 0: ecg_axes.annotate('P', (xc[p - d // 3], 2800), font=FONT)
            if p - d // 6 >= 0: ecg_axes.annotate('Q', (xc[p - d // 6], 1500), font=FONT)
            if p + d // 8 < l: ecg_axes.annotate('S', (xc[p + d // 8], 1700), font=FONT)
            if p + d // 3 < l: ecg_axes.annotate('T', (xc[p + d // 3], 2800), font=FONT)

        hrs.append(np.median(hrs_))

        if len(hrs) < 100:
            return

        hr_medians.append(np.median(hrs))
        hrs.pop(0)

        ecg_min_mid_max_lbl['text'] = min_mid_max(
            str(int(min(hr_medians))) + ' уд/мин',
            str(int(np.mean(hr_medians))) + ' уд/мин',
            str(int(max(hr_medians))) + ' уд/мин'
        )

        if len(hr_medians) > 10:
            hr_medians.pop(0)

    while True:
        display.update()
        ecg_canvas.draw_idle()
        emg_canvas.draw_idle()

        if not arduino.is_open:
            arduino_lbl['text'] = 'Подключите Arduino!'
            continue

        arduino_lbl['text'] = f'Arduino подключена к {arduino.name}!'

        if len(x) < 2:
            continue

        copy_data()

        plot_data()