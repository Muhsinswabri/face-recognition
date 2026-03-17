import sys
sys.path.append('backend')
from database import *

all_students_db = get_all_students()
all_students_list = [{"id": s.get("$id"), "name": s.get("name")} for s in all_students_db]
print("all_students_list:")
for x in all_students_list:
    print(x)

import datetime
today = datetime.date.today().isoformat()
attendance_records = databases.list_documents(DB_ID, ATTENDANCE_COL_ID, [Query.equal("date", [today]), Query.limit(1000)])
present_student_ids = {str(doc["student_id"]) for doc in attendance_records["documents"]}
print("present_student_ids:", present_student_ids)

present_list = [s for s in all_students_list if str(s["id"]) in present_student_ids]
print("present_list:", present_list)
