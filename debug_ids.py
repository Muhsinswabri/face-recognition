import sys
sys.path.append('backend')
from database import *
import datetime

today = datetime.date.today().isoformat()
att = databases.list_documents(DB_ID, ATTENDANCE_COL_ID, [Query.equal('date', [today])])
present_ids = {doc['student_id'] for doc in att['documents']}
print('Present IDs:', present_ids)

stu = get_all_students()
stu_ids = {s.get('$id') for s in stu}
print('Student IDs:', stu_ids)

all_students_list = [{'id': s.get('$id'), 'name': s.get('name')} for s in stu]
present_list = [s for s in all_students_list if s['id'] in present_ids]
print('Present list length:', len(present_list))
