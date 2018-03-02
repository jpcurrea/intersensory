#! /usr/bin/python

import sys
import time
import ISR                      # our module

# import qdarkstyle
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import (QApplication, QDesktopWidget, QInputDialog,
                             QLabel, QMainWindow, QProgressBar, QPushButton,
                             QSpinBox, QWidget)

#from threading import Thread

motor1_offset = 0
motor2_offset = 0

class Example(QMainWindow):

    def __init__(self, left_pin=17, right_pin=18):
        self.left_pin = left_pin
        self.right_pin = right_pin
        super(Example, self).__init__()
        self._thread = None
        self.initUI()

    def initUI(self):

        # duration wheel
        self.duration = QSpinBox(self)
        self.duration.move(110, 10)
        self.duration.setSuffix('s')
        self.duration.setAttribute(Qt.WA_MacShowFocusRect, False)
        self.duration.setMaximum(100000)
        self.duration.setValue(5*60)
        self.duration.setAlignment(Qt.AlignRight)
        durlb = QLabel('Duration:', self)
        durlb.adjustSize()
        durlb.move(20, 20)
        durlb.setFont(QFont("Arial", 10))

        # Pin 17 Column
        left_col = 110
        left_lb = QLabel('Pin 17', self)
        left_lb.adjustSize()
        left_lb.move(left_col, 45)
        left_lb.setFont(QFont("Arial", 10))
        left_lb.setAlignment(Qt.AlignCenter)
        # delay labels
        lb = QLabel('Audio delay:', self)
        lb.adjustSize()
        lb2 = QLabel('Motor delay:', self)
        lb2.adjustSize()
        lb.move(20, 80)
        lb.setFont(QFont("Arial", 10))
        lb2.move(20, 110)
        lb2.setFont(QFont("Arial", 10))
        # delay wheels
        # audio_delay1 wheel
        self.audio_delay1 = QSpinBox(self)
        self.audio_delay1.move(left_col, 70)
        self.audio_delay1.setSuffix('ms')
        self.audio_delay1.setAttribute(Qt.WA_MacShowFocusRect, False)
        self.audio_delay1.setMaximum(100000)
        self.audio_delay1.setValue(0)
        self.audio_delay1.setAlignment(Qt.AlignRight)
        # motor_delay1 wheel
        self.motor_delay1 = QSpinBox(self)
        self.motor_delay1.move(left_col, 100)
        self.motor_delay1.setSuffix('ms')
        self.motor_delay1.setAttribute(Qt.WA_MacShowFocusRect, False)
        self.motor_delay1.setMaximum(100000)
        self.motor_delay1.setAlignment(Qt.AlignRight)

        # Pin 18 column
        right_col = 220
        right_lb = QLabel('Pin 18', self)
        right_lb.adjustSize()
        right_lb.move(right_col, 45)
        right_lb.setFont(QFont("Arial", 10))
        right_lb.setAlignment(Qt.AlignCenter)
        # delay wheels
        # audio_delay2 wheel
        self.audio_delay2 = QSpinBox(self)
        self.audio_delay2.move(right_col, 70)
        self.audio_delay2.setSuffix('ms')
        self.audio_delay2.setAttribute(Qt.WA_MacShowFocusRect, False)
        self.audio_delay2.setMaximum(100000)
        self.audio_delay2.setAlignment(Qt.AlignRight)
        # motor_delay2 wheel
        self.motor_delay2 = QSpinBox(self)
        self.motor_delay2.move(right_col, 100)
        self.motor_delay2.setSuffix('ms')
        self.motor_delay2.setAttribute(Qt.WA_MacShowFocusRect, False)
        self.motor_delay2.setMaximum(100000)
        self.motor_delay2.setValue(500)
        self.motor_delay2.setAlignment(Qt.AlignRight)

        # status bar
        self.sb = self.statusBar()
        self.sb.showMessage('Ready')


        # window settings
        self.setWindowTitle('RoboQuail Synch/Async Bobbing')
        self.resize(500, 250)

        # action buttons
        button_col = 150
        # swap button to swap synch and asynch settings
        self.swap_button = QPushButton('Swap', self)
        self.swap_button.move(button_col, 130)
        self.swap_button.adjustSize()
        self.swap_button.setCheckable(True)
        self.swap_button.clicked.connect(self.swap)

        # start button
        self.button = QPushButton('Start Bobbing', self)
        self.button.move(button_col, 160)
        self.button.adjustSize()
        self.button.setCheckable(True)
        self.button.clicked.connect(self.onClick)

        # progress bar
        self.progressBar = QProgressBar(self)
        self.progressBar.setRange(0, 1)
        self.progressBar.move(button_col, 190)

        self.show()

    def swap(self):
        old_audio_delay1 = self.audio_delay1.value()
        old_audio_delay2 = self.audio_delay2.value()
        old_motor_delay1 = self.motor_delay1.value()
        old_motor_delay2 = self.motor_delay2.value()
        self.audio_delay1.setValue(old_audio_delay2)
        self.audio_delay2.setValue(old_audio_delay1)
        self.motor_delay1.setValue(old_motor_delay2)
        self.motor_delay2.setValue(old_motor_delay1)    

    def onClick(self):
        if self._thread is not None:
            if self._thread.isRunning():
                self._thread.stop_playing()
                self.button.setText('Start Bobbing')
            else:
                audio_delay1 = self.audio_delay1.value()
                motor_delay1 = self.motor_delay1.value()
                audio_delay2 = self.audio_delay2.value()
                motor_delay2 = self.motor_delay2.value()
                self.sb.showMessage(
                    "Running audio delays of {} and {} ms and motor delays\
                    {} and {} ms".format(
                    audio_delay1, audio_delay2,
                    motor_delay1, motor_delay2))
                motor_delay1 = motor_delay1 + motor1_offset
                motor_delay2 = motor_delay2 + motor2_offset
                self.progressBar.setRange(0, 0)
                self.button.setChecked(True)

                self._thread = MyThread(audio_delay1, motor_delay1,
                                        audio_delay2, motor_delay2,
                                        self.duration.value(),
                                        pin1=self.left_pin,
                                        pin2=self.right_pin)

                def updateUI(_):
                    self.sb.showMessage("Done")
                    self.button.setChecked(False)
                    self.progressBar.setRange(0, 1)

                self._thread.updated.connect(updateUI)
                self._thread.start()
                self.button.setText('Stop')
                
        else:
            audio_delay1 = self.audio_delay1.value()
            motor_delay1 = self.motor_delay1.value()
            audio_delay2 = self.audio_delay2.value()
            motor_delay2 = self.motor_delay2.value()
            self.sb.showMessage(
                "Running audio delays of {} and {} ms and motor delays of\
                {} and {} ms".format(
                    audio_delay1, audio_delay2,
                    motor_delay1, motor_delay2))
            motor_delay1 = motor_delay1 + motor1_offset
            motor_delay2 = motor_delay2 + motor2_offset
            self.progressBar.setRange(0, 0)
            self.button.setChecked(True)

            self._thread = MyThread(audio_delay1, motor_delay1,
                                audio_delay2, motor_delay2,
                                self.duration.value(),
                                pin1=self.left_pin, pin2=self.right_pin)

            def updateUI(_):
                self.sb.showMessage("Done")
                self.button.setChecked(False)
                self.progressBar.setRange(0, 1)
                self.button.setText('Start Bobbing')

            self._thread.updated.connect(updateUI)
            self._thread.start()
            self.button.setText('Stop')


class MyThread(QThread):
    updated = pyqtSignal(str)
    def __init__(self, audio_delay1, motor_delay1,
                 audio_delay2, motor_delay2,
                 duration, pin1=17, pin2=18):
        super(MyThread, self).__init__()
        self.audio_delay1 = audio_delay1/1000.
        self.motor_delay1 = motor_delay1/1000.
        self.audio_delay2 = audio_delay2/1000.
        self.motor_delay2 = motor_delay2/1000.
        self.duration = duration
        self.pin1 = pin1
        self.pin2 = pin2

    def run(self):
        # do some functionality
        # time.sleep(2)
        self.isr = ISR.A_2M_ISR("./maternal_call.wav", corr=1, corr_err=.1,
                                pwm_pin1=self.pin1, pwm_pin2=self.pin2,
                                motor1_delay=self.motor_delay1,
                                motor2_delay=self.motor_delay2,
                                audio_delay=self.audio_delay1)
        start = time.time()
        self.dur = 0
        while self.dur < self.duration:
            self.isr.play()
            self.dur = time.time() - start
            time.sleep(.1)
        self.isr.stop()
        self.updated.emit('Done')

        return

    def stop_playing(self):
        self.dur = self.duration
        
        return

if __name__ == '__main__':

    app = QApplication(sys.argv)
    # app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    ex = Example(left_pin=17, right_pin=18)
    sys.exit(app.exec_())
