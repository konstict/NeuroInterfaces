import tkinter as tk
import numpy as np
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.figure import Figure


class GUI():
    root = None

    arial = None
    currentWidth = None
    currentHeight = None
    koefWidth = None
    koefHeight = None
    width = None
    height = None

    allFrames = []
    allEntryes = {
        'FIO': '',
        'AGE': 0
    }


    def __init__(self, root):
        self.root = root
        self.arial = ("Arial", 14)
        self.currentWidth = root.winfo_screenwidth()
        self.currentHeight = root.winfo_screenheight()
        self.koefWidth = 0.7
        self.koefHeight = 0.7
        self.width = self.currentWidth*self.koefWidth
        self.height = self.currentHeight*self.koefHeight

        root.title("Program")
        root.geometry(f"{int(self.width)}x{int(self.height)}+{int(self.width/5)}+{int(self.height/5)}")
        root.resizable(False, False)

        self.drawFirstForm()


    def __del__(self):
        print("close program")


    def drawFirstForm(self):
        self.deleteAllFormes()
        print('first frame')
        self.drawInformations(1)
        self.drawGraphEKG()
        self.drawGraphEMG()
        self.drawInstruction()
        self.informationBlock()


    def drawSecondForm(self):
        self.deleteAllFormes()
        print('second frame')
        self.drawInformations(2)
        self.drawGraphEKG()
        self.drawGraphEMG()
        # video
        self.informationBlock()


    def deleteAllFormes(self):
        print("delete all frames")
        for formes in self.allFrames:
            formes.destroy()


    def createFrame(self, sizeX=0, sizeY=0, posX=0, posY=0, underFrame=None,):
        if(underFrame):
            frame = tk.Frame(master=underFrame, borderwidth=1, relief='solid', ) #sunken
        else:
            frame = tk.Frame(borderwidth=1, relief='solid') #sunken
        frame.place(width=sizeX, height=sizeY, x=posX, y=posY)
        self.allFrames.append(frame)
        return frame


    def createLabel(self, underFrame=None, text="", anch="center", foreground="black", sizeX=None, sizeY=None, posX=None, posY=None):
        label = tk.Label(master=underFrame, text=text, font=self.arial, anchor=anch, foreground=foreground)
        if (not (posX and posY)):
            label.pack()
        else:
            label.place(relx=posX, rely=posY)
        label.update()
        return label
    

    def createEntry(self, underframe=None, foreground="black", sizeX=None, sizeY=None, posX=None, posY=None):
        entry = tk.Entry(master=underframe, font=self.arial, foreground=foreground)
        entry.place(relwidth=sizeX, relheight=sizeY, relx=posX, rely=posY)
        entry.update()
        return entry


    def createButton(self, underFrame=None, command=None, sizeX=None, sizeY=None, posX=None, posY=None, text=''):
        button = tk.Button(master=underFrame, text=text, command=command, cursor='Hand2', relief='solid')
        button.place(relwidth=sizeX, relheight=sizeY, relx=posX, rely=posY)
        return button


    def createFrameLabel(self, sizeX=0, sizeY=0, posX=0, posY=0, text="", anch="center", underFrame=None,):
        frame = self.createFrame(sizeX=sizeX, sizeY=sizeY, posX=posX, posY=posY, underFrame=underFrame,) #sunken
        label = self.createLabel(underFrame=frame, text=text, anch=anch)
        return frame, label
    

    def drawInformations(self, form=1):
        width = self.width; height = self.height

        self.createFrameLabel(width*70/100, height*5/100, 0, 0, f"Информация о разработчике")

        if form == 1:
            self.createFrameLabel(width*30/100, height*5/100, width*70/100, 0)
            self.createFrameLabel(width*0.3, height*3/20, width*0.7, height*0.05)
        else:
            self.createFrameLabel(width*30/100, height*5/100, width*70/100, 0, text="Информация о операторе")
            frame = self.createFrame(width*0.3, height*3/20, width*0.7, height*0.05)
            
            self.createLabel(underFrame=frame, text="ФИО", posX=5/100, posY=5/100)
            self.createLabel(underFrame=frame, text="Возраст", posX=5/100, posY=1/3)

            inputFio = self.createEntry(underframe=frame, sizeX=1/2, sizeY=1/4 , posX=1/3, posY=5/100)
            inputAge = self.createEntry(underframe=frame, sizeX=1/2, sizeY=1/4 , posX=1/3, posY=1/3)

            self.createButton(underFrame=frame, sizeX=25/100, sizeY=25/100, posX=2/3, posY=2/3, command=lambda: self.sendPeopleInformation(inputFio, inputAge), text='Записать')


        self.createFrameLabel(width*0.7/3, height*3/20, 0*width*0.7/3, height*0.05, f"Название\n образовательной\n организации")
        self.createFrameLabel(width*0.7/3, height*3/20, 1*width*0.7/3, height*0.05, f"Проектирование\n нейроинтерфейсов")
        self.createFrameLabel(width*0.7/3, height*3/20, 2*width*0.7/3, height*0.05, f"Рабочее место №__ \n ФИО конкурсанта")


    def drawGraph(self, main=None):
        mainWidth = main.winfo_width(); mainHeight = main.winfo_height()
        frame, label = self.createFrameLabel(mainWidth*90/100, mainHeight*60/100, mainWidth*5/100, mainHeight*15/100, underFrame=main)
        return label


    def drawGraphEKG(self):
        width = self.width; height = self.height
        frame, label = self.createFrameLabel(width*1/4, height*7/20, 0, height*0.05*4, "График ЭКГ")

        self.drawGraph(frame)
        

    def drawGraphEMG(self):
        width = self.width; height = self.height
        frame, label = self.createFrameLabel(width*1/4, height*7/20, width*1/4, height*0.05*4, "График ЭКГ")

        self.drawGraph(frame)

    
    def drawInstruction(self):
        instructions = self.getInstructions(True, True, False)
        width = self.width; height = self.height
        frame, _ = self.createFrameLabel(width*1/2, height*16/20, width*1/2, height*0.05*4)

        labels = [
            self.createLabel(frame, text=f"Инструкция \n1. Автоматическое определение COM-порта \n"),
            self.createLabel(frame, text=f'{instructions[0][1]}\n', foreground=instructions[0][2]),
            self.createLabel(frame, text='2.Подключите электроды ЭКГ\n'),
            self.createLabel(frame, text=f'{instructions[1][1]}\n', foreground=instructions[1][2]),
            self.createLabel(frame, text='3.Подключите электроды ЭМГ\n'),
            self.createLabel(frame, text=f'{instructions[2][1]}\n', foreground=instructions[2][2])
        ]

        self.createButton(underFrame=frame, command=self.drawSecondForm, sizeX=25/100, sizeY=10/100, posX=6/10, posY=8/10, text='Далее')
    

    def informationBlock(self):
        width = self.width; height = self.height
        main, _ = self.createFrameLabel(width*1/2, height*9/20, 0, height*0.05*4+height*7/20, "Информационный блок")
        
        mWidth = main.winfo_width(); mHeight = main.winfo_height()
        self.createFrameLabel(mWidth*80/100, mHeight*80/100, mWidth*10/100, mHeight*10/100, underFrame=main)
        
    
    def getInstructions(self, com=False, ekg=False, emg=False):
        instructions = []
        if (com):
            instructions.append(["COM", "Определен", "green"],)
        else:
            instructions.append(["COM", "Не определен", "red"],)
        if (ekg):
            instructions.append(["ЭКГ", "Подключено", "green"],)
        else:
            instructions.append(["ЭКГ", "Не подключено", "red"],)
        if (emg):
            instructions.append(["ЭМГ", "Подключено", "green"],)
        else:
            instructions.append(["ЭМГ", "Не подключено", "red"],)
        return instructions


    def sendPeopleInformation(self, inputFio, InputAge):
        pass


if (__name__ == "__main__"):
    root = tk.Tk()
    mainGui = GUI(root)
    
    root.mainloop()
