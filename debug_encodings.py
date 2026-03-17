
import pickle
import os

BASE_DIR = os.path.dirname(__file__)
ENCODINGS_FILE = os.path.join(BASE_DIR, "models", "face_encodings.pkl")

def inspect_pickle():
    if not os.path.exists(ENCODINGS_FILE):
        print(f"File not found: {ENCODINGS_FILE}")
        return

    with open(ENCODINGS_FILE, "rb") as f:
        data = pickle.load(f)
    
    print(f"Total entries: {len(data)}")
    for sid, info in data.items():
        print(f"ID: {sid}")
        print(f"  Name: {info.get('name')}")
        if 'encoding' in info:
            print(f"  Encoding shape: {info['encoding'].shape}")
        else:
            print("  NO ENCODING FOUND!")

if __name__ == "__main__":
    inspect_pickle()
