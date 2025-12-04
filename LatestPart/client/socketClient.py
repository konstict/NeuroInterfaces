import socket
import os
import struct
import threading

HOST = "10.220.235.174"   # IP получателя
PORT = 5000

CSV_PATH = "operators_db.csv"
FOLDER = "operators"        # папка с фотографиями


def send_file(sock, file_path):
    size = os.path.getsize(file_path)
    name = os.path.basename(file_path)

    # Отправляем длину имени файла + имя файла + размер
    sock.send(struct.pack("!I", len(name)))  # длина имени
    sock.send(name.encode())                 # имя
    sock.send(struct.pack("!Q", size))       # размер (8 байт)

    # Отправляем содержимое файла
    with open(file_path, "rb") as f:
        while chunk := f.read(4096):
            sock.send(chunk)

    print(f"Отправлен файл: {name} ({size} байт)")


def send():
    try:
        with socket.socket() as s:
            s.connect((HOST, PORT))
            print("Соединение установлено")

            # 1) Отправить CSV
            send_file(s, CSV_PATH)

            # 2) Отправить все файлы из папки
            for fname in os.listdir(FOLDER):
                path = os.path.join(FOLDER, fname)
                if os.path.isfile(path):
                    send_file(s, path)

            # Отправляем "конец" — пустое имя файла
            s.send(struct.pack("!I", 0))
            print("Передача завершена.")
    except:
        send()


def main():
    t = threading.Thread(target=send, daemon=True)
    t.start()
    print('start')