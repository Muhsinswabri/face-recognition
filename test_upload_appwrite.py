import sys
import os
sys.path.append('backend')
from database import upload_student_image
import traceback

try:
    with open('backend/static/student_images/1480.jpg', 'rb') as f:
        file_bytes = f.read()
    print("Uploading test image...")
    res = upload_student_image('test_img_123', file_bytes, 'test_img_123.jpg')
    print("Result:", res)
except Exception as e:
    print("Error:")
    traceback.print_exc()
