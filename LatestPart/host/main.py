from pandas import pandas as pd
import sys

from datetime import datetime, timedelta
import os

from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5 import Qt
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPixmap, QImage, QMouseEvent

from distantFirst import Ui_MainWindow as distantFirstClass
from distantInf import Ui_MainWindow as distantInfClass

import socketHost

class Program():
    def __init__(self):
        self.windowId = 0
        self.old_pos = None

        self.thisOperatorInfo = None
        self.operatorId = -1
        self.foundId = False

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.updateTime)
        self.timer.start(1000)

        self.hostTimer = QtCore.QTimer()
        self.hostTimer.timeout.connect(self.hostRecFiles)
        self.hostTimer.start(3000)

        self.createDistantFirstWindow()
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
    def finishProgram(self, event):
        self.__del__()


    def updateTime(self): # постоянное обновление времени
        file = self.initOperatorsDB()
        for i in file.to_dict("records"):
            if self.operatorId == i["id"]:
                self.thisOperatorInfo = i
                self.foundId = True
                break

        if self.foundId:
            self.distantInfUI.label_6.setText(f"{self.thisOperatorInfo['last_name']} {self.thisOperatorInfo['first_name']} {self.thisOperatorInfo['middle_name']}")
            self.distantInfUI.label_9.setText(f"{self.thisOperatorInfo['age']} лет")
            self.distantInfUI.label_18.setText(f"{self.thisOperatorInfo['date']} / {self.thisOperatorInfo['time']}")
            self.distantInfUI.label_19.setText(f"{self.thisOperatorInfo['software_start_time']}")
            self.distantInfUI.label_20.setText(f"{self.thisOperatorInfo['drive_duration']}")

            driveTemp = str(self.thisOperatorInfo['drive_duration'])
            driveDateTimeTemp = datetime.strptime(driveTemp, '%H:%M:%S')
            driveOstTemp = timedelta(hours=9, minutes=0, seconds=0) - timedelta(hours=driveDateTimeTemp.hour, minutes=driveDateTimeTemp.minute, seconds=driveDateTimeTemp.second)
            self.distantInfUI.label_21.setText(f"{datetime.strptime(str(driveOstTemp), '%H:%M:%S').strftime('%H:%M:%S')}")

            if os.path.exists(f'operators/ID_{str(self.operatorId).zfill(6)}.jpg'):
                self.distantInfUI.close_4.setPixmap(QPixmap(f'operators/ID_{str(self.operatorId).zfill(6)}.jpg'))
            self.distantInfUI.label_25.setText(f"{int(self.thisOperatorInfo['current_pulse'])}")

            if str(self.thisOperatorInfo['operator_status']) == 'CRITICAL':
                self.distantInfUI.label_23.setText('КРИТИЧНО!')
                self.distantInfUI.label_23.setStyleSheet('background-color: rgba(200,200,200,0); color: rgb(200,0,0)')
                self.distantInfUI.label_25.setStyleSheet('background-color: rgba(200,200,200,0); color: rgb(200,0,0)')
                self.distantInfUI.label_26.setText('Состояние критично')
                self.distantInfUI.label_27.setText('Запуск звукового оповещения!')
                self.distantInfUI.label_28.setText('Необходимо связаться с водителем!')
                self.distantInfUI.close_2.setPixmap(QPixmap.fromImage(QImage('./photos/greenGray.png')))
                self.distantInfUI.close_5.setPixmap(QPixmap.fromImage(QImage('./photos/yellowGray.png')))
                self.distantInfUI.close_6.setPixmap(QPixmap.fromImage(QImage('./photos/red.png')))
            elif str(self.thisOperatorInfo['operator_status']) == 'WARNING':
                self.distantInfUI.label_23.setText('ВНИМАНИЕ')
                self.distantInfUI.label_23.setStyleSheet('background-color: rgba(200,200,200,0); color: rgb(200,200,0)')
                self.distantInfUI.label_25.setStyleSheet('background-color: rgba(200,200,200,0); color: rgb(200,200,0)')
                self.distantInfUI.label_26.setText('Состояние внимание')
                self.distantInfUI.label_27.setText('Запуск звукового оповещения!')
                self.distantInfUI.label_28.setText('Необходимо связаться с водителем!')
                self.distantInfUI.close_2.setPixmap(QPixmap.fromImage(QImage('./photos/greenGray.png')))
                self.distantInfUI.close_5.setPixmap(QPixmap.fromImage(QImage('./photos/yellow.png')))
                self.distantInfUI.close_6.setPixmap(QPixmap.fromImage(QImage('./photos/redGray.png')))
            else:
                self.distantInfUI.label_23.setText('НОРМА')
                self.distantInfUI.label_23.setStyleSheet('background-color: rgba(200,200,200,0); color: rgb(0,150,0)')
                self.distantInfUI.label_25.setStyleSheet('background-color: rgba(200,200,200,0); color: rgb(0,150,0)')
                self.distantInfUI.label_26.setText('Состояние НОРМА')
                self.distantInfUI.label_27.setText('')
                self.distantInfUI.label_28.setText('')
                self.distantInfUI.close_2.setPixmap(QPixmap.fromImage(QImage('./photos/green.png')))
                self.distantInfUI.close_5.setPixmap(QPixmap.fromImage(QImage('./photos/yellowGray.png')))
                self.distantInfUI.close_6.setPixmap(QPixmap.fromImage(QImage('./photos/redGray.png')))


    def hostRecFiles(self):
        socketHost.main()


    def initOperatorsDB(self):  # инициализировать базу данных
        file = pd.DataFrame()
        if not os.path.exists('operators_db.csv'):
            file = pd.DataFrame(
                columns=["id", "last_name", "first_name", "middle_name", "age", "date", "time",
                         "software_start_time",
                         "drive_duration", 'pulse_threshold_critical', 'pulse_normal', 'current_pulse',
                         'operator_status'])
            file.to_csv('operators_db.csv', index=False)
        else:
            file = pd.read_csv('operators_db.csv')
        return file


    def createDistantFirstWindow(self):
        try:
            self.distantInf.close()
        except: pass
        self.windowId = 1
        self.distantFirst = QtWidgets.QMainWindow()
        self.distantFirstUI = distantFirstClass()
        self.distantFirstUI.setupUi(self.distantFirst)
        self.distantFirst.setWindowFlags(Qt.FramelessWindowHint)
        self.distantFirst.show()
        self.distantFirstUI.pushButton_3.clicked.connect(self.createDistantInfWindow)

        self.distantFirstUI.close.mouseReleaseEvent = self.finishProgram
        self.distantFirstUI.widget.mousePressEvent = lambda event: self.pressTopWindow(event, self.distantFirst)
        self.distantFirstUI.widget.mouseMoveEvent = lambda event: self.moveTopWindow(event, self.distantFirst)
        self.distantFirstUI.widget.releaseMouse = lambda event: self.releaseTopWindow(event, self.distantFirst)


    def createDistantInfWindow(self):
        file = self.initOperatorsDB()
        operatorIdTemp = self.distantFirstUI.textEdit.toPlainText()
        if operatorIdTemp == '': return
        for i in file.to_dict("records"):
            if int(operatorIdTemp) == i["id"]:
                self.operatorId = int(operatorIdTemp)
                self.thisOperatorInfo = i
                break

        if self.operatorId == -1:
            return

        try:
            self.distantFirst.close()
        except: pass
        self.windowId = 2
        self.distantInf = QtWidgets.QMainWindow()
        self.distantInfUI = distantInfClass()
        self.distantInfUI.setupUi(self.distantInf)
        self.distantInf.setWindowFlags(Qt.FramelessWindowHint)
        self.distantInf.show()

        self.distantInfUI.close.mouseReleaseEvent = self.finishProgram
        self.distantInfUI.widget.mousePressEvent = lambda event: self.pressTopWindow(event, self.distantInf)
        self.distantInfUI.widget.mouseMoveEvent = lambda event: self.moveTopWindow(event, self.distantInf)
        self.distantInfUI.widget.releaseMouse = lambda event: self.releaseTopWindow(event, self.distantInf)

        self.distantInfUI.pushButton_2.clicked.connect(self.__init__)
        self.distantInfUI.label_6.setText(f"{self.thisOperatorInfo['last_name']} {self.thisOperatorInfo['first_name']} {self.thisOperatorInfo['middle_name']}")
        self.distantInfUI.label_9.setText(f"{self.thisOperatorInfo['age']} лет")
        self.distantInfUI.label_18.setText(f"{self.thisOperatorInfo['date']} / {self.thisOperatorInfo['time']}")
        self.distantInfUI.label_19.setText(f"{self.thisOperatorInfo['software_start_time']}")
        self.distantInfUI.label_20.setText(f"{self.thisOperatorInfo['drive_duration']}")
        if os.path.exists(f'operators/ID_{str(self.operatorId).zfill(6)}.jpg'):
            self.distantInfUI.close_4.setPixmap(QPixmap(f'operators/ID_{str(self.operatorId).zfill(6)}.jpg'))


app = QtWidgets.QApplication([])
pr = Program()
app.exec()