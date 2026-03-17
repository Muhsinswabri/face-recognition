import os
from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.exception import AppwriteException
from dotenv import load_dotenv

load_dotenv()

client = Client()
client.set_endpoint(os.getenv("APPWRITE_ENDPOINT"))
client.set_project(os.getenv("APPWRITE_PROJECT_ID"))
client.set_key(os.getenv("APPWRITE_API_KEY"))

databases = Databases(client)
DB_ID = os.getenv("APPWRITE_DATABASE_ID")
ATTENDANCE_COL_ID = os.getenv("APPWRITE_ATTENDANCE_COLLECTION_ID", "attendance")

def init_attendance_collection():
    try:
        # Check if collection exists
        try:
            databases.get_collection(DB_ID, ATTENDANCE_COL_ID)
            print(f"Collection '{ATTENDANCE_COL_ID}' already exists.")
            return
        except AppwriteException as e:
            if e.code == 404:
                print(f"Collection '{ATTENDANCE_COL_ID}' not found. Creating...")
                databases.create_collection(DB_ID, ATTENDANCE_COL_ID, ATTENDANCE_COL_ID)
                
                # Add attributes
                print("Adding attributes...")
                databases.create_string_attribute(DB_ID, ATTENDANCE_COL_ID, "student_id", 255, True)
                databases.create_string_attribute(DB_ID, ATTENDANCE_COL_ID, "date", 255, True)
                databases.create_string_attribute(DB_ID, ATTENDANCE_COL_ID, "status", 255, False, default="Present")
                
                print("Attendance collection successfully created!")
            else:
                print(f"Error checking collection: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    init_attendance_collection()
