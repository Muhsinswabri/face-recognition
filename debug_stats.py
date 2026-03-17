import sys
sys.path.append('backend')
import warnings
warnings.filterwarnings('ignore')
from database import *

try:
    stats = get_attendance_stats()
    print("Present List Length:", len(stats.get('present_list', [])))
    print("Present List:", stats.get('present_list'))
    
    print("Absent List Length:", len(stats.get('absent_list', [])))
    print("Absent List:", stats.get('absent_list'))
except Exception as e:
    print("Error:", e)
