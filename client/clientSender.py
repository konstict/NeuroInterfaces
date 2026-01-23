import socket, struct, os, threading


address, port = '127.0.0.1', 5050


def sendFile(sock, path, name): # отправка конкретного файла (размер названия и название, размер данных и данные)
    path, name = str(path), str(name)

    pathName = f'{path}{name}'
    if not os.path.exists('./operators'):
        os.mkdir('operators')
    if not os.path.exists(pathName):
        return
    
    sock.sendall(struct.pack('!I', len(name)))
    sock.sendall(name.encode())

    dataSize = os.path.getsize(pathName)
    sock.sendall(struct.pack('!Q', dataSize))
    with open(pathName, 'rb') as file:
        while dataSize > 0:
            data = file.read(min(dataSize, 1024))
            sock.sendall(data)
            dataSize -= 1024


def sendAllFiles(sock): # отправка всех нужных файлов (БД и фотографии операторов)
    sendFile(sock, './', 'operators_db.csv')
    if not os.path.exists('./operators'):
        os.mkdir('operators')
    for file in os.listdir('./operators'):
        sendFile(sock, './operators/', file)


sock = None
def client(): # установление связи с сервером по айпи адресу и порту
    try:
        global sock
        sock = socket.create_connection((address, port))
        with sock:
            sendAllFiles(sock)
    except:
        print('client')


def main(): # запуск клиента в новом потоке
    try:
        thr = threading.Thread(target=client, daemon=False)
        thr.start()
    except:
        print('thr err')


if __name__ == '__main__':

    main()
