import socket
import struct
import os
import time
import threading

HOST = "0.0.0.0"    # слушаем
PORT = 5000

BASE_DIR = "./"
OPS_DIR = "./operators"

# создаём папку для операторов
os.makedirs(OPS_DIR, exist_ok=True)


def recv_exact(sock, size):
    """Гарантированно получает нужное число байт"""
    buf = b""
    while len(buf) < size:
        data = sock.recv(size - len(buf))
        if not data:
            raise ConnectionError("Соединение оборвалось")
        buf += data
    return buf


def choose_save_path(filename: str):
    """Определяет, куда сохранять файл по расширению"""

    lower = filename.lower()

    # изображения операторов
    if lower.endswith(".jpg") or lower.endswith(".jpeg") or lower.endswith(".png"):
        return os.path.join(OPS_DIR, filename)

    # таблица CSV (корень)
    if lower.endswith(".csv"):
        return os.path.join(BASE_DIR, filename)

    # всё остальное — тоже в корень (можно поменять)
    return os.path.join(BASE_DIR, filename)


def receive():
    try:
        with socket.socket() as s:
            s.bind((HOST, PORT))
            s.listen(1)

            print(f"Ожидаю соединения на порту {PORT}...")
            conn, addr = s.accept()
            print(f"Подключился: {addr}")

            while True:
                # Читаем длину имени файла
                name_len_data = recv_exact(conn, 4)
                name_len = struct.unpack("!I", name_len_data)[0]

                if name_len == 0:
                    print("Передача завершена")
                    break

                # Читаем имя файла
                name = recv_exact(conn, name_len).decode()

                # Читаем размер файла
                size = struct.unpack("!Q", recv_exact(conn, 8))[0]

                # определяем путь сохранения
                save_path = choose_save_path(name)

                print(f"Получаю файл: {name} ({size} байт)")
                print(f"Сохраняю в: {save_path}")

                # Получение данных файла
                with open(save_path, "wb") as f:
                    remaining = size
                    while remaining > 0:
                        chunk = conn.recv(min(4096, remaining))
                        if not chunk:
                            raise ConnectionError("Разрыв соединения")
                        f.write(chunk)
                        remaining -= len(chunk)

                print(f"Файл сохранён: {save_path}")
        isActive = False
    except:
        isActive = False


def main():
    t = threading.Thread(target = receive, daemon = True)
    t.start()
    print('start')