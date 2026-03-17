import os
import io
from appwrite.client import Client
from appwrite.services.storage import Storage
from dotenv import load_dotenv
from train_faces import load_encodings, save_encodings
import cv2
import numpy as np
import requests
from insightface.app import FaceAnalysis
from database import get_student_by_id

# Initialize InsightFace FaceAnalysis App
app = FaceAnalysis(name='buffalo_l')
app.prepare(ctx_id=0, det_size=(640, 640))

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

client = Client()
client.set_endpoint(os.getenv("APPWRITE_ENDPOINT"))
client.set_project(os.getenv("APPWRITE_PROJECT_ID"))
client.set_key(os.getenv("APPWRITE_API_KEY"))

storage = Storage(client)
BUCKET_ID = "student-images"

IMAGES_DIR = os.path.join(os.path.dirname(__file__), '..', 'static', 'student_images')
os.makedirs(IMAGES_DIR, exist_ok=True)

def sync_from_appwrite():
    print(f"Fetching files from Appwrite Storage (bucket: {BUCKET_ID})...")
    try:
        url = f"{os.getenv('APPWRITE_ENDPOINT')}/storage/buckets/{BUCKET_ID}/files"
        headers = {
            'X-Appwrite-Project': os.getenv('APPWRITE_PROJECT_ID'),
            'X-Appwrite-Key': os.getenv('APPWRITE_API_KEY')
        }
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        files = res.json().get('files', [])
    except Exception as e:
        print(f"Failed to list files from bucket {BUCKET_ID}: {e}")
        return

    print(f"Found {len(files)} files in bucket.")
    encodings = load_encodings()
    
    for file_info in files:
        file_id = file_info['$id']
        filename = file_info['name']
        print(f"Processing {filename} (ID: {file_id})...")
        
        # Determine student ID from filename (e.g., "1480.png" -> "1480")
        student_id = os.path.splitext(filename)[0]
        
        # Get student details from DB
        student_doc = get_student_by_id(student_id)
        if not student_doc:
            print(f"  Warning: No student found in database with ID {student_id}. Skipping.")
            continue
            
        student_name = student_doc['name']
        
        # Download file
        try:
            file_bytes = storage.get_file_download(bucket_id=BUCKET_ID, file_id=file_id)
        except Exception as e:
            print(f"  Failed to download file {file_id}: {e}")
            continue
            
        # Optional: save the raw image to static folder
        img_path = os.path.join(IMAGES_DIR, filename)
        
        # Read the image using cv2 directly from bytes
        try:
            file_bytes_np = np.asarray(bytearray(file_bytes), dtype=np.uint8)
            image = cv2.imdecode(file_bytes_np, cv2.IMREAD_COLOR)
        except Exception as e:
            print(f"  Failed to load image data for {filename}: {e}")
            continue
            
        faces = app.get(image)
        if not faces:
            print(f"  No face detected in {filename}. Skipping.")
            continue
            
        if len(faces) > 1:
            print(f"  Multiple faces detected in {filename}. Using the first one found.")
            
        face_encoding = faces[0].embedding
        
        # Save a crop as profile picture (to be consistent with local saving)
        bbox = faces[0].bbox.astype(int)
        left, top, right, bottom = bbox[0], bbox[1], bbox[2], bbox[3]
        pad = 40
        h, w, _ = image.shape
        t = max(0, top - pad)
        b = min(h, bottom + pad)
        l = max(0, left - pad)
        r = min(w, right + pad)
        
        face_crop = image[t:b, l:r]
        if face_crop.size > 0:
            imgPath = os.path.join(IMAGES_DIR, f"{student_id}.jpg")
            cv2.imwrite(imgPath, face_crop)
            print(f"  Saved profile image to {imgPath}")
            
        encodings[student_id] = {
            "name": student_name,
            "encoding": face_encoding
        }
        print(f"  Successfully encoded {student_name} ({student_id}).")
        
    save_encodings(encodings)
    print("Sync complete. Encodings saved.")

if __name__ == "__main__":
    sync_from_appwrite()
