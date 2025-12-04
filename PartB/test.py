import serial
import time

port = 'COM7'
baud_rate = 9600
ser = serial.Serial(port, baud_rate, timeout=1)
time.sleep(3)

timePrev = time.time()
while(1):
    if ser.in_waiting > 0:
        try:
            value = ser.readline().decode('utf-8').strip()
        except: pass
        else:
            if value != '':
                if int(value) >= 150:
                    diff = time.time() - timePrev
                    if diff >= 0.4:
                        pulse = 60 / diff
                        timePrev = time.time()
                        print(pulse, value)