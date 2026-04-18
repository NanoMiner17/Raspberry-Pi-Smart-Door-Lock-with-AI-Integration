import cv2
import os

person_name = input("Enter name: ")
save_dir = os.path.join("dataset", person_name)
os.makedirs(save_dir, exist_ok=True)

cam = cv2.VideoCapture(0)
count = 0

while True:
    ret, frame = cam.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    for (x,y,w,h) in faces:
        count += 1
        face = gray[y:y+h, x:x+w]
        cv2.imwrite(os.path.join(save_dir, f"{count}.jpg"), face)
        cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 2)

    cv2.imshow("Capturing Faces", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break
    if count >= 20:  # capture 20 samples
        break

cam.release()
cv2.destroyAllWindows()
