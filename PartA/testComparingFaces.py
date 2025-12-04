import cv2
import numpy as np
import face_recognition

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Ошибка: не удалось открыть камеру.")
    exit()

faces = [["stethem", "photo_2025-09-26_16-33-50.jpg"]]
faceEncs = []
for face in faces:
    file = face_recognition.load_image_file(face[1])
    face.append(file)
    faceEncs.append(face_recognition.face_encodings(file))

while True:
    ret, frame = cap.read()
    if frame is None:
        continue

    locations = face_recognition.face_locations(frame)

    if not ret:
        print("Ошибка: не удалось получить кадр. Прерывание.")
        break

    if len(locations) > 0:
        # frame = frame[firstLocations[0]:firstLocations[2], firstLocations[3]:firstLocations[1]]
        frameEncs = face_recognition.face_encodings(frame, locations)
        # cv2.imwrite('kostik.jpg', frame)
        for i, location in enumerate(locations):

            for j, faceEnc in enumerate(faceEncs):
                result = False

                for k in face_recognition.compare_faces(faceEnc, frameEncs[i]):
                    result = result or k
                print(result, faces[j][0])

            cv2.rectangle(frame, (location[3], location[0]), (location[1], location[2]), (255,255,255), 3)

    cv2.imshow(winname='Video', mat=frame)

    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
