import os
from dotenv import load_dotenv
from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.exception import AppwriteException
import uuid

load_dotenv()

client = Client()
client.set_endpoint(os.getenv("APPWRITE_ENDPOINT"))
client.set_project(os.getenv("APPWRITE_PROJECT_ID"))
client.set_key(os.getenv("APPWRITE_API_KEY"))

databases = Databases(client)

try:
    response = databases.create_document(
        database_id=os.getenv("APPWRITE_DATABASE_ID"),
        collection_id=os.getenv("APPWRITE_STUDENTS_COLLECTION_ID"),
        document_id=str(uuid.uuid4()),
        data={
            "student_id": "test_id4",
            "name": "Test Name",
            "major": "Computer Science",
            "year": "2024"
        }
    )
    print("Success")
except Exception as e:
    print("Error:", str(e))
