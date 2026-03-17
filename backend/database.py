import os
from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.services.storage import Storage
from appwrite.input_file import InputFile
from appwrite.query import Query
from appwrite.exception import AppwriteException
from dotenv import load_dotenv
import datetime
import uuid
import requests

load_dotenv()

# -----------------------------
# Appwrite Connection
# -----------------------------
client = Client()

client.set_endpoint(os.getenv("APPWRITE_ENDPOINT"))
client.set_project(os.getenv("APPWRITE_PROJECT_ID"))
client.set_key(os.getenv("APPWRITE_API_KEY"))

databases = Databases(client)
storage = Storage(client)
BUCKET_ID = "student-images"

# -----------------------------
# Database / Collection IDs
# -----------------------------
DB_ID = os.getenv("APPWRITE_DATABASE_ID")
STUDENTS_COL_ID = os.getenv("APPWRITE_STUDENTS_COLLECTION_ID")
ATTENDANCE_COL_ID = os.getenv("APPWRITE_ATTENDANCE_COLLECTION_ID")
ADMINS_COL_ID = os.getenv("APPWRITE_ADMINS_COLLECTION_ID")


# -----------------------------
# ADMIN
# -----------------------------
def get_admin_by_email(email):
    try:
        response = databases.list_documents(
            database_id=DB_ID,
            collection_id=ADMINS_COL_ID,
            queries=[Query.equal("email", [email])]
        )

        if response["total"] > 0:
            return response["documents"][0]

        return None

    except AppwriteException as e:
        print("Error fetching admin:", e)
        return None


# -----------------------------
# STUDENTS
# -----------------------------
def add_student(student_id, name, student_major, student_year):
    try:
        # Based on the user's current Appwrite Schema, "student_id" is no longer an attribute.
        # It should be used solely as the document_id.
        
        # Sanitize student_id for Appwrite requirements (max 36 chars, valid chars)
        safe_student_id = "".join(c for c in student_id if c.isalnum() or c in '.-_')
        if not safe_student_id:
            safe_student_id = "unknown_student"
            
        # Year is a string in Appwrite Schema!
        data = {
            "name": name,
            "major": student_major,
            "year": str(student_year),
            "total_attendance": 0,
            "standing": "G",
            "starting_year": int(student_year) if str(student_year).isdigit() else 2024,
            "last_attendance_time": ""
        }

        response = databases.create_document(
            database_id=DB_ID,
            collection_id=STUDENTS_COL_ID,
            document_id=safe_student_id,
            data=data
        )

        return response

    except AppwriteException as e:
        print("Error adding student:", e)
        return None

def upload_student_image(student_id, file_bytes, filename):
    try:
        response = storage.create_file(
            bucket_id=BUCKET_ID,
            file_id=student_id, # Using student_id directly as the file_id
            file=InputFile.from_bytes(file_bytes, filename)
        )
        return response
    except AppwriteException as e:
        # If it already exists, replace it
        if "already exists" in str(e).lower():
            try:
                storage.delete_file(BUCKET_ID, student_id)
                return storage.create_file(
                    bucket_id=BUCKET_ID,
                    file_id=student_id,
                    file=InputFile.from_bytes(file_bytes, filename)
                )
            except Exception as e2:
                print("Error replacing existing image:", e2)
                return None
        print("Error uploading image:", e)
        return None


def get_student_by_id(student_id):
    try:
        # User schema often uses document_id == student_id
        try:
            doc = databases.get_document(
                database_id=DB_ID,
                collection_id=STUDENTS_COL_ID,
                document_id=student_id
            )
            return doc
        except Exception:
            pass # Fall back to query
            
        response = databases.list_documents(
            database_id=DB_ID,
            collection_id=STUDENTS_COL_ID,
            queries=[Query.equal("student_id", [student_id])]
        )

        if response["total"] > 0:
            return response["documents"][0]

        return None

    except AppwriteException as e:
        print("Error fetching student:", e)
        return None


def get_all_students():
    try:
        response = databases.list_documents(
            database_id=DB_ID,
            collection_id=STUDENTS_COL_ID,
            queries=[Query.limit(1000)]
        )

        return response["documents"]

    except AppwriteException as e:
        print("Error fetching students:", e)
        return []


# -----------------------------
# ATTENDANCE
# -----------------------------
def mark_attendance(student_id, date_str, status="Present"):
    try:
        # Check if attendance already exists
        response = databases.list_documents(
            database_id=DB_ID,
            collection_id=ATTENDANCE_COL_ID,
            queries=[
                Query.equal("student_id", [student_id]),
                Query.equal("date", [date_str])
            ]
        )

        if response["total"] > 0:
            print("Attendance already marked for today.")
            return {
                "ok": False,
                "reason": "already_marked",
                "message": "Attendance already marked for today."
            }

        databases.create_document(
            database_id=DB_ID,
            collection_id=ATTENDANCE_COL_ID,
            document_id=str(uuid.uuid4()),
            data={
                "student_id": student_id,
                "date": date_str,
                "status": status
            }
        )

        return {
            "ok": True,
            "reason": "marked",
            "message": "Attendance marked successfully."
        }

    except Exception as e:
        print("Error marking attendance:", e)
        return {
            "ok": False,
            "reason": "error",
            "message": str(e)
        }


# -----------------------------
# ADMIN ANALYTICS
# -----------------------------
def get_attendance_stats():
    all_students_db = get_all_students()
    all_students_list = [{"id": s.get("$id"), "name": s.get("name")} for s in all_students_db]
    total_students = len(all_students_list)
    
    today = datetime.date.today().isoformat()

    try:
        attendance_records = databases.list_documents(
            database_id=DB_ID,
            collection_id=ATTENDANCE_COL_ID,
            queries=[
                Query.equal("date", [today]),
                Query.limit(1000)
            ]
        )

        present_student_ids = {str(doc["student_id"]) for doc in attendance_records["documents"]}
        
        present_list = [s for s in all_students_list if str(s["id"]) in present_student_ids]
        absent_list = [s for s in all_students_list if str(s["id"]) not in present_student_ids]

        present_today_count = len(present_list)
        absent_today_count = len(absent_list)

        all_attendance = databases.list_documents(
            database_id=DB_ID,
            collection_id=ATTENDANCE_COL_ID,
            queries=[Query.select(["date"]), Query.limit(5000)]
        )

        unique_dates = sorted(list(set(doc["date"] for doc in all_attendance["documents"])))
        total_working_days = max(1, len(unique_dates))

        percentage_today = (
            (present_today_count / total_students) * 100 if total_students > 0 else 0
        )

        return {
            "total_students": total_students,
            "total_working_days": total_working_days,
            "present_today": present_today_count,
            "absent_today": absent_today_count,
            "percentage_today": round(percentage_today, 2),
            "students_list": all_students_list,
            "present_list": present_list,
            "absent_list": absent_list
        }

    except Exception as e:
        print("Error getting stats:", e)
        return {
            "total_students": total_students,
            "total_working_days": 0,
            "present_today": 0,
            "absent_today": 0,
            "percentage_today": 0,
            "students_list": all_students_list,
            "present_list": [],
            "absent_list": []
        }


# -----------------------------
# STUDENT ANALYTICS
# -----------------------------
def get_student_analytics(student_id):
    try:
        all_attendance = databases.list_documents(
            database_id=DB_ID,
            collection_id=ATTENDANCE_COL_ID,
            queries=[Query.select(["date"]), Query.limit(5000)]
        )

        unique_dates = sorted(list(set(doc["date"] for doc in all_attendance["documents"])))
        total_working_days = max(1, len(unique_dates))

        student_attendance = databases.list_documents(
            database_id=DB_ID,
            collection_id=ATTENDANCE_COL_ID,
            queries=[
                Query.equal("student_id", [student_id]),
                Query.equal("status", ["Present"]),
                Query.limit(1000)
            ]
        )

        attended_dates = sorted([doc["date"] for doc in student_attendance["documents"]])
        days_attended = len(attended_dates)

        percentage = (
            (days_attended / total_working_days) * 100
            if total_working_days > 0 else 0
        )

        return {
            "total_working_days": total_working_days,
            "days_attended": days_attended,
            "attendance_percentage": round(percentage, 2),
            "working_dates": unique_dates,
            "attended_dates": attended_dates
        }

    except Exception as e:
        print("Error getting analytics:", e)
        return {
            "total_working_days": 0,
            "days_attended": 0,
            "attendance_percentage": 0,
            "working_dates": [],
            "attended_dates": []
        }
