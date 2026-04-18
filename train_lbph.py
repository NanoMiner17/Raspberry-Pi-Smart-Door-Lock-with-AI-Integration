import cv2
import os
import numpy as np

DATASET_DIR = "dataset"
faces = []
labels = []
label_dict = {}
label_id = 0

for person in os.listdir(DATASET_DIR):
    person_dir = os.path.join(DATASET_DIR, person)
    if not os.path.isdir(person_dir): continue
    label_dict[label_id] = person
    for imgname in os.listdir(person_dir):
        img_path = os.path.join(person_dir, imgname)
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        faces.append(img)
        labels.append(label_id)
    label_id += 1

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.train(faces, np.array(labels))
recognizer.save("face_model.yml")

# save label dictionary
np.save("labels.npy", label_dict)

print("Training finished saved model and labels")
