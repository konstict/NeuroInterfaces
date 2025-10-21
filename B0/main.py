from pandas import pandas as pd
import sys

import cv2
import face_recognition

from datetime import datetime
import serial
import time
import os
from collections import deque

from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5 import Qt
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPixmap, QImage, QMouseEvent

from first import Ui_MainWindow as firstClass
from registration import Ui_MainWindow as registrationClass
from inputId import Ui_MainWindow as inputIdClass
from authorization import Ui_MainWindow as authorizationClass

from instr import Ui_MainWindow as instrClass
from analizReg import Ui_MainWindow as analizRegClass
from analizAuth import Ui_MainWindow as analizAuthClass

class Program():
    def __init__(self):
        self.windowId = 0
        self.operatorId = -1
        self.old_pos = None
        self.logined = False
        self.foundId = False
        self.after = 0 # reg or auth

        self.port = 'COM7'
        self.baud_rate = 9600
        self.ser = None
        self.timePrev = time.time()

        self.timeStart = datetime.now()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.updateTime)
        self.timer.start(1000)

        self.cameraTimer = QtCore.QTimer()
        self.cap = None

        self.pulseTimer = QtCore.QTimer()
        self.pulseTimer.timeout.connect(self.updatePulse)
        self.pulses = deque(maxlen=5)
        self.pulseNow = 0
        self.pulseAvg = 0
        self.isPulse = False

        self.createFirstWindow()


    def __del__(self):
        print('finish')
        sys.exit(0)


    def updateTime(self): # постоянное обновление времени
        self.timeNow = datetime.now()
        if self.windowId == 4:
            self.authorizationUI.label_19.setText(self.timeNow.strftime(f'{self.timeNow.strftime("%d.%m.%Y")} / {self.timeNow.strftime("%H.%M.%S")}'))
            self.authorizationUI.label_20.setText(self.timeStart.strftime("%H.%M.%S"))

        file = self.initOperatorsDB()
        operatorIndex = -1
        self.foundId = False
        for i in file.to_dict('records'):
            operatorIndex += 1
            if i['id'] == self.operatorId:
                self.operatorIndex = operatorIndex
                file.loc[operatorIndex,'software_start_time'] = self.timeStart.strftime("%H-%M-%S")
                file.loc[operatorIndex,'date'] = self.timeNow.strftime("%d-%m-%Y")
                file.loc[operatorIndex,'time'] = self.timeNow.strftime("%H:%M:%S")
                file.loc[operatorIndex, 'current_pulse'] = self.pulseAvg
                self.thisOperatorInfo = i
                file.to_csv('operators_db.csv', index=False)
                self.foundId = True

        if self.foundId and self.logined:
            if self.windowId == 4:
                self.goodAuthorizationWindow()
            elif self.windowId == 2:
                self.goodRegistrationWindow()
            elif self.windowId == 6:
                if self.ser == None:
                    try:
                        self.ser = serial.Serial(self.port, self.baud_rate, timeout=1)
                    except:
                        self.analizUI.label_13.setText('Проверка сигнала..............................НЕ ОК')
                        self.analizUI.label_14.setText('Проверка пульса..............................НЕ ОК')
                        self.analizUI.label_15.setText('Пульс.............................................')
                        self.isPulse = False
                        self.analizUI.pushButton_2.setStyleSheet("color: white; border: 1px solid black; border-radius: 5px")
                        self.analizUI.label_16.close()
                        self.ser = None
                        self.pulseTimer.stop()
                    else:
                        self.analizUI.label_13.setText('Проверка сигнала..............................ОК')
                        if self.ser is not None and not self.pulseTimer.isActive():
                            self.pulseTimer.start(5)

                if (self.isPulse):
                    self.goodAnalizWindow()
        else:
            if self.windowId == 4:
                self.badAuthorizationWindow()
            elif self.windowId == 2:
                self.badRegistrationWindow()


    def createFirstWindow(self): # выбор регистрация или авторизация
        self.windowId = 1
        self.first = QtWidgets.QMainWindow()
        self.firstUI = firstClass()
        self.firstUI.setupUi(self.first)
        self.first.setWindowFlags(Qt.FramelessWindowHint)
        self.first.show()
        self.firstUI.pushButton.clicked.connect(self.createRegistrationWindow)
        self.firstUI.pushButton_2.clicked.connect(self.createInputIdWindow)

        self.firstUI.close.mouseReleaseEvent = self.finishProgram
        self.firstUI.top.mousePressEvent = lambda event: self.pressTopWindow(event, self.first)
        self.firstUI.top.mouseMoveEvent = lambda event: self.moveTopWindow(event, self.first)
        self.firstUI.top.releaseMouse = lambda event: self.releaseTopWindow(event, self.first)


    def pressTopWindow(self, event, window):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()
    def moveTopWindow(self, event, window):
        if self.old_pos:
            p = QPoint(event.globalPos() - self.old_pos)
            window.move(window.x() + p.x(), window.y() + p.y())
            self.old_pos = event.globalPos()
    def releaseTopWindow(self, event, window):
        self.old_pos = None
    def finishProgram(self, event):
        self.__del__()


    def createRegistrationWindow(self): # регистрация
        self.windowId = 2
        self.registration = QtWidgets.QMainWindow()
        self.registrationUI = registrationClass()
        self.registrationUI.setupUi(self.registration)
        self.registration.setWindowFlags(Qt.FramelessWindowHint)
        self.registration.show()
        self.first.close()
        self.badRegistrationWindow()
        self.registrationUI.pushButton.clicked.connect(self.regOperator)
        self.registrationUI.pushButton_3.clicked.connect(self.createInstrWindow)

        self.registrationUI.close.mouseReleaseEvent = self.finishProgram
        self.registrationUI.top.mousePressEvent = lambda event: self.pressTopWindow(event, self.registration)
        self.registrationUI.top.mouseMoveEvent = lambda event: self.moveTopWindow(event, self.registration)
        self.registrationUI.top.releaseMouse = lambda event: self.releaseTopWindow(event, self.registration)


    def badRegistrationWindow(self): # id не присвоен регистрация
        self.registrationUI.label_11.setText("Оператор не определен")
        self.registrationUI.label_15.setPixmap(QPixmap("photos/nook.png"))
        self.registrationUI.widget_13.setStyleSheet("background-color: rgb(200,0,0)")
        self.registrationUI.label_13.close()
        self.registrationUI.label_12.setText("ID не присвоен")
        self.registrationUI.pushButton_3.setStyleSheet("color: white; border: 1px solid black; border-radius: 5px")


    def goodRegistrationWindow(self): # id присвоен регистрация
        self.registrationUI.label_12.setText("ID")
        self.registrationUI.label_13.setText(f"{str(self.operatorId).zfill(6)}")
        self.registrationUI.label_15.setPixmap(QPixmap("photos/ok.png"))
        self.registrationUI.widget_13.setStyleSheet("background-color: rgb(0,200,0)")
        self.registrationUI.label_13.show()
        self.registrationUI.pushButton_3.setStyleSheet("background-color: black; color: white; border-radius: 5px")


    def initOperatorsDB(self): # инициализировать базу данных
        file = pd.DataFrame()
        if not os.path.exists('operators_db.csv'):
            file = pd.DataFrame(
                columns=["id", "last_name", "first_name", "middle_name", "age", "date", "time", "software_start_time",
                         "drive_duration", 'pulse_threshold_critical', 'pulse_normal', 'current_pulse'])
            file.to_csv('operators_db.csv', index=False)
        else:
            file = pd.read_csv('operators_db.csv')
        return file


    def regOperator(self): # записать информацию о операторе
        file = self.initOperatorsDB()

        operatorIdTemp = -1
        for i in file.to_dict("records"):
            operatorIdTemp = max(operatorIdTemp, i["id"])
        operatorIdTemp += 1
        self.operatorId = operatorIdTemp

        if (self.registrationUI.textEdit.toPlainText() != "" and self.registrationUI.textEdit_2.toPlainText() != "" and self.registrationUI.textEdit_4.toPlainText().isdigit()):
            self.thisOperatorInfo = {
                "id": self.operatorId, "last_name": self.registrationUI.textEdit.toPlainText(),
                "first_name": self.registrationUI.textEdit_2.toPlainText(),
                "middle_name": self.registrationUI.textEdit_3.toPlainText() if self.registrationUI.textEdit_3.toPlainText() != '' else ' ',
                "age": self.registrationUI.textEdit_4.toPlainText(),
                "date": self.timeNow.strftime("%d.%m.%Y"), "time": self.timeNow.strftime("%H.%M.%S"), "software_start_time": self.timeStart.strftime("%H.%M.%S"), "drive_duration": 0,
                'pulse_threshold_critical': 0, 'pulse_normal': 0, 'current_pulse': 0
            }
            self.newOperatorsDB = pd.concat([file, pd.DataFrame([self.thisOperatorInfo])], ignore_index=True)

            if self.cap is None or not self.cap.isOpened():
                self.cameraStart()


    def cameraStart(self): # инициализация камеры
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Ошибка в камере")
            return False

        self.frameFace = None
        self.frameFaceEncs = None

        if not self.cameraTimer.isActive():
            self.cameraTimer = QtCore.QTimer()
            self.cameraTimer.timeout.connect(self.cameraDetectFace)
            self.cameraTimer.start(20)


    def cameraDetectFace(self): # поиск лица
        print("detecting")
        ret, frame = self.cap.read()
        _, frameRectangle = self.cap.read()
        if ret and not frame is None:
            locations = face_recognition.face_locations(frame)
            if len(locations) > 0: # нашло первое лицо
                firstLocations = locations[0]
                for i in locations:
                    if abs(i[3]-i[1]) * abs(i[0]-i[2]) > abs(firstLocations[3]-firstLocations[1]) * abs(firstLocations[0]-firstLocations[2]):
                        firstLocations = i

                cv2.rectangle(frameRectangle, (firstLocations[3]-50, firstLocations[0]-50), (firstLocations[1]+50, firstLocations[2]+50), (255,255,255), 3)

                self.frameFace = frame[firstLocations[0]-50:firstLocations[2]+50, firstLocations[3]-50:firstLocations[1]+50]
                self.frameFaceEncs = face_recognition.face_encodings(frame, locations)[0]

                self.cameraTimer.stop()
                self.cap.release()

                if self.windowId == 2: self.regSaveFace()
                elif self.windowId == 4: self.authCheckFace()

            if self.windowId == 2: # при регистрации
                self.registrationUI.label_10.setPixmap(
                    QPixmap.fromImage(
                        QImage( cv2.cvtColor(cv2.resize(frameRectangle, dsize = (320, 200), interpolation = cv2.INTER_AREA), cv2.COLOR_BGR2RGB).data, 320, 200, QImage.Format_RGB888 )
                    )
                )
            elif self.windowId == 4: # при авторизации
                self.authorizationUI.label_10.setPixmap(
                    QPixmap.fromImage(
                        QImage( cv2.cvtColor(cv2.resize(frameRectangle, dsize = (320, 200), interpolation = cv2.INTER_AREA), cv2.COLOR_BGR2RGB).data, 320, 200, QImage.Format_RGB888 )
                    )
                )


    def regSaveFace(self): # сохранение лица
        if not os.path.exists("operators"):
            os.mkdir("operators")
        files = os.listdir("operators")  # список всех файлов и папок в директории

        faceExist = False
        for file in files:
            face = face_recognition.load_image_file(f"operators/{file}")

            locations = face_recognition.face_locations(face)
            if len(locations) > 0:
                firstLocations = locations[0]
                faceEnc = face_recognition.face_encodings(face, [firstLocations])[0]
                results = face_recognition.compare_faces([faceEnc], self.frameFaceEncs)
                for k in results:
                    faceExist = faceExist or k

        if faceExist:
            self.badRegistrationWindow()
            print("bad reg")
        else:
            print("good reg")
            self.logined = True
            self.goodRegistrationWindow()
            self.newOperatorsDB.to_csv('operators_db.csv', index=False)
            cv2.imwrite(f'operators/ID_{str(self.operatorId).zfill(6)}.jpg', self.frameFace)


    def authCheckFace(self): # идентификация лица
        if not os.path.exists("operators"):
            os.mkdir("operators")
        if not os.path.exists(f"operators/ID_{str(self.operatorId).zfill(6)}.jpg"):
            return 0
        face = face_recognition.load_image_file(f"operators/ID_{str(self.operatorId).zfill(6)}.jpg")
        locations = face_recognition.face_locations(face)
        if len(locations) > 0:
            firstLocations = locations[0]
            faceEnc = face_recognition.face_encodings(face)[0]
            results = face_recognition.compare_faces([faceEnc], self.frameFaceEncs)
            faceThis = False
            for k in results:
                faceThis = faceThis or k
            print(faceThis)
            if faceThis:
                self.goodAuthorizationWindow()
                self.logined = True
            else:
                self.badAuthorizationWindow()


    def createInputIdWindow(self): # ввод айди для авторизации
        self.windowId = 3
        self.inputId = QtWidgets.QMainWindow()
        self.inputIdUI = inputIdClass()
        self.inputIdUI.setupUi(self.inputId)
        self.inputId.setWindowFlags(Qt.FramelessWindowHint)
        self.inputId.show()
        self.inputIdUI.pushButton.clicked.connect(self.createAuthorizationWindow)
        self.first.close()

        self.inputIdUI.close.mouseReleaseEvent = self.finishProgram
        self.inputIdUI.top.mousePressEvent = lambda event: self.pressTopWindow(event, self.inputId)
        self.inputIdUI.top.mouseMoveEvent = lambda event: self.moveTopWindow(event, self.inputId)
        self.inputIdUI.top.releaseMouse = lambda event: self.releaseTopWindow(event, self.inputId)


    def createAuthorizationWindow(self): # авторизация
        file = self.initOperatorsDB()
        operatorIdTemp = int(self.inputIdUI.textEdit.toPlainText())
        name = ''
        age = 0
        indexTemp = 0
        for i in file.to_dict("records"):
            if operatorIdTemp == i["id"]:
                self.operatorId = operatorIdTemp
                name = f"{i['last_name']} {i['first_name']} {i['middle_name']}"
                age = str(i["age"])
                break
            indexTemp+=1

        if self.operatorId != -1:
            self.after = 1
            self.windowId = 4
            self.authorization = QtWidgets.QMainWindow()
            self.authorizationUI = authorizationClass()
            self.authorizationUI.setupUi(self.authorization)
            self.authorization.setWindowFlags(Qt.FramelessWindowHint)
            self.authorization.show()
            self.inputId.close()

            self.authorizationUI.close.mouseReleaseEvent = self.finishProgram
            self.authorizationUI.top.mousePressEvent = lambda event: self.pressTopWindow(event, self.authorization)
            self.authorizationUI.top.mouseMoveEvent = lambda event: self.moveTopWindow(event, self.authorization)
            self.authorizationUI.top.releaseMouse = lambda event: self.releaseTopWindow(event, self.authorization)

            self.authorizationUI.pushButton_3.clicked.connect(self.createInstrWindow)
            self.badAuthorizationWindow()
            self.authorizationUI.label_6.setText(name)
            self.authorizationUI.label_7.setText(f'{age} лет')
            if os.path.exists(f'operators/ID_{str(self.operatorId).zfill(6)}.jpg'):
                self.authorizationUI.label_16.setPixmap(QPixmap(f'operators/ID_{str(self.operatorId).zfill(6)}.jpg'))

            if self.cap is None or not self.cap.isOpened():
                self.cameraStart()


    def badAuthorizationWindow(self): # id не присвоен авторизация
        self.authorizationUI.label_11.setText("Оператор не определен")
        self.authorizationUI.label_15.setPixmap(QPixmap("photos/nook.png"))
        self.authorizationUI.widget_13.setStyleSheet("background-color: rgb(200,0,0)")
        self.authorizationUI.label_13.close()
        self.authorizationUI.label_12.setText("ID не присвоен")
        self.authorizationUI.pushButton_3.setStyleSheet("color: white; border: 1px solid black; border-radius: 5px")


    def goodAuthorizationWindow(self): # id присвоен авторизация
        self.authorizationUI.label_11.setText("Оператор определен")
        self.authorizationUI.label_12.setText("ID")
        self.authorizationUI.label_13.setText(f"{str(self.operatorId).zfill(6)}")
        self.authorizationUI.label_15.setPixmap(QPixmap("photos/ok.png"))
        self.authorizationUI.widget_13.setStyleSheet("background-color: rgb(0,200,0)")
        self.authorizationUI.label_13.show()
        self.authorizationUI.pushButton_3.setStyleSheet("background-color: black; color: white; border-radius: 5px")


    def createInstrWindow(self): # инструкция
        if self.foundId and self.logined:
            self.windowId = 5
            self.instr = QtWidgets.QMainWindow()
            self.instrUI = instrClass()
            self.instrUI.setupUi(self.instr)
            self.instr.setWindowFlags(Qt.FramelessWindowHint)
            self.instr.show()
            self.instrUI.pushButton_2.clicked.connect(self.createAnalizWindow)
            self.instrUI.label_10.setText(f"{str(self.thisOperatorInfo.get('last_name'))} {str(self.thisOperatorInfo.get('first_name'))}")
            if self.after == 0:
                self.registration.close()
            else:
                self.authorization.close()

            self.instrUI.close.mouseReleaseEvent = self.finishProgram
            self.instrUI.widget.mousePressEvent = lambda event: self.pressTopWindow(event, self.instr)
            self.instrUI.widget.mouseMoveEvent = lambda event: self.moveTopWindow(event, self.instr)
            self.instrUI.widget.releaseMouse = lambda event: self.releaseTopWindow(event, self.instr)


    def updatePulse(self):
        try:
            serInWaiting = self.ser.in_waiting
        except:
            self.ser = None
            self.pulseTimer.stop()
        else:
            if serInWaiting > 0:
                try:
                    value = self.ser.readline().decode('utf-8').strip()

                except: pass
                else:
                    if self.windowId == 6:
                        if value is None:
                            self.analizUI.label_14.setText('Проверка пульса..............................НЕ ОК')
                            self.isPulse = False
                    if value != '':
                        self.analizUI.label_14.setText('Проверка пульса..............................ОК')

                        if (str(self.thisOperatorInfo['pulse_threshold_critical']).isdigit() and str(
                                self.thisOperatorInfo['pulse_threshold_critical']) != '0'
                                and str(self.thisOperatorInfo['pulse_normal']).isdigit() and str(
                                    self.thisOperatorInfo['pulse_normal']) != '0'):
                            self.isPulse = True

                        if int(value) >= 150:
                            diff = time.time() - self.timePrev
                            if diff >= 0.4:
                                self.pulseNow = int(60 / diff)
                                self.pulses.append(self.pulseNow)
                                self.timePrev = time.time()

                                lenPulses = self.pulses.__len__()
                                sumPulses = 0
                                for i in range(0, lenPulses):
                                    sumPulses += self.pulses[i]
                                self.pulseAvg = self.pulseNow #int(sumPulses / lenPulses)

                                if self.windowId == 6:
                                    self.analizUI.label_15.setText('Пульс.............................................' + str(self.pulseAvg))


    def createAnalizWindow(self):
        self.windowId = 6
        self.analiz = QtWidgets.QMainWindow()
        if self.after == 0:
            self.analizUI = analizRegClass()
        else:
            self.analizUI = analizAuthClass()
        self.analizUI.setupUi(self.analiz)
        self.analiz.setWindowFlags(Qt.FramelessWindowHint)
        self.instr.close()
        self.analiz.show()
        self.analizUI.label_10.setText(f"{str(self.thisOperatorInfo.get('last_name'))} {str(self.thisOperatorInfo.get('first_name'))}")
        self.analizUI.label_16.close()
        self.analizUI.pushButton_2.setStyleSheet("color: white; border: 1px solid black; border-radius: 5px")
        if self.after == 0:
            self.analizUI.pushButton_3.clicked.connect(self.regOperatorPulse)
        else:
            self.analizUI.label_17.setText(str(self.thisOperatorInfo.get('pulse_threshold_critical')))
            self.analizUI.label_18.setText(str(self.thisOperatorInfo.get('pulse_normal')))

        self.analizUI.close.mouseReleaseEvent = self.finishProgram
        self.analizUI.widget.mousePressEvent = lambda event: self.pressTopWindow(event, self.analiz)
        self.analizUI.widget.mouseMoveEvent = lambda event: self.moveTopWindow(event, self.analiz)
        self.analizUI.widget.releaseMouse = lambda event: self.releaseTopWindow(event, self.analiz)


    def goodAnalizWindow(self):
        self.analizUI.label_16.show()
        self.analizUI.pushButton_2.setStyleSheet("background-color: black; color: white; border-radius: 5px")


    def regOperatorPulse(self):
        file = self.initOperatorsDB()

        if (self.analizUI.textEdit.toPlainText().isdigit() and self.analizUI.textEdit_2.toPlainText().isdigit()):
            file.loc[self.operatorIndex, 'pulse_threshold_critical'] = int(self.analizUI.textEdit.toPlainText())
            file.loc[self.operatorIndex, 'pulse_normal'] = int(self.analizUI.textEdit_2.toPlainText())
            file.to_csv('operators_db.csv', index=False)


app = QtWidgets.QApplication([])
pr = Program()
app.exec()