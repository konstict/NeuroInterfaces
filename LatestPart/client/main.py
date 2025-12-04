from pandas import pandas as pd
import sys

import cv2
import face_recognition

from datetime import datetime, timedelta
import os
import serial
import serial.tools.list_ports
import time
import numpy as np
import mediapipe as mp
import math
import pygame
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
from analizAuth import Ui_MainWindow as analizAuthClass
from analizReg import Ui_MainWindow as analizRegClass

from upr import Ui_MainWindow as uprClass

import socketClient

class Program():
    def __init__(self):
        self.windowId = 0
        self.old_pos = None

        self.after = 0 # 0 - reg, 1 - log
        self.thisOperatorInfo = None
        self.operatorId = -1
        self.operatorIndex = -1
        self.logined = False
        self.foundId = False
        self.fullMode = False # переключатся между инструкцией, анализом и управлением
        self.driveTime = timedelta(hours=0,minutes=0,seconds=0)

        self.timeStart = datetime.now()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.updateTime)
        self.timer.start(1000)

        self.cap = None

        self.cameraLogRegTimer = QtCore.QTimer()
        self.cameraLogRegTimer.timeout.connect(self.cameraDetectLogRegFace)

        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh =  self.mp_face_mesh.FaceMesh(
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.7,
                min_tracking_confidence=0.7
        )
        self.LEFT_EYE = [33, 160, 158, 133, 153, 144]
        self.RIGHT_EYE = [362, 385, 387, 263, 373, 380]
        self.timeLastCameraSleep = time.time()
        self.headBadTime = 0
        self.eyesBadTime = 0
        self.badHead = False
        self.stateOperator = 0 # 0 - green, 1 - yellow, 2 - red
        self.cameraSleepTimer = QtCore.QTimer()
        self.cameraSleepTimer.timeout.connect(self.cameraDetectSleepFace)

        self.capVideoBG = cv2.VideoCapture('./photos/videoBG.mp4')
        self.backgroundVideoUprTimer = QtCore.QTimer()
        self.backgroundVideoUprTimer.timeout.connect(self.backgroundVideoUpr)

        self.port = 'COM7'
        self.baudrate = 9600
        self.ser = None
        self.pulseQueue = deque(maxlen=10)
        self.pulse = 0
        self.pulseTimer = QtCore.QTimer()
        self.pulseTimer.timeout.connect(self.updatePulse)
        self.prevPulseTime = time.time()

        self.clientTimer = QtCore.QTimer()
        self.clientTimer.timeout.connect(self.clientSendFiles)
        self.clientTimer.start(3000)

        try:
            pygame.mixer.init()
        except: pass

        self.createFirstWindow()
    def __del__(self):
        print('finish')
        sys.exit(0)

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
    def finishProgram(self, event = None):
        self.__del__()



    def updateTime(self): # постоянное обновление времени
        self.timeNow = datetime.now()
        if self.windowId == 4:
            self.authorizationUI.label_19.setText(self.timeNow.strftime(f'{self.timeNow.strftime("%d.%m.%Y")} / {self.timeNow.strftime("%H:%M:%S")}'))
            self.authorizationUI.label_20.setText(self.timeStart.strftime("%H:%M:%S"))

        file = self.initOperatorsDB()
        operatorIndex = -1
        self.foundId = False
        for i in file.to_dict('records'):
            operatorIndex += 1
            if i['id'] == self.operatorId:
                self.operatorIndex = operatorIndex
                file.loc[operatorIndex,'software_start_time'] = self.timeStart.strftime("%H:%M:%S")
                file.loc[operatorIndex,'date'] = self.timeNow.strftime("%d.%m.%Y")
                file.loc[operatorIndex,'time'] = self.timeNow.strftime("%H:%M:%S")
                file.loc[operatorIndex,'drive_duration'] = datetime.strptime(str(self.driveTime), '%H:%M:%S').strftime('%H:%M:%S')
                if self.stateOperator == 2:
                    file.loc[operatorIndex,'operator_status'] = 'CRITICAL'
                elif self.stateOperator == 1:
                    file.loc[operatorIndex,'operator_status'] = 'WARNING'
                else:
                    file.loc[operatorIndex,'operator_status'] = 'NORMAL'
                file.loc[operatorIndex,'current_pulse'] = self.pulse
                self.thisOperatorInfo = i
                file.to_csv('operators_db.csv', index=False)
                self.foundId = True

        if self.foundId and self.logined:
            if self.windowId == 4:
                self.goodAuthorizationWindow()
            elif self.windowId == 2:
                self.goodRegistrationWindow()
            elif self.windowId == 6:
                if self.after == 1:
                    self.analizUI.label_19.setText(str(self.thisOperatorInfo['pulse_threshold_critical']))
                    self.analizUI.label_20.setText(str(self.thisOperatorInfo['pulse_normal']))
                if self.ser is None:
                    try:
                        self.fullMode = False
                        self.pulse = 0
                        self.port = serial.tools.list_ports.comports()[0].device
                        self.ser = serial.Serial(port = self.port, baudrate = self.baudrate)
                    except:
                        self.fullMode = False
                        self.ser = None
                        self.pulse = 0
                        self.analizUI.label_13.setText('Проверка сигнала..................НЕ ОК')
                        self.analizUI.label_14.setText('Проверка пульса..................НЕ ОК')
                        self.analizUI.label_15.setText('Пульс.............................................')
                        self.analizUI.label_16.close()
                        self.analizUI.pushButton_2.setStyleSheet("background-color: rgb(200,200,200); color: black; border-radius: 5px; border: 2px solid black")
                        self.pulseTimer.stop()
                    else:
                        self.analizUI.label_13.setText('Проверка сигнала..................ОК')
                        if self.ser and not self.pulseTimer.isActive():
                            self.pulseTimer.start(0)
                elif self.ser is not None and self.pulse != 0:
                    self.analizUI.label_13.setText('Проверка сигнала..................ОК')
                    self.analizUI.label_14.setText('Проверка пульса..................ОК')
                    self.analizUI.label_15.setText('Пульс............................................' + str(self.pulse))
                    if str(self.thisOperatorInfo['pulse_threshold_critical']).isdigit() and str(self.thisOperatorInfo['pulse_normal']).isdigit() \
                            and self.thisOperatorInfo['pulse_threshold_critical'] > 0 and self.thisOperatorInfo['pulse_normal'] > 0 :
                        self.analizUI.label_16.show()
                        self.fullMode = True
                        self.analizUI.pushButton_2.setStyleSheet("background-color: black; color: white; border-radius: 5px")
                    else:
                        self.fullMode = False
                        self.analizUI.label_16.close()
                        self.analizUI.pushButton_2.setStyleSheet("background-color: rgb(200,200,200); color: black; border-radius: 5px; border: 2px solid black")

            elif self.windowId == 7:
                if self.fullMode:
                    self.driveTime = self.driveTime + timedelta(seconds=1, minutes=0, hours=0)
                    if self.driveTime.seconds >= 32400:
                        self.finishProgram()
                if self.ser is None:
                    try:
                        self.pulse = 0
                        self.port = serial.tools.list_ports.comports()[0].device
                        self.ser = serial.Serial(port = self.port, baudrate = self.baudrate)
                    except:
                        self.pulse = 0
                        self.ser = None
                        self.pulseTimer.stop()
                    else:
                        if self.ser and not self.pulseTimer.isActive():
                            self.pulseTimer.start(0)
                self.uprUI.label_16.setText(f"{self.timeNow.strftime('%d.%m.%Y')} / {self.thisOperatorInfo['time']}")
                self.uprUI.label_17.setText(f"{self.timeStart.strftime('%H:%M:%S')}")
                self.uprUI.label_20.setText(f'{self.pulse}')
                if self.stateOperator == 1:
                    self.uprUI.label_15.setText(f'Пульс {self.pulse}')
                else:
                    self.uprUI.label_22.setText(f'Пульс {self.pulse}')

                if (self.headBadTime >= 4 and self.eyesBadTime >= 3) or (self.pulse >= self.thisOperatorInfo['pulse_threshold_critical'] or self.pulse <= 10):
                    self.redIndicator()
                elif (self.badHead and self.eyesBadTime >= 3) or (self.pulse >= self.thisOperatorInfo['pulse_normal'] or self.pulse <= 40):
                    self.yellowIndicator()
                else:
                    self.greenIndicator()

                driveTimeForm = datetime.strptime(str(timedelta(seconds=((timedelta(hours=9) - self.driveTime).seconds % 86400))), '%H:%M:%S')
                self.uprUI.label_14.setText(str(driveTimeForm.hour).zfill(2)[0])
                self.uprUI.label_23.setText(str(driveTimeForm.hour).zfill(2)[1])
                self.uprUI.label_24.setText(str(driveTimeForm.minute).zfill(2)[0])
                self.uprUI.label_25.setText(str(driveTimeForm.minute).zfill(2)[1])

        else:
            if self.windowId == 4:
                self.badAuthorizationWindow()
            elif self.windowId == 2:
                self.badRegistrationWindow()

    def updatePulse(self):
        try:
            serInWaiting = self.ser.in_waiting
        except:
            self.pulse = 0
            self.ser = None
            self.pulseTimer.stop()
        else:
            if serInWaiting > 0:
                try:
                    line = self.ser.readline().decode().strip()

                except: pass
                else:
                    if line != '':
                        # self.pulse = int(line)
                        # or this ->
                        self.pulseQueue.append(int(line))
                        sumTemp = 0
                        for i in self.pulseQueue:
                            sumTemp += i
                        print(list(self.pulseQueue), sumTemp, self.pulseQueue.maxlen)
                        self.pulse = int(sumTemp / self.pulseQueue.maxlen)

    def cameraDetectLogRegFace(self): # поиск лица
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

                self.cameraLogRegTimer.stop()
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

    def cameraDetectSleepFace(self): # поиск лица
        ret, frame = self.cap.read()
        if ret and not frame is None:
            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, _ = rgb.shape

            results = self.face_mesh.process(rgb)

            if not results.multi_face_landmarks:
                self.eyesBadTime = 5
                self.headBadTime = 5
            else:
                mesh = results.multi_face_landmarks[0].landmark
                minCoord, maxCoord = [1,1], [0,0]
                for id, coords in enumerate(mesh):
                    minCoord[0] = min(coords.x, minCoord[0])
                    minCoord[1] = min(coords.y, minCoord[1])
                    maxCoord[0] = max(coords.x, maxCoord[0])
                    maxCoord[1] = max(coords.y, maxCoord[1])
                    if id in self.LEFT_EYE or id in self.RIGHT_EYE or id in [1,152,33,263]: pass
                        # color = (0,0,255)
                        # cv2.circle(frame, (int(coords.x*w), int(coords.y*h)), 1, color, 1)
                    # cv2.putText(frame, str(id), (int(coords.x*w*otbit), int(coords.y*h*otbit)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 2)

                minCoord[0] = max(min(int(minCoord[0] * w-50), w), 0)
                minCoord[1] = max(min(int(minCoord[1] * h-50), h), 0)
                maxCoord[0] = max(min(int(maxCoord[0] * w+50), w), 0)
                maxCoord[1] = max(min(int(maxCoord[1] * h+50), h), 0)

                # cv2.circle(rgb, (int(minCoord[0]), int(minCoord[1])), 5, color, 5)
                # cv2.circle(rgb, (int(maxCoord[0]), int(maxCoord[1])), 5, color, 5)

                frame = frame[(minCoord[1]):(maxCoord[1]), (minCoord[0]):(maxCoord[0])]

                left_ear = self.getEar(np.array([(mesh[i].x, mesh[i].y) for i in self.LEFT_EYE]))
                right_ear = self.getEar(np.array([(mesh[i].x, mesh[i].y) for i in self.RIGHT_EYE]))
                avg_ear = (left_ear + right_ear) / 2

                nose_tip = mesh[1]
                chin = mesh[152]
                left_eye = mesh[33]
                right_eye = mesh[263]
                eyeCenterY = (left_eye.y + right_eye.y) / 2
                pitch = (nose_tip.y - eyeCenterY) / (chin.y - eyeCenterY)
                roll = (right_eye.y - left_eye.y) / (right_eye.x - left_eye.x)

                pitchDegr = math.degrees(pitch)
                rollDegr = math.degrees(roll)


                if not (-40 <= rollDegr <= 40) or not (pitchDegr <= 35):
                    self.badHead = True
                else: self.badHead = False
                # print(avg_ear, '0.2')
                # print(rollDegr, '-40 40')
                # print(pitchDegr, '35')

                if avg_ear <= 0.2:
                    self.eyesBadTime += time.time() - self.timeLastCameraSleep
                else: self.eyesBadTime = 0
                if self.badHead:
                    self.headBadTime += time.time() - self.timeLastCameraSleep
                else: self.headBadTime = 0

                # print(f"Pitch: {pitchDegr}°")
                # print(f"Roll: {rollDegr}")
                # print(f'head {self.headBadTime}')
                # print(f'eyes {self.eyesBadTime}')

                self.timeLastCameraSleep = time.time()
            try:
                self.uprUI.close_4.setPixmap(
                    QPixmap.fromImage(
                        QImage( cv2.cvtColor(cv2.resize(frame, dsize = (320, 200), interpolation = cv2.INTER_AREA), cv2.COLOR_BGR2RGB).data, 320, 200, QImage.Format_RGB888 )
                    )
                )
            except: pass

    def backgroundVideoUpr(self):
        ok, frame = self.capVideoBG.read()
        if not ok:
            self.capVideoBG.set(cv2.CAP_PROP_POS_FRAMES, 0)
            return

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        qimg = QImage(frame.data, w,h, QImage.Format_RGB888)
        pix = QPixmap.fromImage(qimg)
        self.uprUI.close_3.setPixmap(pix)

    def clientSendFiles(self):
        socketClient.main()



    def initOperatorsDB(self): # инициализировать базу данных
        file = pd.DataFrame()
        if not os.path.exists('operators_db.csv'):
            file = pd.DataFrame(
                columns=["id", "last_name", "first_name", "middle_name", "age", "date", "time", "software_start_time",
                         "drive_duration", 'pulse_threshold_critical', 'pulse_normal', 'current_pulse', 'operator_status'])
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
                'pulse_threshold_critical': 0, 'pulse_normal': 0, 'current_pulse': 0, 'operator_status': 'NORMAL'
            }
            self.newOperatorsDB = pd.concat([file, pd.DataFrame([self.thisOperatorInfo])], ignore_index=True)

            if self.cap is None or not self.cap.isOpened():
                self.cap = cv2.VideoCapture(0)
                if not self.cap.isOpened():
                    print("Ошибка в камере")
                    return False

                self.frameFace = None
                self.frameFaceEncs = None

                if not self.cameraLogRegTimer.isActive():
                    self.cameraLogRegTimer.start(20)

    def regOperatorPulse(self):
        if self.analizUI.textEdit.toPlainText().isdigit() and self.analizUI.textEdit_2.toPlainText().isdigit():
            file = self.initOperatorsDB()
            file.loc[self.operatorIndex, 'pulse_threshold_critical'] = int(self.analizUI.textEdit.toPlainText())
            file.loc[self.operatorIndex, 'pulse_normal'] = int(self.analizUI.textEdit_2.toPlainText())
            file.to_csv('operators_db.csv', index=False)


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


    def getEar(self, eye_landmarks):
        """Расчёт Eye Aspect Ratio — определение закрытия глаз."""
        # eye_landmarks — массив из 6 точек (x, y)
        A = np.linalg.norm(eye_landmarks[1] - eye_landmarks[5])
        B = np.linalg.norm(eye_landmarks[2] - eye_landmarks[4])
        C = np.linalg.norm(eye_landmarks[0] - eye_landmarks[3])
        res = (A + B) / (2.0 * C)
        return res



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
        operatorIdTemp = self.inputIdUI.textEdit.toPlainText()
        if operatorIdTemp == '': return
        name = ''
        age = 0
        indexTemp = 0
        for i in file.to_dict("records"):
            if int(operatorIdTemp) == i["id"]:
                self.operatorId = int(operatorIdTemp)
                name = f"{i['last_name']} {i['first_name']} {i['middle_name']}"
                age = str(i["age"])
                self.thisOperatorInfo = i
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

            self.badAuthorizationWindow()
            self.authorizationUI.pushButton_3.clicked.connect(self.createInstrWindow)
            self.authorizationUI.label_6.setText(name)
            self.authorizationUI.label_7.setText(f'{age} лет')
            if os.path.exists(f'operators/ID_{str(self.operatorId).zfill(6)}.jpg'):
                self.authorizationUI.label_16.setPixmap(QPixmap(f'operators/ID_{str(self.operatorId).zfill(6)}.jpg'))

            if self.cap is None or not self.cap.isOpened():
                self.cap = cv2.VideoCapture(0)
                if not self.cap.isOpened():
                    print("Ошибка в камере")
                    return False

                self.frameFace = None
                self.frameFaceEncs = None

                if not self.cameraLogRegTimer.isActive():
                    self.cameraLogRegTimer.start(20)

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


    def createInstrWindow(self):
        if not (self.logined and self.foundId):
            return
        self.windowId = 5
        self.instr = QtWidgets.QMainWindow()
        self.instrUI = instrClass()
        self.instrUI.setupUi(self.instr)
        self.instr.setWindowFlags(Qt.FramelessWindowHint)
        self.instr.show()
        if self.after == 0:
            self.registration.close()
        else:
            self.authorization.close()
        try: self.upr.close()
        except: pass
        try: self.analiz.close()
        except: pass
        try:
            self.instrUI.label_12.setText(str(self.thisOperatorInfo['last_name']) + ' ' + str(self.thisOperatorInfo['first_name']))
        except: pass
        self.instrUI.pushButton_3.clicked.connect(self.createInstrWindow)
        self.instrUI.pushButton_4.clicked.connect(self.createAnalizWindow)
        self.instrUI.pushButton_5.clicked.connect(self.createUprWindow)

        self.instrUI.pushButton_2.clicked.connect(self.createAnalizWindow)
        self.instrUI.close.mouseReleaseEvent = self.finishProgram
        self.instrUI.widget.mousePressEvent = lambda event: self.pressTopWindow(event, self.instr)
        self.instrUI.widget.mouseMoveEvent = lambda event: self.moveTopWindow(event, self.instr)
        self.instrUI.widget.releaseMouse = lambda event: self.releaseTopWindow(event, self.instr)


    def createAnalizWindow(self):
        self.windowId = 6
        self.analiz = QtWidgets.QMainWindow()
        if self.after == 0:
            self.analizUI = analizRegClass()
        else:
            self.analizUI = analizAuthClass()
        self.analizUI.setupUi(self.analiz)
        self.analiz.setWindowFlags(Qt.FramelessWindowHint)
        self.analiz.show()

        try: self.upr.close()
        except: pass
        try: self.instr.close()
        except: pass
        try:
            self.analizUI.label_12.setText(str(self.thisOperatorInfo['last_name']) + ' ' + str(self.thisOperatorInfo['first_name']))
        except: pass
        self.analizUI.pushButton_2.setStyleSheet("background-color: rgb(200,200,200); color: black; border-radius: 5px; border: 2px solid black")
        self.analizUI.pushButton_2.clicked.connect(self.createUprWindow)
        self.analizUI.pushButton_3.clicked.connect(self.createInstrWindow)
        self.analizUI.pushButton_4.clicked.connect(self.createAnalizWindow)
        self.analizUI.pushButton_5.clicked.connect(self.createUprWindow)
        if self.after == 0:
            self.analizUI.pushButton_6.clicked.connect(self.regOperatorPulse)

        self.analizUI.close.mouseReleaseEvent = self.finishProgram
        self.analizUI.widget.mousePressEvent = lambda event: self.pressTopWindow(event, self.analiz)
        self.analizUI.widget.mouseMoveEvent = lambda event: self.moveTopWindow(event, self.analiz)
        self.analizUI.widget.releaseMouse = lambda event: self.releaseTopWindow(event, self.analiz)
        self.analizUI.label_16.close()


    def createUprWindow(self):
        if self.fullMode == False:
            return
        self.after = 1
        self.windowId = 7
        self.upr = QtWidgets.QMainWindow()
        self.uprUI = uprClass()
        self.uprUI.setupUi(self.upr)
        self.upr.setWindowFlags(Qt.FramelessWindowHint)
        self.upr.show()
        try: self.instr.close()
        except: pass
        try: self.analiz.close()
        except: pass
        try:
            self.uprUI.label_12.setText(f"{self.thisOperatorInfo['last_name']} {self.thisOperatorInfo['first_name']}")
        except: pass
        self.uprUI.pushButton_3.clicked.connect(self.createInstrWindow)
        self.uprUI.pushButton_4.clicked.connect(self.createAnalizWindow)
        self.uprUI.pushButton_5.clicked.connect(self.createUprWindow)

        self.uprUI.close.mouseReleaseEvent = self.finishProgram
        self.uprUI.widget.mousePressEvent = lambda event: self.pressTopWindow(event, self.upr)
        self.uprUI.widget.mouseMoveEvent = lambda event: self.moveTopWindow(event, self.upr)
        self.uprUI.widget.releaseMouse = lambda event: self.releaseTopWindow(event, self.upr)

        self.greenIndicator()
        self.backgroundVideoUprTimer.start(5)
        if self.cap is None or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                print("Ошибка в камере")
                return

            if not self.cameraSleepTimer.isActive():
                self.cameraSleepTimer.start(20)

    def redIndicator(self):
        if not pygame.mixer.music.get_busy():
            pygame.mixer.music.load('./photos/redSound.mp3')
            pygame.mixer.music.play()
        self.stateOperator = 2
        self.uprUI.label_13.setText('Состояние оператора выходит за пределы')
        self.uprUI.label_22.setText(f'Пульс {self.pulse}')
        self.uprUI.label_15.setText('Запуск звукового оповещения!')
        self.uprUI.label_21.setText('')
        self.uprUI.label_18.setText('КРИТИЧНО!')
        self.uprUI.label_18.setStyleSheet('color: rgb(200,0,0)')
        self.uprUI.label_20.setStyleSheet('background-color: rgba(200,200,200,0); color: rgb(200,0,0)')
        self.uprUI.close_2.setPixmap(QPixmap.fromImage(QImage('./photos/greenGray.png')))
        self.uprUI.close_5.setPixmap(QPixmap.fromImage(QImage('./photos/yellowGray.png')))
        self.uprUI.close_6.setPixmap(QPixmap.fromImage(QImage('./photos/red.png')))

    def yellowIndicator(self):
        if not pygame.mixer.music.get_busy():
            pygame.mixer.music.load('./photos/yellowSound.mp3')
            pygame.mixer.music.play()
        self.stateOperator = 1
        self.uprUI.label_13.setText('Состояние оператора выходит за пределы')
        self.uprUI.label_22.setText('ВНИМАНИЕ!')
        self.uprUI.label_15.setText(f'Пульс {self.pulse}')
        self.uprUI.label_21.setText('Запуск звукового оповещения "ВНИМАНИЕ"')
        self.uprUI.label_18.setText('ВНИМАНИЕ')
        self.uprUI.label_18.setStyleSheet('color: rgb(200,200,0)')
        self.uprUI.label_20.setStyleSheet('background-color: rgba(200,200,200,0); color: rgb(200,200,0)')
        self.uprUI.close_2.setPixmap(QPixmap.fromImage(QImage('./photos/greenGray.png')))
        self.uprUI.close_5.setPixmap(QPixmap.fromImage(QImage('./photos/yellow.png')))
        self.uprUI.close_6.setPixmap(QPixmap.fromImage(QImage('./photos/redGray.png')))

    def greenIndicator(self):
        self.stateOperator = 0
        self.uprUI.label_13.setText('Состояние нормальное')
        self.uprUI.label_22.setText(f'Пульс {self.pulse}')
        self.uprUI.label_15.setText('')
        self.uprUI.label_21.setText('')
        self.uprUI.label_18.setText('НОРМА')
        self.uprUI.label_18.setStyleSheet('color: rgb(0,150,0)')
        self.uprUI.label_20.setStyleSheet('background-color: rgba(200,200,200,0); color: rgb(0,150,0)')
        self.uprUI.close_2.setPixmap(QPixmap.fromImage(QImage('./photos/green.png')))
        self.uprUI.close_5.setPixmap(QPixmap.fromImage(QImage('./photos/yellowGray.png')))
        self.uprUI.close_6.setPixmap(QPixmap.fromImage(QImage('./photos/redGray.png')))


app = QtWidgets.QApplication([])
pr = Program()
app.exec()