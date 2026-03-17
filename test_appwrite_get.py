import os
import requests
import json
from dotenv import load_dotenv

load_dotenv(os.path.join('backend', '..', '.env'))

url = f"{os.getenv('APPWRITE_ENDPOINT')}/databases/{os.getenv('APPWRITE_DATABASE_ID')}/collections/{os.getenv('APPWRITE_ADMINS_COLLECTION_ID')}/documents"
headers = {
    'X-Appwrite-Project': os.getenv('APPWRITE_PROJECT_ID'),
    'X-Appwrite-Key': os.getenv('APPWRITE_API_KEY')
}
url_with_query = url + '?queries[]=equal("email",["swabri2004@gmail.com"])'

res = requests.get(url_with_query, headers=headers)
print("Status:", res.status_code)
try:
    print("Body:", json.dumps(res.json(), indent=2))
except:
    print("Body:", res.text)
