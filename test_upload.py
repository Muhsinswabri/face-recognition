import sys
import os
sys.path.append('backend')
from train_faces import train_face_from_image_stream
import io

print("Testing face training from image...")
image_path = os.path.join('backend', 'static', 'student_images', '1480.jpg')
if os.path.exists(image_path):
    with open(image_path, 'rb') as f:
        # Create a mock file stream similar to Werkzeug's FileStorage
        class MockFileStorage:
            def __init__(self, data):
                self.data = data
            def read(self):
                return self.data
        
        stream = MockFileStorage(f.read())
        student_id = "test_123"
        name = "Test Upload"
        major = "CS"
        year = "3"
        
        success, msg = train_face_from_image_stream(student_id, name, stream, major, year)
        print("Success:", success)
        print("Message:", msg)
else:
    print("Could not find a test image.")
