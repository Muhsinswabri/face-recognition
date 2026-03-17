
import cv2
import os
import pickle
import numpy as np
import faiss
from insightface.app import FaceAnalysis

BASE_DIR = os.path.dirname(__file__)
ENCODINGS_FILE = os.path.join(BASE_DIR, "models", "face_encodings.pkl")
IMAGES_DIR = os.path.join(BASE_DIR, "static", "student_images")

def test_recognition():
    print("Initializing FaceAnalysis...")
    app = FaceAnalysis(name="buffalo_l")
    app.prepare(ctx_id=-1, det_size=(640, 640))

    if not os.path.exists(ENCODINGS_FILE):
        print("Encodings file not found!")
        return

    with open(ENCODINGS_FILE, "rb") as f:
        encodings = pickle.load(f)

    known_ids = []
    known_embeddings = []
    for sid, data in encodings.items():
        known_ids.append(sid)
        known_embeddings.append(data["encoding"])

    index = faiss.IndexFlatIP(512)
    if len(known_embeddings) > 0:
        db_matrix = np.array(known_embeddings).astype('float32')
        faiss.normalize_L2(db_matrix)
        index.add(db_matrix)
        print(f"Loaded {index.ntotal} encodings.")

    # Test with each image in static folder
    for filename in os.listdir(IMAGES_DIR):
        if not filename.endswith(".jpg"):
            continue
        
        img_id = os.path.splitext(filename)[0]

    img_path = os.path.join(IMAGES_DIR, filename)

    img = cv2.imread(img_path)

        if img is None:
            print(f"⚠️ Failed to read image: {img_path}")
            continue

        print(f"\nTesting image: {filename} (Expected ID: {img_id})")
        faces = app.get(img)
        
        if not faces:
            print("  FAIL: No face detected in test image!")
            continue

        for face in faces:
            embedding = face.embedding.astype('float32').reshape(1, -1)
            faiss.normalize_L2(embedding)
            
            distances, indices = index.search(embedding, 1)
            best_similarity = distances[0][0]
            best_idx = indices[0][0]
            recognized_id = known_ids[best_idx]

            print(f"  Recognized as: {recognized_id}")
            print(f"  Similarity: {best_similarity:.4f}")
            
            if recognized_id == img_id and best_similarity > 0.50:
                print("  RESULT: SUCCESS")
            elif recognized_id == img_id:
                print(f"  RESULT: WEAK MATCH (below 0.50 threshold)")
            else:
                print(f"  RESULT: MISMATCH (Recognized as {recognized_id} instead of {img_id})")

if __name__ == "__main__":
    test_recognition()
