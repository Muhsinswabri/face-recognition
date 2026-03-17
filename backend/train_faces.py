import cv2
from insightface.app import FaceAnalysis
import pickle
import os
import numpy as np

ENCODINGS_FILE = os.path.join(os.path.dirname(__file__), '..', 'models', 'face_encodings.pkl')
IMAGES_DIR = os.path.join(os.path.dirname(__file__), '..', 'static', 'student_images')

# Initialize InsightFace Model
app = FaceAnalysis(name='buffalo_l')
app.prepare(ctx_id=0, det_size=(640, 640))


# ------------------------------
# Load Encodings
# ------------------------------
def load_encodings():
    if os.path.exists(ENCODINGS_FILE):
        with open(ENCODINGS_FILE, 'rb') as f:
            return pickle.load(f)
    return {}


# ------------------------------
# Save Encodings
# ------------------------------
def save_encodings(encodings):
    os.makedirs(os.path.dirname(ENCODINGS_FILE), exist_ok=True)
    with open(ENCODINGS_FILE, 'wb') as f:
        pickle.dump(encodings, f)


# ------------------------------
# Webcam Training
# ------------------------------
def capture_and_train_face(student_id, student_name, student_major, student_year):

    cap = cv2.VideoCapture(0)
    print(f"Training for {student_name} ({student_id}).")

    captured_encodings = []

    while True:

        ret, frame = cap.read()

        if not ret:
            print("Failed to access camera.")
            break

        cv2.putText(frame, "Press 'C' to Capture Face (Need 5)", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.putText(frame, f"Captured: {len(captured_encodings)}/5", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        cv2.putText(frame, "Press 'Q' to Quit", (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        cv2.imshow("Student Face Capture Registration", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('c'):

            faces = app.get(frame)

            if faces:

                face_encoding = faces[0].embedding

                # Normalize embedding
                face_encoding = face_encoding / np.linalg.norm(face_encoding)

                captured_encodings.append(face_encoding)

                print(f"Captured {len(captured_encodings)} / 5")

                if len(captured_encodings) >= 5:
                    break

            else:
                print("No face detected! Try again.")

        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    if len(captured_encodings) >= 5:

        os.makedirs(IMAGES_DIR, exist_ok=True)

        bbox = faces[0].bbox.astype(int)

        left, top, right, bottom = bbox

        pad = 40

        h, w, _ = frame.shape

        t = max(0, top - pad)
        b = min(h, bottom + pad)
        l = max(0, left - pad)
        r = min(w, right + pad)

        face_crop = frame[t:b, l:r]

        face_bytes = None

        if face_crop.size > 0:

            imgPath = os.path.join(IMAGES_DIR, f"{student_id}.jpg")

            cv2.imwrite(imgPath, face_crop)

            _, buffer = cv2.imencode('.jpg', face_crop)

            face_bytes = buffer.tobytes()

        avg_encoding = np.mean(captured_encodings, axis=0)

        encodings = load_encodings()

        encodings[student_id] = {
            "name": student_name,
            "major": student_major,
            "year": student_year,
            "encoding": avg_encoding
        }

        save_encodings(encodings)

        print(f"Successfully generated and saved encoding for {student_name}.")

        return True, face_bytes

    print("Capture cancelled or insufficient frames.")

    return False, None


# ------------------------------
# Image Upload Training
# ------------------------------
def train_face_from_image_stream(student_id, student_name, image_stream, student_major, student_year):

    try:

        file_bytes = np.asarray(bytearray(image_stream.read()), dtype=np.uint8)

        image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        if image is None:
            return False, "Failed to decode image."

        faces = app.get(image)

        if not faces:
            return False, "No face detected."

        if len(faces) > 1:
            return False, "Multiple faces detected."

        face_encoding = faces[0].embedding

        # Normalize embedding
        face_encoding = face_encoding / np.linalg.norm(face_encoding)

        os.makedirs(IMAGES_DIR, exist_ok=True)

        bbox = faces[0].bbox.astype(int)

        left, top, right, bottom = bbox

        pad = 40

        h, w, _ = image.shape

        t = max(0, top - pad)
        b = min(h, bottom + pad)
        l = max(0, left - pad)
        r = min(w, right + pad)

        face_crop = image[t:b, l:r]

        face_bytes = None

        if face_crop.size > 0:

            imgPath = os.path.join(IMAGES_DIR, f"{student_id}.jpg")

            cv2.imwrite(imgPath, face_crop)

            _, buffer = cv2.imencode('.jpg', face_crop)

            face_bytes = buffer.tobytes()

        encodings = load_encodings()

        encodings[student_id] = {
            "name": student_name,
            "major": student_major,
            "year": student_year,
            "encoding": face_encoding
        }

        save_encodings(encodings)

        print(f"Successfully generated encoding for {student_name}")

        return True, face_bytes

    except Exception as e:

        print("Training error:", e)

        return False, str(e)


if __name__ == "__main__":
    print("Run this file through the backend system.")