import os, math, sys 
import datetime, time
import pygame, pandas

from PyQt5.QtCore import QTimer, QPoint, Qt
from PyQt5.QtWidgets import QMainWindow, QWidget, QApplication
from PyQt5.QtGui import QImage, QPixmap


from setid import Ui_MainWindow as setidClass
from upr import Ui_MainWindow as uprClass

import serverRecver


class Program(): # main функция GUI программы
    def __init__(self): # запуск программы - иницилизация всех переменных и запуск первого окна
        self.pos = None
        self.windowID = 0

        self.found = False

        self.operatorID = 0
        self.operatorInfo = {}

        self.timeUpdateTimer = QTimer()
        self.timeUpdateTimer.timeout.connect(self.updateTime)
        self.timeUpdateTimer.start(1000)

        self.updateServerRecverTimer = QTimer()
        self.updateServerRecverTimer.timeout.connect(self.updateServerRecver)
        self.updateServerRecverTimer.start(250)

        self.createSetidWindow()


    def __del__(self): # закрытие программы - прерывание активности сокета и "уничтожение" запущенной программы
        serverRecver.shutdownSocket()
        sys.exit(0)
    def finishProgram(self): # функция, по названию которой вызывается деструктор
        self.__del__()
    def finishIdent(self): # закрытие только лишь диалогового окна
        try:
            self.ident.close()
        except:
            pass
        if self.windowID == 4:
            self.startAuthOperator()
    def mousePress(self, event): # начало клика - готовность к передвижению окна
        self.pos = event.globalPos()
    def mouseMove(self, event, window): # движение мыши - движение окна
        window.move(window.pos() + (QPoint(event.globalPos() - QPoint(self.pos))))
        self.pos = event.globalPos()
    def mouseRelease(self): # конец клика - завершение передвижения окна
        self.pos = None
    def createTemplateWindow(self, window, windowUI): # шаблон для создания форм (окон)
        window.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        windowUI.label.mouseReleaseEvent = lambda event: self.finishProgram()
        windowUI.widget.mousePressEvent = lambda event: self.mousePress(event)
        windowUI.widget.mouseMoveEvent = lambda event: self.mouseMove(event, window)
        windowUI.widget.mouseReleaseEvent = lambda event: self.mouseRelease()
        window.show()


    def initDB(self): # инициализация базы данных в текстовом формате operators_db.csv
        try:
            data = None
            if not os.path.exists('./operators_db.csv'):
                data = pandas.DataFrame(columns=[
                    'id', 'last_name', 'first_name', 'middle_name', 'age', 'date', 'time', 'software_start_time', 'drive_duration', 'pulse_threshold_critical', 'pulse_normal', 'current_pulse', 'operator_status'
                ])
                data.to_csv('./operators_db.csv', index=False)
                return data
            data = pandas.read_csv('./operators_db.csv')
            return data
        except:
            data = pandas.DataFrame(columns=[
                'id', 'last_name', 'first_name', 'middle_name', 'age', 'date', 'time', 'software_start_time', 'drive_duration', 'pulse_threshold_critical', 'pulse_normal', 'current_pulse', 'operator_status'
            ])
            data.to_csv('./operators_db.csv', index=False)
            return data


    def updateTime(self):
        # вызов функции по PyQt Timer происходит каждую секунду
        # обновляется содержимое базы данных и окон
        
        data = self.initDB()
        
        self.found = False
        operatorIndex = 0
        for i in data.to_dict('records'):
            if self.operatorID == int(i['id']):
                self.operatorInfo = i
                self.found = True
                break
            operatorIndex += 1

        if self.windowID == 2:
            self.uprUI.label_26.setPixmap(QPixmap(f'./operators/ID_{str(self.operatorID).zfill(6)}.jpg'))
            self.uprUI.label_24.setText(f"{self.operatorInfo['last_name']} {self.operatorInfo['first_name']} {self.operatorInfo['middle_name']}")
            self.uprUI.label_25.setText(f"{self.operatorInfo['age']} лет")
            self.uprUI.label_30.setText(f'{self.operatorInfo["current_pulse"]}')

            self.uprUI.label_20.setText(f"{datetime.datetime.strptime(self.operatorInfo['date'], '%d-%m-%Y').strftime('%d.%m.%Y')} / {datetime.datetime.strptime(self.operatorInfo['time'], '%H:%M:%S').strftime('%H:%M:%S')}")
            self.uprUI.label_21.setText(f"{datetime.datetime.strptime(self.operatorInfo['software_start_time'], '%H:%M:%S').strftime('%H:%M:%S')}")
            driveDuration = datetime.datetime.strptime(self.operatorInfo['drive_duration'], '%H:%M:%S')
            self.uprUI.label_22.setText(f"{driveDuration.strftime('%H:%M:%S')}")
            driveDurationDelta = datetime.timedelta(hours=driveDuration.hour, minutes=driveDuration.minute, seconds=driveDuration.second)
            leftDriveDurationDelta = datetime.timedelta(seconds=(32400-driveDurationDelta.seconds))
            self.uprUI.label_23.setText(f"{datetime.datetime.strptime(str(leftDriveDurationDelta), '%H:%M:%S').strftime('%H:%M:%S')}")

            if self.operatorInfo['operator_status'] == 'NORMAL':
                self.uprUI.label_28.setText('НОРМА')
                self.uprUI.label_28.setStyleSheet('color: rgb(0,200,0)')
                self.uprUI.label_30.setStyleSheet('color: rgb(0,200,0); background-color: rgba(0,0,0,0)')
                self.uprUI.label_7.setPixmap(QPixmap('./files/Blue_ellipse.png'))
                self.uprUI.label_8.setPixmap(QPixmap('./files/Trinangel.png'))
                self.uprUI.label_9.setPixmap(QPixmap('./files/Rectangle.png'))
                self.uprUI.label_11.setText('Состояние нормальное')
                self.uprUI.label_12.setText('')
                self.uprUI.label_13.setText('')
            elif self.operatorInfo['operator_status'] == 'WARNING':
                self.uprUI.label_28.setText('ВНИМАНИЕ')
                self.uprUI.label_28.setStyleSheet('color: rgb(200,200,0)')
                self.uprUI.label_30.setStyleSheet('color: rgb(200,200,0); background-color: rgba(0,0,0,0)')
                self.uprUI.label_7.setPixmap(QPixmap('./files/Ellipse.png'))
                self.uprUI.label_8.setPixmap(QPixmap('./files/Yellow_Trinagel.png'))
                self.uprUI.label_9.setPixmap(QPixmap('./files/Rectangle.png'))
                self.uprUI.label_11.setText('Состояние внимание !')
                self.uprUI.label_12.setText('Запуск звукового оповещения!')
                self.uprUI.label_13.setText('Необходимо связаться с водителем!')
            else:
                self.uprUI.label_28.setText('КРИТИЧНО!')
                self.uprUI.label_28.setStyleSheet('color: rgb(200,0,0)')
                self.uprUI.label_30.setStyleSheet('color: rgb(200,0,0); background-color: rgba(0,0,0,0)')
                self.uprUI.label_7.setPixmap(QPixmap('./files/Ellipse.png'))
                self.uprUI.label_8.setPixmap(QPixmap('./files/Trinangel.png'))
                self.uprUI.label_9.setPixmap(QPixmap('./files/Red_Rectangle.png'))
                self.uprUI.label_11.setText('Состояние критичное !')
                self.uprUI.label_12.setText('Запуск звукового оповещения!')
                self.uprUI.label_13.setText('Необходимо связаться с водителем!')


    def updateServerRecver(self): # постоянный вызов для получения с клиента информации
        try:
            serverRecver.main()
        except:
            pass


    def createSetidWindow(self): # создание формы для введения айди оператора
        self.windowID = 1
        self.setid = QMainWindow()
        self.setidUI = setidClass()
        self.setidUI.setupUi(self.setid)

        self.createTemplateWindow(self.setid, self.setidUI)
        try:
            self.upr.close()
        except:
            pass
        self.setidUI.pushButton_3.clicked.connect(self.createUprWindow)


    def createUprWindow(self): # главная форма, отображение информации о операторе по айди
        if not self.setidUI.plainTextEdit_3.toPlainText().isdigit():
            return
        self.operatorID = int(self.setidUI.plainTextEdit_3.toPlainText())
        data = self.initDB()
        self.found = False
        for i in data.to_dict('records'):
            if self.operatorID == int(i['id']):
                self.found = True
                break

        if not self.found:
            return
        self.found = False

        self.windowID = 2
        self.upr = QMainWindow()
        self.uprUI = uprClass()
        self.uprUI.setupUi(self.upr)

        self.createTemplateWindow(self.upr, self.uprUI)
        try:
            self.setid.close()
        except:
            pass
        self.uprUI.pushButton_2.clicked.connect(self.createSetidWindow)


app = QApplication([])
pr = Program()
app.exec() # запуск
