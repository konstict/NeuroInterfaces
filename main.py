import tkinter as tk


class GUI():
    root = None
    
    arial = None

    currentWidth = None
    currentHeight = None
    koefWidth = None
    koefHeight = None
    width = None
    height = None


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
        root.geometry(f"{int(self.width)}x{int(self.height)}+100+100")
        # root.resizable(False, False)


    def drawAll(self):
        self.drawInformations()
        self.drawGraphEKG()
        self.drawGraphEMG()
        self.drawInstruction()
        self.informationBlock()


    def createFrameText(self, sizeX=0, sizeY=0, posX=0, posY=0, text="", anch="center", fram=None,):
        if(not fram):
            frame = tk.Frame(borderwidth=1, relief='solid') #sunken
        else:
            frame = tk.Frame(fram, borderwidth=1, relief='solid') #sunken
        label = tk.Label(frame, text=text, font=self.arial, anchor=anch)
        label.pack()
        frame.place(width=sizeX, height=sizeY, x=posX, y=posY)
        frame.update()
        return frame
    

    def createLabel(self, frame, text="", anch="center", foreground="black"):
        label = tk.Label(frame, text=text, font=self.arial, anchor=anch, foreground=foreground)
        label.pack()
        return label
    

    def drawInformations(self):
        width = self.width; height = self.height

        self.createFrameText(width*70/100, height*5/100, 0, 0, f"Информация о разработчике")
        self.createFrameText(width*30/100, height*5/100, width*70/100, 0)

        self.createFrameText(width*0.7/3, height*3/20, 0*width*0.7/3, height*0.05, f"Название\n образовательной\n организации")
        self.createFrameText(width*0.7/3, height*3/20, 1*width*0.7/3, height*0.05, f"Проектирование\n нейроинтерфейсов")
        self.createFrameText(width*0.7/3, height*3/20, 2*width*0.7/3, height*0.05, f"Рабочее место №__ \n ФИО конкурсанта")
        self.createFrameText(width*0.3, height*3/20, width*0.7, height*0.05)


    def drawGraphEKG(self):
        width = self.width; height = self.height
        main = self.createFrameText(width*1/4, height*7/20, 0, height*0.05*4, "График ЭКГ")

        mWidth = main.winfo_width(); mHeight = main.winfo_height()
        self.createFrameText(mWidth*90/100, mHeight*75/100, mWidth*5/100, mHeight*15/100, fram=main)


    def drawGraphEMG(self):
        width = self.width; height = self.height
        main = self.createFrameText(width*1/4, height*7/20, width*1/4, height*0.05*4, "График ЭКГ")

        mWidth = main.winfo_width(); mHeight = main.winfo_height()
        self.createFrameText(mWidth*90/100, mHeight*75/100, mWidth*5/100, mHeight*15/100, fram=main)

    
    def drawInstruction(self):
        instructions = self.getInstructions(True, True, False)
        width = self.width; height = self.height
        fr = self.createFrameText(width*1/2, height*16/20, width*1/2, height*0.05*4)

        labels = [
            self.createLabel(fr, text=f"Инструкция \n1. Автоматическое определение COM-порта \n"),
            self.createLabel(fr, text=f'{instructions[0][1]}\n', foreground=instructions[0][2]),
            self.createLabel(fr, text='2.Подключите электроды ЭКГ\n'),
            self.createLabel(fr, text=f'{instructions[1][1]}\n', foreground=instructions[1][2]),
            self.createLabel(fr, text='3.Подключите электроды ЭМГ\n'),
            self.createLabel(fr, text=f'{instructions[2][1]}\n', foreground=instructions[2][2])
        ]

        button = tk.Button(text="Далее", cursor='Hand2', relief='solid')
        button.place(width=150, height=50, x=width*8/10, y=height*8/10)
    

    def informationBlock(self):
        width = self.width; height = self.height
        main = self.createFrameText(width*1/2, height*9/20, 0, height*0.05*4+height*7/20, "Информационный блок")
        
        mWidth = main.winfo_width(); mHeight = main.winfo_height()
        self.createFrameText(mWidth*80/100, mHeight*80/100, mWidth*10/100, mHeight*10/100, fram=main)
        
    
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


if (__name__ == "__main__"):
    root = tk.Tk()
    mainGui = GUI(root)
    mainGui.drawAll()
    
    root.mainloop()