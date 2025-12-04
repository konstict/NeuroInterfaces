import cv2
import os
import numpy as np
import face_recognition

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Ошибка: не удалось открыть камеру.")
    exit()

files = os.listdir("operators")  # список всех файлов и папок в директории
id = 3

frameFace = None
frameFaceFaceEncs = None
while True:
    ret, frame = cap.read()
    if frame is None or not ret:
        continue
    locations = face_recognition.face_locations(frame)

    if len(locations) > 0:
        firstLocations = locations[0]
        frameFace = frame # frame[firstLocations[0]:firstLocations[2], firstLocations[3]:firstLocations[1]]
        frameFaceFaceEncs = face_recognition.face_encodings(frame, locations)[0]
        break

    cv2.imshow(winname='Video', mat=frame)

    if cv2.waitKey(1) == ord('q'):
        break

for file in files:
    face = face_recognition.load_image_file(f"operators/{file}")
    faceEnc = face_recognition.face_encodings(face)[0]
    results = face_recognition.compare_faces([faceEnc], frameFaceFaceEncs)
    result = False
    for k in results:
        result = result or k

    if result:
        print(result, file)
        break

if not os.path.exists("operators"):
    os.mkdir("operators")
cv2.imwrite(f'operators/ID_{str(id).zfill(6)}.jpg', frameFace)

cap.release()
cv2.destroyAllWindows()
