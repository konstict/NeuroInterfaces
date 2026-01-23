import os, math, sys 
import datetime, time
import pygame, pandas

import cv2, face_recognition
from mediapipe.python.solutions import face_mesh

import serial
from serial.tools import list_ports
from collections import deque

from PyQt5.QtCore import QTimer, QPoint, Qt
from PyQt5.QtWidgets import QMainWindow, QWidget, QApplication
from PyQt5.QtGui import QImage, QPixmap


from firstw import Ui_MainWindow as firstClass
from reg import Ui_MainWindow as regClass
from setid import Ui_MainWindow as setidClass
from auth import Ui_MainWindow as authClass
from ident import Ui_MainWindow as identClass

from instr import Ui_MainWindow as instrClass
from analizAuth import Ui_MainWindow as analizAuthClass
from analizReg import Ui_MainWindow as analizRegClass

from upr import Ui_MainWindow as uprClass

import clientSender


class Program(): # main функция GUI программы
    def __init__(self): # запуск программы - иницилизация всех переменных и запуск первого окна
        self.pos = None
        self.windowID = 0

        self.after = 0 # 0 - регистрация; 1 - авторизация
        self.logined = False
        self.found = False
        self.fullMode = False

        self.operatorFace = None
        self.operatorFaceEnc = None
        self.operatorID = 0
        self.operatorInfo = {}
        self.operatorState = 0
        self.pulse = 0
        self.pulseDeque = deque(maxlen=10)

        self.timeNow = datetime.datetime.now()
        self.timeStart = datetime.datetime.now()
        self.driveDuration = datetime.timedelta()

        self.timeUpdateTimer = QTimer()
        self.timeUpdateTimer.timeout.connect(self.updateTime)
        self.timeUpdateTimer.start(1000)

        self.cap = None
        self.cameraUpdateTimer = QTimer()
        self.cameraUpdateTimer.timeout.connect(self.updateCamera)

        self.com = None
        self.pulseUpdateTimer = QTimer()
        self.pulseUpdateTimer.timeout.connect(self.updatePulse)

        self.video = None
        self.videoUpdateTimer = QTimer()
        self.videoUpdateTimer.timeout.connect(self.videoUpdate)
        
        self.cap = None
        self.cameraUprUpdateTimer = QTimer()
        self.cameraUprUpdateTimer.timeout.connect(self.updateCameraUpr)

        self.faceMesh = face_mesh.FaceMesh(
            max_num_faces=1,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6,
            static_image_mode=False
        )
        self.leftEye = [362, 386, 385, 263, 374, 373] # айди для работы с сеткой лица (левый глаз)
        self.rightEye = [33, 159, 158, 133, 145, 153] # правый глаз
        self.other = [1, 152] # 1 - нос, 152 - подбородок
        self.latestCameraUprTime = 0
        self.earTime = 0
        self.headTime = 0

        try:
            pygame.mixer.init()
        except:
            pass

        self.updateClientSenderTimer = QTimer()
        self.updateClientSenderTimer.timeout.connect(self.updateClientSender)
        self.updateClientSenderTimer.start(250)

        self.createFirstWindow()


    def __del__(self): # закрытие программы - прерывание активности сокета и "уничтожение" запущенной программы
        clientSender.sock.shutdown(0)
        clientSender.sock.close()
        clientSender.sock = None
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
        data = None
        if not os.path.exists('./operators_db.csv'):
            data = pandas.DataFrame(columns=[
                'id', 'last_name', 'first_name', 'middle_name', 'age', 'date', 'time', 'software_start_time', 'drive_duration', 'pulse_threshold_critical', 'pulse_normal', 'current_pulse', 'operator_status'
            ])
            data.to_csv('./operators_db.csv', index=False)
            return data
        data = pandas.read_csv('./operators_db.csv')
        return data


    def updateTime(self): 
        # вызов функции по PyQt Timer происходит каждую секунду
        # обновляется содержимое базы данных и окон
        data = self.initDB()
        self.timeNow = datetime.datetime.now()
        
        self.found = False
        operatorIndex = 0
        for i in data.to_dict('records'):
            if self.operatorID == int(i['id']):
                data.loc[operatorIndex, 'date'] = self.timeNow.strftime('%d-%m-%Y')
                data.loc[operatorIndex, 'time'] = self.timeNow.strftime('%H:%M:%S')
                data.loc[operatorIndex, 'software_start_time'] = self.timeStart.strftime('%H:%M:%S')
                data.loc[operatorIndex, 'current_pulse'] = self.pulse
                data.loc[operatorIndex, 'drive_duration'] = str(self.driveDuration)
                if self.operatorState == 0:
                    data.loc[operatorIndex, 'operator_status'] = 'NORMAL'
                elif self.operatorState == 1:
                    data.loc[operatorIndex, 'operator_status'] = 'WARNING'
                else:
                    data.loc[operatorIndex, 'operator_status'] = 'CRITICAL'

                data.to_csv('./operators_db.csv', index=False)
                self.operatorInfo = i
                self.found = True
                break
            operatorIndex += 1

        self.fullMode = self.pulse > 0 and self.operatorInfo['pulse_threshold_critical'] > 0 and self.operatorInfo['pulse_normal'] > 0
        if self.windowID == 2:
            if self.found and self.logined:
                self.regUI.label_12.setText('Оператор определен')
                self.regUI.label_14.setText('Для запуска программы нажмите "Далее"')
                self.regUI.label_16.setText(f'{str(self.operatorID).zfill(6)}')
                self.regUI.widget_10.setStyleSheet('background-color: rgb(0,200,0); color: black')
                self.regUI.pushButton_2.setStyleSheet('background-color: black; color: white; border-radius: 10px; border: 2px solid black')
                self.regUI.label_13.setPixmap(QPixmap('./files/Check Mark.png'))
            else:
                self.regUI.label_12.setText('Оператор не определен')
                self.regUI.label_14.setText('Запуск программы невозможен')
                self.regUI.label_16.setText('не присвоен')
                self.regUI.widget_10.setStyleSheet('background-color: rgb(200,0,0); color: black')
                self.regUI.pushButton_2.setStyleSheet('background-color: rgb(200,200,200); color: white; border-radius: 10px; border: 2px solid black')
                self.regUI.label_13.setPixmap(QPixmap('./files/Cancel.png'))   
        elif self.windowID == 4:
            self.authUI.label_26.setPixmap(QPixmap(f'./operators/ID_{str(self.operatorID).zfill(6)}.jpg'))
            self.authUI.label_24.setText(f"{self.operatorInfo['last_name']} {self.operatorInfo['first_name']} {self.operatorInfo['middle_name']}")
            self.authUI.label_25.setText(f"{self.operatorInfo['age']} лет")
            self.authUI.label_20.setText(f"{self.timeNow.strftime('%d.%m.%Y')} / {self.timeNow.strftime('%H:%M:%S')}")
            self.authUI.label_21.setText(f"{self.timeStart.strftime('%H:%M:%S')}")
            if self.found and self.logined:
                self.authUI.label_12.setText('Оператор определен')
                self.authUI.label_14.setText('Для запуска программы нажмите "Далее"')
                self.authUI.label_16.setText(f'{str(self.operatorID).zfill(6)}')
                self.authUI.widget_10.setStyleSheet('background-color: rgb(0,200,0); color: black')
                self.authUI.pushButton_2.setStyleSheet('background-color: black; color: white; border-radius: 10px; border: 2px solid black')
                self.authUI.label_13.setPixmap(QPixmap('./files/Check Mark.png'))
            else:
                self.authUI.label_12.setText('Оператор не определен')
                self.authUI.label_14.setText('Запуск программы невозможен')
                self.authUI.label_16.setText('не присвоен')
                self.authUI.widget_10.setStyleSheet('background-color: rgb(200,0,0); color: black')
                self.authUI.pushButton_2.setStyleSheet('background-color: rgb(200,200,200); color: white; border-radius: 10px; border: 2px solid black')
                self.authUI.label_13.setPixmap(QPixmap('./files/Cancel.png'))   
        elif self.windowID == 5:
            if not self.found or not self.logined:
                self.__init__()
                self.createIdentWindow()
                return

            self.instrUI.label_22.setText(f"{self.operatorInfo['last_name']} {self.operatorInfo['first_name']}")
        elif self.windowID == 6:
            if not self.found or not self.logined:
                self.__init__()
                self.createIdentWindow()
                return
                
            self.startPulseUpdate()
            if self.after == 0:
                self.analizUI.plainTextEdit.setPlaceholderText(str(f"{self.operatorInfo['pulse_threshold_critical']}"))
                self.analizUI.plainTextEdit_2.setPlaceholderText(str(f"{self.operatorInfo['pulse_normal']}"))
            self.analizUI.label_22.setText(f"{self.operatorInfo['last_name']} {self.operatorInfo['first_name']}")
            self.analizUI.label_11.setText(f'Пульс........................................................{self.pulse}')
            if self.after == 1:
                self.analizUI.label_18.setText(f"{self.operatorInfo['pulse_threshold_critical']}")
                self.analizUI.label_19.setText(f"{self.operatorInfo['pulse_normal']}")
            if self.pulseUpdateTimer.isActive():
                self.analizUI.label_7.setText('Проверка сигнала..............................ОК')
            else:
                self.analizUI.label_7.setText('Проверка сигнала..............................НЕ ОК')
            if self.pulse > 0:
                self.analizUI.label_10.setText('Проверка пульса................................ОК')
            else:
                self.analizUI.label_10.setText('Проверка пульса................................НЕ ОК')
            if self.fullMode:
                self.analizUI.label_12.setText('Для перехода в режим управления нажмите далее')
                self.analizUI.pushButton_2.setStyleSheet('background-color: black; color: white; border-radius: 10px; border: 2px solid black')
            else:
                self.analizUI.label_12.setText('')
                self.analizUI.pushButton_2.setStyleSheet('background-color: rgb(200,200,200); color: white; border-radius: 10px; border: 2px solid black')
        elif self.windowID == 7:
            if not self.found or not self.logined:
                self.__init__()
                self.createIdentWindow()
                return
            if not self.fullMode:
                self.cameraUprUpdateTimer.stop()
                self.videoUpdateTimer.stop()
                self.createAnalizWindow()
                return
            
            self.startVideoUpdate()
            self.startPulseUpdate()
            self.startCameraUprUpdate()
            
            self.driveDuration = datetime.timedelta(seconds=((self.driveDuration.seconds+1) % 86400))
            if self.driveDuration.seconds >= 32400:
                self.finishProgram()
            driveDurationLeftTimedelta = datetime.timedelta(seconds=(32400 - self.driveDuration.seconds))
            driveDurationLeftDatetime = datetime.datetime.strptime(str(driveDurationLeftTimedelta), '%H:%M:%S')
            self.uprUI.label_27.setText(f'{str(driveDurationLeftDatetime.hour).zfill(2)[0]}')
            self.uprUI.label_29.setText(f'{str(driveDurationLeftDatetime.hour).zfill(2)[1]}')
            self.uprUI.label_30.setText(f'{str(driveDurationLeftDatetime.minute).zfill(2)[0]}')
            self.uprUI.label_32.setText(f'{str(driveDurationLeftDatetime.minute).zfill(2)[1]}')

            self.uprUI.label_22.setText(f"{self.operatorInfo['last_name']} {self.operatorInfo['first_name']}")
            self.uprUI.label_17.setText(f"{self.timeNow.strftime('%d.%m.%Y')} / {self.timeNow.strftime('%H:%M:%S')}")
            self.uprUI.label_18.setText(f"{self.timeStart.strftime('%H:%M:%S')}")
            self.uprUI.label_38.setText(f"{self.pulse}")

            print(self.headTime, self.earTime)
            if self.pulse >= int(self.operatorInfo['pulse_threshold_critical']) or self.pulse <= 40 or (self.headTime >= 4 and self.earTime >= 3):
                self.operatorState = 2
            elif self.pulse >= int(self.operatorInfo['pulse_normal']) or self.pulse <= 50 or (self.headTime > 0 or self.earTime >= 3):
                self.operatorState = 1
            else:
                self.operatorState = 0
            # print(self.operatorState)

            if self.operatorState == 0:
                self.uprUI.label_19.setText('НОРМА')
                self.uprUI.label_19.setStyleSheet('color: rgb(0,200,0)')
                self.uprUI.label_38.setStyleSheet('color: rgb(0,200,0); background-color: rgba(0,0,0,0)')
                self.uprUI.label_34.setPixmap(QPixmap('./files/Blue_ellipse.png'))
                self.uprUI.label_35.setPixmap(QPixmap('./files/Trinangel.png'))
                self.uprUI.label_36.setPixmap(QPixmap('./files/Rectangle.png'))
                self.uprUI.label_7.setText('Состояние нормальное')
                self.uprUI.label_10.setText(f'Пульс {self.pulse}')
                self.uprUI.label_11.setText('')
                self.uprUI.label_12.setText('')
            elif self.operatorState == 1:
                try:
                    if not pygame.mixer.music.get_busy():
                        pygame.mixer.music.load('./files/yellowSound.mp3')
                        pygame.mixer.music.play()
                except:
                    pass
                self.uprUI.label_19.setText('ВНИМАНИЕ')
                self.uprUI.label_19.setStyleSheet('color: rgb(200,200,0)')
                self.uprUI.label_38.setStyleSheet('color: rgb(200,200,0); background-color: rgba(0,0,0,0)')
                self.uprUI.label_34.setPixmap(QPixmap('./files/Ellipse.png'))
                self.uprUI.label_35.setPixmap(QPixmap('./files/Yellow_Trinagel.png'))
                self.uprUI.label_36.setPixmap(QPixmap('./files/Rectangle.png'))
                self.uprUI.label_7.setText('Состояние оператора выходит за пределы')
                self.uprUI.label_10.setText('"ВНИМАНИЕ')
                self.uprUI.label_11.setText(f'Пульс {self.pulse}')
                self.uprUI.label_12.setText('Запуск звукового оповещения "ВНИМАНИЕ"')
            else:
                try:
                    if not pygame.mixer.music.get_busy():
                        pygame.mixer.music.load('./files/redSound.mp3')
                        pygame.mixer.music.play()
                except:
                    pass
                self.uprUI.label_19.setText('КРИТИЧНО!')
                self.uprUI.label_19.setStyleSheet('color: rgb(200,0,0)')
                self.uprUI.label_38.setStyleSheet('color: rgb(200,0,0); background-color: rgba(0,0,0,0)')
                self.uprUI.label_34.setPixmap(QPixmap('./files/Ellipse.png'))
                self.uprUI.label_35.setPixmap(QPixmap('./files/Trinangel.png'))
                self.uprUI.label_36.setPixmap(QPixmap('./files/Red_Rectangle.png'))
                self.uprUI.label_7.setText('Состояние критичное!')
                self.uprUI.label_10.setText(f'Пульс {self.pulse}')
                self.uprUI.label_11.setText('Запуск звукового оповещения!')
                self.uprUI.label_12.setText('')


    def updateClientSender(self): # постоянный вызов для отправки на сервер информации
        try:
            clientSender.main()
        except:
            pass


    def updateCamera(self): # обновление камеры и нахождения лица при авторизации или регистрации 
        ok, frame = self.cap.read()
        frameRect = frame.copy()
        if not ok:
            return
        
        locations = face_recognition.face_locations(frame)
        if len(locations) > 0:
            location = locations[0]
            for i in locations:
                if (location[1]-location[3])*(location[2]-location[0]) > (i[1]-i[3])*(i[2]-i[0]):
                    location = i

            self.operatorFace = frame[location[0]-25:location[2]+25, location[3]-25:location[1]+25]
            faceEncs = face_recognition.face_encodings(frame, [location])
            if len(faceEncs) > 0:
                self.operatorFaceEnc = faceEncs[0]
            else:
                return
            
            cv2.rectangle(frameRect, (location[3], location[0]), (location[1], location[2]), (255,255,255), 5)

            if self.windowID == 2:
                self.finishRegOperator()
            if self.windowID == 4:
                self.finishAuthOperator()

            self.cameraUpdateTimer.stop()
            self.cap.release()
            self.cap = None

        if self.windowID == 2:
            self.regUI.label_11.setPixmap(QPixmap.fromImage(
                QImage(cv2.cvtColor(cv2.resize(frameRect, (1920,1080), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB), 1920, 1080, QImage.Format.Format_RGB888)
            ))
        elif self.windowID == 4:
            self.authUI.label_11.setPixmap(QPixmap.fromImage(
                QImage(cv2.cvtColor(cv2.resize(frameRect, (1920,1080), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB), 1920, 1080, QImage.Format.Format_RGB888)
            ))
        

    def updatePulse(self): # обновление пульса (из платы Arduino)
        try:
            if self.com.in_waiting > 0:
                value = int(self.com.readline())

                self.pulseDeque.append(value)
                pulseSum = 0
                for i in self.pulseDeque:
                    pulseSum += i
                self.pulse = int(pulseSum / self.pulseDeque.maxlen)

                # print(self.pulse)
        except:
            self.pulseUpdateTimer.stop()
            self.pulse = 0
            return


    def updateCameraUpr(self): # обновление камеры в последней форме Управление
        ok, frame = self.cap.read()
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if not ok:
            return
        
        process = self.faceMesh.process(rgb).multi_face_landmarks
        if process is None or not len(process) > 0:
            self.headTime = 10
            self.earTime = 10
        else:
            landmarks = process[0].landmark
            
            # leftEye = {}
            # for i in face_mesh.FACEMESH_RIGHT_EYE:
            #     leftEye[i[0]] = landmarks[i[0]]
            #     leftEye[i[1]] = landmarks[i[1]]
            # print(sorted(leftEye.items(), key=lambda k: k[1].y, reverse=False)[0:2], sorted(leftEye.items(), key=lambda k: k[1].y, reverse=True)[0:2])
            # print(sorted(leftEye.items(), key=lambda k: k[1].x, reverse=False)[0], sorted(leftEye.items(), key=lambda k: k[1].x, reverse=True)[0])
            
            earValue = self.getEar(list(landmarks[i] for i in self.leftEye), list(landmarks[i] for i in self.rightEye))
            if earValue <= 0.35:
                self.earTime += time.time() - self.latestCameraUprTime
            else:
                self.earTime = 0
                
            earAvg = (landmarks[self.leftEye[0]].x + landmarks[self.rightEye[3]].x) /2 , (landmarks[self.leftEye[0]].y + landmarks[self.rightEye[3]].y) /2

            xValue = (
                math.sqrt((landmarks[self.other[1]].x - earAvg[0])**2 + (landmarks[self.other[1]].y - earAvg[1])**2) / 
                math.sqrt((landmarks[self.other[0]].x - landmarks[self.other[1]].x)**2 + (landmarks[self.other[0]].y - landmarks[self.other[1]].y)**2)
            )
            zValue = (
                ((landmarks[self.leftEye[0]].x - landmarks[self.rightEye[3]].x)**2) / 
                math.sqrt((landmarks[self.other[1]].x - earAvg[0])**2 + (landmarks[self.other[1]].y - earAvg[1])**2)
            )
            if xValue >= 3 or xValue <= 1.3 or zValue <= 0.01:
                self.headTime += time.time() - self.latestCameraUprTime
            else:
                self.headTime = 0
            # print(self.headTime)

            self.latestCameraUprTime = time.time()
        
        if self.windowID == 7:
            self.uprUI.label_13.setPixmap(QPixmap.fromImage(
                QImage(cv2.resize(rgb, (1920,1080), interpolation=cv2.INTER_AREA), 1920, 1080, QImage.Format.Format_RGB888)
            ))


    def videoUpdate(self): # обновление видеопотока с файла
        ok, frame = self.video.read()
        if not ok:
            self.videoUpdateTimer.stop()
            self.startVideoUpdate()
            return
        
        elif self.windowID == 7:
            self.uprUI.label_6.setPixmap(QPixmap.fromImage(
                QImage(cv2.cvtColor(cv2.resize(frame, (1920,1080), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB), 1920, 1080, QImage.Format.Format_RGB888)
            ))


    def getEar(self, leftEye, rightEye): 
        # получение EAR (Eyes Aspect Ratio) - 
        # прямо говоря это формат точек глаз, чем меньше расстояние от верхних точек, до нижних - тем меньше формат и тем меньше данное значение
        y = (
            math.sqrt((leftEye[1].y - leftEye[4].y)**2 + (leftEye[1].x - leftEye[4].x)**2) + math.sqrt((leftEye[2].y - leftEye[5].y)**2 + (leftEye[2].x - leftEye[5].x)**2) +
            math.sqrt((rightEye[1].y - rightEye[4].y)**2 + (rightEye[1].x - rightEye[4].x)**2) + math.sqrt((rightEye[2].y - rightEye[5].y)**2 + (rightEye[2].x - rightEye[5].x)**2)
        ) / 4
        x = (
            math.sqrt((leftEye[0].y - leftEye[3].y)**2 + (leftEye[0].x - leftEye[3].x)**2) + math.sqrt((rightEye[0].y - rightEye[3].y)**2 + (rightEye[0].x - rightEye[3].x)**2)
        ) / 2
        if x == 0: return 10
        return y / x


    def finishRegOperator(self): 
        # завершение регистрации оператора (проверка на нахождение данного оператора уже в системе)
        # и при успешной регистрации - заполнение его строчки в БД, сохранение его фотографии и выдать доступ к дальнейшим окнам
        
        data = self.initDB()

        self.logined = False
        self.after = 0

        self.operatorID = 0
        for i in data.to_dict('records'):
            self.operatorID = max(int(i['id']), self.operatorID)
        self.operatorID += 1

        self.found = False
        if not os.path.exists('./operators'):
            os.mkdir('operators')
        for i in os.listdir('./operators'):
            face = cv2.imread(f'./operators/{i}')
            faceEncs = face_recognition.face_encodings(face)
            if len(faceEncs) > 0:
                faceEnc = faceEncs[0]
            else:
                continue
            result = face_recognition.compare_faces([faceEnc], self.operatorFaceEnc)
            for i in result:
                self.found = i or self.found
        
        if self.found:
            self.createIdentWindow()
            return
        
        middleName = ' '
        if self.regUI.plainTextEdit_3.toPlainText().strip() != '':
            middleName = self.regUI.plainTextEdit_3.toPlainText().strip()
        self.operatorInfo = {
            'id': self.operatorID,
            'last_name': self.regUI.plainTextEdit.toPlainText().strip(), 'first_name': self.regUI.plainTextEdit_2.toPlainText().strip(), 'middle_name': middleName, 
            'age': self.regUI.plainTextEdit_4.toPlainText().strip(), 
            'date': self.timeNow.strftime('%d-%m-%Y'), 'time': self.timeNow.strftime('%H:%M:%S'), 'software_start_time': self.timeStart.strftime('%H:%M:%S'), 
            'drive_duration': '00:00:00', 'pulse_threshold_critical': 0, 'pulse_normal': 0, 'current_pulse': 0, 'operator_status': 'NORMAL'
        }
        pandas.concat([data, pandas.DataFrame([self.operatorInfo])], ignore_index=True).to_csv('./operators_db.csv', index=False)
        cv2.imwrite(f'./operators/ID_{str(self.operatorID).zfill(6)}.jpg', self.operatorFace)

        self.logined = True


    def finishAuthOperator(self):
        # завершение авторизации оператора (проверка на нахождение данного оператора под указанным айди в системе)
        # и при успешной авторизации - выдать доступ к дальнейшим окнам
        
        data = self.initDB()

        self.logined = False
        self.after = 1

        self.found = False
        if not os.path.exists('./operators'):
            os.mkdir('operators')
        if not os.path.exists(f'./operators/ID_{str(self.operatorID).zfill(6)}.jpg'):
            self.createIdentWindow()
            return
        face = cv2.imread(f'./operators/ID_{str(self.operatorID).zfill(6)}.jpg')
        faceEncs = face_recognition.face_encodings(face)
        if len(faceEncs) > 0:
            faceEnc = faceEncs[0]
        else:
            self.createIdentWindow()
            return
        result = face_recognition.compare_faces([faceEnc], self.operatorFaceEnc)
        for i in result:
            self.found = i or self.found
        
        if not self.found:
            self.createIdentWindow()
            return

        self.found = False
        self.logined = True


    def startCameraUprUpdate(self): # безопасно запустить камеру для формы Управление
        if self.cameraUprUpdateTimer.isActive():
            return
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.cap = cv2.VideoCapture(0)
        self.cameraUprUpdateTimer.start(20)


    def startVideoUpdate(self): # безопасно запустить видеопоток для формы Управление
        if self.videoUpdateTimer.isActive():
            return
        if self.video is not None:
            self.video.release()
            self.video = None
        self.video = cv2.VideoCapture('./files/videoBG.mp4')
        self.videoUpdateTimer.start(20)


    def startPulseUpdate(self): # безопасно запустить получение пульса для формы Управление
        if self.pulseUpdateTimer.isActive():
            return
        self.pulse = 0
        if self.com is not None:
            self.com.close()
            self.com = None
        
        for i,j,k in list_ports.comports():
            if 'Arduino' in j:
                self.com = serial.Serial(i)
                self.com.close()
                try:
                    self.com.open()
                except:
                    return
                self.pulseUpdateTimer.start(50)
                return


    def startRegOperatorPulse(self): # записывает порог и норму пульса, срабатывает при нажатии на кнопку
        if not self.analizUI.plainTextEdit.toPlainText().isdigit() or not self.analizUI.plainTextEdit_2.toPlainText().isdigit():
            return
        data = self.initDB()
        
        self.found = False
        operatorIndex = 0
        for i in data.to_dict('records'):
            if self.operatorID == int(i['id']):
                data.loc[operatorIndex, 'pulse_threshold_critical'] = int(self.analizUI.plainTextEdit.toPlainText())
                data.loc[operatorIndex, 'pulse_normal'] = int (self.analizUI.plainTextEdit_2.toPlainText())

                data.to_csv('./operators_db.csv', index=False)
                self.operatorInfo = i
                self.found = True
                break
            operatorIndex += 1


    def startAuthOperator(self): # безопасно запустить камеру для авторизации пользователя
        if self.cameraUpdateTimer.isActive():
            self.cameraUpdateTimer.stop()
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.cap = cv2.VideoCapture(0)
        self.cameraUpdateTimer.start(20)


    def startRegOperator(self): # безопасно запустить камеру для регистрации пользователя, если он указал валидные значения про себя
        if self.cameraUpdateTimer.isActive():
            self.cameraUpdateTimer.stop()
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        if self.regUI.plainTextEdit.toPlainText().strip() == '' or self.regUI.plainTextEdit_2.toPlainText().strip() == '' or not self.regUI.plainTextEdit_4.toPlainText().isdigit():
            return
        self.cap = cv2.VideoCapture(0)
        self.cameraUpdateTimer.start(20)
        # print(123)
        

    def createFirstWindow(self): # создать первую форму выбора - регистрация или авторизация
        self.windowID = 1
        self.first = QMainWindow()
        self.firstUI = firstClass()
        self.firstUI.setupUi(self.first)

        self.createTemplateWindow(self.first, self.firstUI)
        try:
            self.instr.close()
        except:
            pass
        try:
            self.analiz.close()
        except:
            pass

        self.firstUI.pushButton.clicked.connect(self.createRegWindow)
        self.firstUI.pushButton_2.clicked.connect(self.createSetidWindow)


    def createRegWindow(self): # форма регистрации
        self.windowID = 2
        self.reg = QMainWindow()
        self.regUI = regClass()
        self.regUI.setupUi(self.reg)

        self.createTemplateWindow(self.reg, self.regUI)
        try:
            self.first.close()
        except:
            pass

        self.regUI.pushButton.clicked.connect(self.startRegOperator)
        self.regUI.pushButton_2.clicked.connect(self.createInstrWindow)


    def createSetidWindow(self): # форма для написания айди при авторизации
        self.windowID = 3
        self.setid = QMainWindow()
        self.setidUI = setidClass()
        self.setidUI.setupUi(self.setid)

        self.createTemplateWindow(self.setid, self.setidUI)
        try:
            self.first.close()
        except:
            pass

        self.setidUI.pushButton_2.clicked.connect(self.createAuthWindow)


    def createAuthWindow(self): # форма авторизации
        if not self.setidUI.plainTextEdit.toPlainText().isdigit():
            return
        self.operatorID = int(self.setidUI.plainTextEdit.toPlainText().strip())
        self.found = False
        data = self.initDB()
        for i in data.to_dict('records'):
            if self.operatorID == int(i['id']):
                self.found = True
                break
        if not self.found:
            self.found = False
            return
        
        self.windowID = 4
        self.auth = QMainWindow()
        self.authUI = authClass()
        self.authUI.setupUi(self.auth)

        self.createTemplateWindow(self.auth, self.authUI)
        try:
            self.setid.close()
        except:
            pass
        self.authUI.pushButton_2.clicked.connect(self.createInstrWindow)

        self.startAuthOperator()


    def createIdentWindow(self): # форма диалогового окна для прохождения повторной идентификации
        self.found = False
        self.ident = QMainWindow()
        self.identUI = identClass()
        self.identUI.setupUi(self.ident)

        self.ident.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.identUI.label.mouseReleaseEvent = lambda event: self.finishIdent()
        self.identUI.widget.mousePressEvent = lambda event: self.mousePress(event)
        self.identUI.widget.mouseMoveEvent = lambda event: self.mouseMove(event, self.ident)
        self.identUI.widget.mouseReleaseEvent = lambda event: self.mouseRelease()
        self.ident.show()
        self.identUI.pushButton_2.clicked.connect(self.finishIdent)


    def createInstrWindow(self): # форма инструкции
        if not self.found and not self.logined:
            return
        
        self.windowID = 5
        self.instr = QMainWindow()
        self.instrUI = instrClass()
        self.instrUI.setupUi(self.instr)

        self.createTemplateWindow(self.instr, self.instrUI)
        try:
            self.reg.close()
        except:
            pass
        try:
            self.auth.close()
        except:
            pass
        try:
            self.analiz.close()
        except:
            pass
        try:
            self.upr.close()
        except:
            pass

        self.instrUI.pushButton_2.clicked.connect(self.createAnalizWindow)
        self.instrUI.pushButton_3.clicked.connect(self.createAnalizWindow)
        self.instrUI.pushButton_4.clicked.connect(self.createUprWindow)


    def createAnalizWindow(self): # форма анализа
        self.windowID = 6
        self.analiz = QMainWindow()
        self.analizUI = analizRegClass()
        if self.after == 1:
            self.analizUI = analizAuthClass()
        self.analizUI.setupUi(self.analiz)

        self.createTemplateWindow(self.analiz, self.analizUI)
        try:
            self.reg.close()
        except:
            pass
        try:
            self.auth.close()
        except:
            pass
        try:
            self.instr.close()
        except:
            pass
        try:
            self.upr.close()
        except:
            pass

        self.analizUI.pushButton_5.clicked.connect(self.createInstrWindow)
        self.analizUI.pushButton_4.clicked.connect(self.createUprWindow)
        self.analizUI.pushButton_2.clicked.connect(self.createUprWindow)
        if self.after == 0:
            self.analizUI.pushButton_6.clicked.connect(self.startRegOperatorPulse)


    def createUprWindow(self): # форма управления
        if not self.fullMode:
            return
        
        self.windowID = 7
        self.upr = QMainWindow()
        self.uprUI = uprClass()
        self.uprUI.setupUi(self.upr)

        self.createTemplateWindow(self.upr, self.uprUI)
        try:
            self.instr.close()
        except:
            pass
        try:
            self.analiz.close()
        except:
            pass

        self.uprUI.pushButton_5.clicked.connect(self.createInstrWindow)
        self.uprUI.pushButton_3.clicked.connect(self.createAnalizWindow)


app = QApplication([])
pr = Program()
app.exec() # запуск

