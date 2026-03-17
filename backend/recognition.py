import datetime
import os
import pickle
import threading
import time

import cv2
import faiss
import numpy as np
from insightface.app import FaceAnalysis

from database import get_student_by_id, mark_attendance


BASE_DIR = os.path.dirname(__file__)
ENCODINGS_FILE = os.path.join(BASE_DIR, "..", "models", "face_encodings.pkl")


def load_encodings():
    if os.path.exists(ENCODINGS_FILE):
        with open(ENCODINGS_FILE, "rb") as file:
            return pickle.load(file)
    return {}


class BrowserRecognitionSystem:
    def __init__(self):
        self.lock = threading.Lock()
        self.face_app = None
        self.index = None
        self.known_ids = []

        self.active = False
        self.last_error = ""
        self.last_event = "Idle"
        self.last_event_type = "idle"
        self.last_event_id = 0
        self.last_student_id = None
        self.last_student_name = None
        self.marked_today = set()
        self.current_day = datetime.date.today().isoformat()

    def _set_event(self, event_type, message):
        self.last_event_type = event_type
        self.last_event = message
        self.last_event_id += 1

    def _refresh_day(self):
        today = datetime.date.today().isoformat()
        if today != self.current_day:
            self.current_day = today
            self.marked_today = set()

    def _ensure_model(self):
        if self.face_app is None:
            self.face_app = FaceAnalysis(name="buffalo_l")
            self.face_app.prepare(ctx_id=-1, det_size=(640, 640))

    def _build_index(self):
        encodings = load_encodings()
        known_ids = []
        known_embeddings = []

        for student_id, data in encodings.items():
            known_ids.append(student_id)
            known_embeddings.append(data["encoding"])

        index = faiss.IndexFlatIP(512)

        if known_embeddings:
            db_matrix = np.array(known_embeddings).astype("float32")
            faiss.normalize_L2(db_matrix)
            index.add(db_matrix)

        self.known_ids = known_ids
        self.index = index

    def start(self):
        with self.lock:
            self.last_error = ""
            self._refresh_day()
            self.last_student_id = None
            self.last_student_name = None
            self._set_event("starting", "Starting recognition...")

        try:
            self._ensure_model()
            self._build_index()

            with self.lock:
                self.active = True
                self._set_event("live", "Recognition live in browser")

            return True, "Attendance recognition is now running in the browser."
        except Exception as exc:
            with self.lock:
                self.active = False
                self.last_error = str(exc)
                self._set_event("error", "Failed to start recognition")

            return False, str(exc)

    def stop(self):
        with self.lock:
            self.active = False
            self._set_event("stopped", "Recognition stopped")

    def _get_status_unlocked(self):
        return {
            "active": self.active,
            "last_error": self.last_error,
            "last_event": self.last_event,
            "last_event_type": self.last_event_type,
            "last_event_id": self.last_event_id,
            "student_id": self.last_student_id,
            "student_name": self.last_student_name
        }

    def get_status(self):
        with self.lock:
            return self._get_status_unlocked()

    def recognize_frame_bytes(self, frame_bytes):
        started_at = time.perf_counter()

        with self.lock:
            self._refresh_day()
            if not self.active:
                return {
                    **self._get_status_unlocked(),
                    "matched": False,
                    "message": "Recognition is not running.",
                    "elapsed_ms": 0
                }

        frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
        frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)

        if frame is None:
            with self.lock:
                self.last_error = "Invalid image frame received"
                self._set_event("error", "Invalid image frame received")
                status = self._get_status_unlocked()

            return {
                **status,
                "matched": False,
                "message": "Invalid image frame received.",
                "elapsed_ms": round((time.perf_counter() - started_at) * 1000, 1)
            }

        # Keep CPU inference responsive for browser uploads.
        height, width = frame.shape[:2]
        max_width = 640
        if width > max_width:
            scale = max_width / float(width)
            frame = cv2.resize(frame, (max_width, int(height * scale)))

        faces = self.face_app.get(frame)

        if not faces:
            with self.lock:
                self._set_event("waiting", "Waiting for face")
                status = self._get_status_unlocked()

            return {
                **status,
                "matched": False,
                "message": "No face detected.",
                "elapsed_ms": round((time.perf_counter() - started_at) * 1000, 1)
            }

        if self.index is None or self.index.ntotal == 0:
            with self.lock:
                self.last_error = "No trained faces available"
                self._set_event("no_trained_faces", "No trained faces available")
                status = self._get_status_unlocked()

            return {
                **status,
                "matched": False,
                "message": "No trained faces available.",
                "elapsed_ms": round((time.perf_counter() - started_at) * 1000, 1)
            }

        matched_student_id = None
        best_similarity = 0.0

        for face in faces:
            embedding = face.embedding.astype("float32").reshape(1, -1)
            faiss.normalize_L2(embedding)
            distances, indices = self.index.search(embedding, 1)

            similarity = distances[0][0]
            index_id = indices[0][0]

            if similarity > 0.55:
                matched_student_id = self.known_ids[index_id]
                best_similarity = float(similarity)
                break

        if not matched_student_id:
            with self.lock:
                self._set_event("no_match", "Face detected, no match found")
                status = self._get_status_unlocked()

            return {
                **status,
                "matched": False,
                "message": "Face detected, no match found.",
                "elapsed_ms": round((time.perf_counter() - started_at) * 1000, 1)
            }

        student = get_student_by_id(matched_student_id)
        student_name = student.get("name") if student else matched_student_id
        result = mark_attendance(matched_student_id, self.current_day)

        with self.lock:
            self.last_student_id = matched_student_id
            self.last_student_name = student_name

            if result["ok"]:
                self.marked_today.add(matched_student_id)
                self._set_event("attendance_marked", f"Attendance marked for {student_name}")
            elif result["reason"] == "already_marked":
                self.marked_today.add(matched_student_id)
                self._set_event("attendance_already_marked", f"Attendance already marked for {student_name}")
            else:
                self.last_error = result["message"]
                self._set_event("attendance_error", f"Failed to mark attendance for {student_name}")

            status = self._get_status_unlocked()

        return {
            **status,
            "matched": True,
            "student_id": matched_student_id,
            "student_name": student_name,
            "student_major": student.get("major") if student else "",
            "student_year": student.get("year") if student else "",
            "student_image_url": f"/static/student_images/{matched_student_id}.jpg",
            "similarity": round(best_similarity, 4),
            "message": result["message"],
            "elapsed_ms": round((time.perf_counter() - started_at) * 1000, 1)
        }


recognition_system = BrowserRecognitionSystem()


def start_recognition_window():
    return recognition_system.start()
