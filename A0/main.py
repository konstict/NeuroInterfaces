from pandas import pandas as pd
import sys

import cv2
import face_recognition

from datetime import datetime
import os

from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5 import Qt
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPixmap, QImage, QMouseEvent

from first import Ui_MainWindow as firstClass
from reg import Ui_MainWindow as registrationClass
from choose import Ui_MainWindow as inputIdClass
from auth import Ui_MainWindow as authorizationClass

from instruction import Ui_MainWindow as instructionClass
from analizReg import Ui_MainWindow as analizRegClass
from analizAuth import Ui_MainWindow as analizAuthClass

class Program():
    def __init__(self):
        self.windowId = 0
        self.operatorId = -1
        self.operatorName = []
        self.old_pos = None
        self.logined = False
        self.foundId = False
        self.afterRegOrAuth = 0 # 0 - reg, 1 - auth

        self.timeStart = datetime.now()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.updateTime)
        self.timer.start(1000)

        self.cameraTimer = QtCore.QTimer()
        self.cap = None

        self.createFirstWindow()

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
    def __del__(self):
        print('finish')
        sys.exit(0)


    def updateTime(self): # постоянное обновление времени
        self.timeNow = datetime.now()
        if self.windowId == 4:
            self.authorizationUI.label_18.setText(self.timeNow.strftime(f'{self.timeNow.strftime("%d.%m.%Y")} / {self.timeNow.strftime("%H.%M.%S")}'))
            self.authorizationUI.label_19.setText(self.timeStart.strftime("%H.%M.%S"))

        file = self.initOperatorsDB()
        operatorIndex = -1
        self.foundId = False
        for i in file.to_dict('records'):
            operatorIndex += 1
            if i['id'] == self.operatorId:
                self.operatorName = [i['last_name'], i['first_name'], i['middle_name']]
                file.loc[operatorIndex,'software_start_time'] = self.timeStart.strftime("%H:%M:%S")
                file.loc[operatorIndex,'date'] = self.timeNow.strftime("%d-%m-%Y")
                file.loc[operatorIndex,'time'] = self.timeNow.strftime("%H:%M:%S")
                file.to_csv('operators_db.csv', index=False)
                self.foundId = True

        if self.foundId and self.logined:
            if self.windowId == 4:
                self.goodAuthorizationWindow()
            elif self.windowId == 2:
                self.goodRegistrationWindow()
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
        self.firstUI.widget.mousePressEvent = lambda event: self.pressTopWindow(event, self.first)
        self.firstUI.widget.mouseMoveEvent = lambda event: self.moveTopWindow(event, self.first)
        self.firstUI.widget.releaseMouse = lambda event: self.releaseTopWindow(event, self.first)


    def createRegistrationWindow(self): # регистрация
        self.windowId = 2
        self.afterRegOrAuth = 0
        self.registration = QtWidgets.QMainWindow()
        self.registrationUI = registrationClass()
        self.registrationUI.setupUi(self.registration)
        self.registration.setWindowFlags(Qt.FramelessWindowHint)
        self.registration.show()
        self.first.close()
        self.badRegistrationWindow()
        self.registrationUI.pushButton.clicked.connect(self.regOperator)
        self.registrationUI.pushButton_2.clicked.connect(self.createInstructionWindow)

        self.registrationUI.close.mouseReleaseEvent = self.finishProgram
        self.registrationUI.widget.mousePressEvent = lambda event: self.pressTopWindow(event, self.registration)
        self.registrationUI.widget.mouseMoveEvent = lambda event: self.moveTopWindow(event, self.registration)
        self.registrationUI.widget.releaseMouse = lambda event: self.releaseTopWindow(event, self.registration)


    def badRegistrationWindow(self): # id не присвоен регистрация
        self.registrationUI.label_10.setText("Оператор не определен")
        self.registrationUI.close_3.setPixmap(QPixmap("photos/nook.png"))
        self.registrationUI.widget_12.setStyleSheet("background-color: rgb(200,0,0)")
        self.registrationUI.label_13.close()
        self.registrationUI.label_12.setText("ID не присвоен")
        self.registrationUI.pushButton_2.setStyleSheet("color: white; border: 1px solid black; border-radius: 5px")


    def goodRegistrationWindow(self): # id присвоен регистрация
        self.registrationUI.label_10.setText("Оператор определен")
        self.registrationUI.label_12.setText("ID")
        self.registrationUI.label_13.setText(f"{str(self.operatorId).zfill(6)}")
        self.registrationUI.close_3.setPixmap(QPixmap("photos/ok.png"))
        self.registrationUI.widget_12.setStyleSheet("background-color: rgb(0,200,0)")
        self.registrationUI.label_13.show()
        self.registrationUI.pushButton_2.setStyleSheet("background-color: black; color: white; border-radius: 5px")


    def createInstructionWindow(self):
        if self.logined and self.foundId:
            self.windowId = 5
            self.instruction = QtWidgets.QMainWindow()
            self.instructionUI = instructionClass()
            self.instructionUI.setupUi(self.instruction)
            self.instruction.setWindowFlags(Qt.FramelessWindowHint)
            self.instruction.show()
            if self.afterRegOrAuth == 0:
                self.instructionUI.pushButton_3.clicked.connect(self.createAnalizRegWindow)
            else:
                self.instructionUI.pushButton_3.clicked.connect(self.createAnalizAuthWindow)

            self.instructionUI.close.mouseReleaseEvent = self.finishProgram
            self.instructionUI.top.mousePressEvent = lambda event: self.pressTopWindow(event, self.instruction)
            self.instructionUI.top.mouseMoveEvent = lambda event: self.moveTopWindow(event, self.instruction)
            self.instructionUI.top.releaseMouse = lambda event: self.releaseTopWindow(event, self.instruction)


    def createAnalizRegWindow(self):
        self.windowId = 6
        self.analizReg = QtWidgets.QMainWindow()
        self.analizRegUI = analizRegClass()
        self.analizRegUI.setupUi(self.analizReg)
        self.analizReg.setWindowFlags(Qt.FramelessWindowHint)
        self.analizReg.show()
        self.instruction.close()

        self.analizRegUI.close.mouseReleaseEvent = self.finishProgram
        self.analizRegUI.top.mousePressEvent = lambda event: self.pressTopWindow(event, self.analizReg)
        self.analizRegUI.top.mouseMoveEvent = lambda event: self.moveTopWindow(event, self.analizReg)
        self.analizRegUI.top.releaseMouse = lambda event: self.releaseTopWindow(event, self.analizReg)


    def createAnalizAuthWindow(self):
        self.windowId = 7
        self.analizAuth = QtWidgets.QMainWindow()
        self.analizAuthUI = analizAuthClass()
        self.analizAuthUI.setupUi(self.analizAuth)
        self.analizAuth.setWindowFlags(Qt.FramelessWindowHint)
        self.analizAuth.show()
        self.instruction.close()

        self.analizAuthUI.close.mouseReleaseEvent = self.finishProgram
        self.analizAuthUI.top.mousePressEvent = lambda event: self.pressTopWindow(event, self.analizAuth)
        self.analizAuthUI.top.mouseMoveEvent = lambda event: self.moveTopWindow(event, self.analizAuth)
        self.analizAuthUI.top.releaseMouse = lambda event: self.releaseTopWindow(event, self.analizAuth)


    def initOperatorsDB(self): # инициализировать базу данных
        file = pd.DataFrame()
        if not os.path.exists('operators_db.csv'):
            file = pd.DataFrame(
                columns=["id", "last_name", "first_name", "middle_name", "age", "date", "time", "software_start_time",
                         "drive_duration"])
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
                "date": self.timeNow.strftime("%d.%m.%Y"), "time": self.timeNow.strftime("%H.%M.%S"), "software_start_time": self.timeStart.strftime("%H.%M.%S"), "drive_duration": 0
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
                self.registrationUI.close_2.setPixmap(
                    QPixmap.fromImage(
                        QImage( cv2.cvtColor(cv2.resize(frameRectangle, dsize = (320, 200), interpolation = cv2.INTER_AREA), cv2.COLOR_BGR2RGB).data, 320, 200, QImage.Format_RGB888 )
                    )
                )
            elif self.windowId == 4: # при авторизации
                self.authorizationUI.close_2.setPixmap(
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
        self.inputIdUI.pushButton_2.clicked.connect(self.createAuthorizationWindow)
        self.first.close()

        self.inputIdUI.close.mouseReleaseEvent = self.finishProgram
        self.inputIdUI.widget.mousePressEvent = lambda event: self.pressTopWindow(event, self.inputId)
        self.inputIdUI.widget.mouseMoveEvent = lambda event: self.moveTopWindow(event, self.inputId)
        self.inputIdUI.widget.releaseMouse = lambda event: self.releaseTopWindow(event, self.inputId)


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
            self.windowId = 4
            self.afterRegOrAuth = 1
            self.authorization = QtWidgets.QMainWindow()
            self.authorizationUI = authorizationClass()
            self.authorizationUI.setupUi(self.authorization)
            self.authorization.setWindowFlags(Qt.FramelessWindowHint)
            self.authorization.show()
            self.inputId.close()
            self.authorizationUI.pushButton_2.clicked.connect(self.createInstructionWindow)

            self.authorizationUI.close.mouseReleaseEvent = self.finishProgram
            self.authorizationUI.widget.mousePressEvent = lambda event: self.pressTopWindow(event, self.authorization)
            self.authorizationUI.widget.mouseMoveEvent = lambda event: self.moveTopWindow(event, self.authorization)
            self.authorizationUI.widget.releaseMouse = lambda event: self.releaseTopWindow(event, self.authorization)

            self.badAuthorizationWindow()
            self.authorizationUI.label_6.setText(name)
            self.authorizationUI.label_9.setText(f'{age} лет')
            if os.path.exists(f'operators/ID_{str(self.operatorId).zfill(6)}.jpg'):
                self.authorizationUI.close_4.setPixmap(QPixmap(f'operators/ID_{str(self.operatorId).zfill(6)}.jpg'))

            if self.cap is None or not self.cap.isOpened():
                self.cameraStart()


    def badAuthorizationWindow(self): # id не присвоен авторизация
        self.authorizationUI.label_10.setText("Оператор не определен")
        self.authorizationUI.close_3.setPixmap(QPixmap("photos/nook.png"))
        self.authorizationUI.widget_12.setStyleSheet("background-color: rgb(200,0,0)")
        self.authorizationUI.label_13.close()
        self.authorizationUI.label_12.setText("ID не присвоен")
        self.authorizationUI.pushButton_2.setStyleSheet("color: white; border: 1px solid black; border-radius: 5px")


    def goodAuthorizationWindow(self): # id присвоен авторизация
        self.authorizationUI.label_10.setText("Оператор определен")
        self.authorizationUI.label_12.setText("ID")
        self.authorizationUI.label_13.setText(f"{str(self.operatorId).zfill(6)}")
        self.authorizationUI.close_3.setPixmap(QPixmap("photos/ok.png"))
        self.authorizationUI.widget_12.setStyleSheet("background-color: rgb(0,200,0)")
        self.authorizationUI.label_13.show()
        self.authorizationUI.pushButton_2.setStyleSheet("background-color: black; color: white; border-radius: 5px")


app = QtWidgets.QApplication([])
pr = Program()
app.exec()