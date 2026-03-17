import requests

url = 'http://localhost:5000/api/admin/add_student'
data = {
    'name': 'Test New Api',
    'student_id': 'api_test_999',
    'student_major': 'SE',
    'student_year': '4'
}
files = {
    'image': open('backend/static/student_images/1480.jpg', 'rb')
}

response = requests.post(url, data=data, files=files)
print(response.status_code)
print(response.text)
