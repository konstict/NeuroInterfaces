import socket, struct, os, threading


address, port = '', 5050 # айпи не требуется, порт можно изменить (под устройства)


def recvData(sock, size): # полное принятие данных с указанным размером
    data = b''
    while size > len(data):
        thisData = sock.recv(size - len(data))
        data += thisData
        if not thisData:
            raise RuntimeError('server finish')
    return data


def recvFile(sock): # принятие конкретного файла (размер названия и название, размер данных и данные)
    sizeName = struct.unpack('!I', recvData(sock, 4))[0]
    name = recvData(sock, int(sizeName)).decode()

    if not os.path.exists('./operators'):
        os.mkdir('operators')
    path = './'
    if not name.endswith('.csv'):
        path = './operators/'
    pathName = f'{path}{name}'

    dataSize = struct.unpack('!Q', recvData(sock, 8))[0]
    with open(pathName, 'wb') as file:
        while dataSize > 0:
            data = recvData(sock, min(dataSize, 1024))
            file.write(data)
            dataSize -= 1024


def recvAllFiles(sock): # принять все файлы
    while True:
        recvFile(sock)


sock = socket.socket()
def server(): # создание сервера, установление связи с клиентом
    try:
        global sock
        sock = socket.create_server((address, port))
        with sock:
            conn, addr = sock.accept()
            with conn:
                recvAllFiles(conn)
    except:
        print('server')


def shutdownSocket():
    try:
        global sock
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except:
            pass
        sock.close()
        sock = None
    except:
        pass


def main(): # запуск сервера в новом потоке
    try:
        thr = threading.Thread(target=server, daemon=False)
        thr.start()
    except:
        print('thr err')


if __name__ == '__main__':

    main()
