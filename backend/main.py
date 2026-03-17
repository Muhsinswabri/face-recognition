from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import os

# Import local modules
from database import (
    get_admin_by_email,
    get_student_by_id,
    add_student,
    get_attendance_stats,
    get_student_analytics,
    upload_student_image
)

from train_faces import capture_and_train_face, train_face_from_image_stream
from recognition import recognition_system, start_recognition_window


app = Flask(
    __name__,
    template_folder="../frontend",
    static_folder="../static"
)

app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback_secret_key")


def static_asset_url(filename):
    file_path = os.path.join(app.static_folder, filename)

    try:
        version = int(os.path.getmtime(file_path))
    except OSError:
        version = 0

    return url_for('static', filename=filename, v=version)


@app.context_processor
def inject_asset_helpers():
    return {
        "static_asset_url": static_asset_url
    }


@app.after_request
def add_no_cache_headers(response):
    if request.path.startswith('/api/') or response.mimetype == 'text/html':
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'

    return response


# ==============================
# HTML ROUTES
# ==============================

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/admin_login')
def admin_login():
    return render_template('admin_login.html')


@app.route('/student_login')
def student_login():
    return render_template('student_login.html')


@app.route('/attendance_scanner')
def attendance_scanner():
    return render_template('attendance_scanner.html')


@app.route('/admin_dashboard')
def admin_dashboard():

    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    return render_template('admin_dashboard.html')


@app.route('/student_dashboard')
def student_dashboard():

    if not session.get('student_id'):
        return redirect(url_for('student_login'))

    return render_template('student_dashboard.html')


# ==============================
# ADMIN LOGIN
# ==============================

@app.route('/api/admin/login', methods=['POST'])
def api_admin_login():

    data = request.json or {}

    email = data.get('email')
    password = data.get('password')

    admin = get_admin_by_email(email)

    if admin and str(admin.get("password_hash")) == str(password):

        session['admin_logged_in'] = True

        return jsonify({
            "status": "success",
            "message": "Login successful"
        }), 200

    return jsonify({
        "status": "error",
        "message": "Invalid credentials"
    }), 401


@app.route('/api/admin/logout', methods=['POST'])
def api_admin_logout():

    session.pop('admin_logged_in', None)

    return jsonify({
        "status": "success",
        "message": "Logged out"
    })


# ==============================
# STUDENT LOGIN
# ==============================

@app.route('/api/student/login', methods=['POST'])
def api_student_login():

    data = request.json or {}

    student_id = data.get('student_id')

    if not student_id:
        return jsonify({
            "status": "error",
            "message": "Student ID required"
        }), 400

    student = get_student_by_id(student_id)

    if student:

        session['student_id'] = student_id
        session['student_name'] = student.get('name')
        session['student_major'] = student.get('major', 'Unknown Major')

        return jsonify({
            "status": "success",
            "message": "Login successful"
        }), 200

    return jsonify({
        "status": "error",
        "message": "Invalid Student ID"
    }), 401


@app.route('/api/student/logout', methods=['POST'])
def api_student_logout():

    session.pop('student_id', None)
    session.pop('student_name', None)

    return jsonify({
        "status": "success",
        "message": "Logged out"
    })


# ==============================
# ADMIN DASHBOARD STATS
# ==============================

@app.route('/api/admin/stats', methods=['GET'])
def api_admin_stats():

    if not session.get('admin_logged_in'):
        return jsonify({
            "status": "error",
            "message": "Unauthorized"
        }), 401

    stats = get_attendance_stats()

    return jsonify({
        "status": "success",
        "data": stats
    })


# ==============================
# STUDENT DASHBOARD STATS
# ==============================

@app.route('/api/student/stats', methods=['GET'])
def api_student_stats():

    student_id = session.get('student_id')

    if not student_id:
        return jsonify({
            "status": "error",
            "message": "Unauthorized"
        }), 401

    stats = get_student_analytics(student_id)

    return jsonify({
        "status": "success",
        "data": {
            "student_name": session.get("student_name"),
            "student_id": student_id,
            "student_major": session.get("student_major"),
            "total_working_days": stats.get("total_working_days",0),
            "days_attended": stats.get("days_attended",0),
            "attendance_percentage": stats.get("attendance_percentage",0),
            "working_dates": stats.get("working_dates", []),
            "attended_dates": stats.get("attended_dates", [])
        }
    })


# ==============================
# ADD STUDENT
# ==============================

@app.route('/api/admin/add_student', methods=['POST'])
def api_add_student():

    if not session.get('admin_logged_in'):
        return jsonify({
            "status": "error",
            "message": "Unauthorized"
        }), 401

    # Handle multipart form
    if request.content_type and "multipart/form-data" in request.content_type:

        student_id = request.form.get('student_id')
        name = request.form.get('name')
        student_major = request.form.get('student_major')
        student_year = request.form.get('student_year')

        image_file = request.files.get('image')

    else:

        data = request.json or {}

        student_id = data.get('student_id')
        name = data.get('name')
        student_major = data.get('student_major')
        student_year = data.get('student_year')

        image_file = None


    # Validation
    if not student_id or not name:

        return jsonify({
            "status": "error",
            "message": "Student ID and Name are required"
        }), 400


    # Check duplicate student
    existing = get_student_by_id(student_id)

    if existing:

        return jsonify({
            "status": "error",
            "message": "Student already exists"
        }), 400


    print(f"Registering student: {student_id} - {name}")


    # Add student to database
    result = add_student(student_id, name, student_major, student_year)

    if not result:

        return jsonify({
            "status": "error",
            "message": "Failed to add student to DB"
        }), 500


    # =========================
    # IMAGE TRAINING
    # =========================

    if image_file and image_file.filename != '':

        success, face_bytes = train_face_from_image_stream(
            student_id,
            name,
            image_file,
            student_major,
            student_year
        )

        if success:

            if face_bytes:
                upload_student_image(student_id, face_bytes, f"{student_id}.jpg")

            return jsonify({
                "status": "success",
                "message": "Student added and face trained successfully from image!"
            })

        else:

            return jsonify({
                "status": "error",
                "message": f"Student added but face training failed: {face_bytes}"
            }), 400


    # =========================
    # WEBCAM TRAINING
    # =========================

    success, face_bytes = capture_and_train_face(
        student_id,
        name,
        student_major,
        student_year
    )

    if success:

        if face_bytes:
            upload_student_image(student_id, face_bytes, f"{student_id}.jpg")

        return jsonify({
            "status": "success",
            "message": "Student added and webcam face trained successfully!"
        })


    return jsonify({
        "status": "warning",
        "message": "Student added but webcam training cancelled."
    })


# ==============================
# START FACE RECOGNITION
# ==============================

@app.route('/api/start_attendance', methods=['POST'])
def api_start_attendance():
    try:
        success, message = start_recognition_window()
    except Exception as exc:
        return jsonify({
            "status": "error",
            "message": str(exc)
        }), 500

    status_code = 200 if success else 500

    return jsonify({
        "status": "success" if success else "error",
        "message": message
    }), status_code


@app.route('/api/attendance/recognize_frame', methods=['POST'])
def api_attendance_recognize_frame():
    frame = request.files.get('frame')

    if frame is None or frame.filename == '':
        return jsonify({
            "status": "error",
            "message": "Frame image is required."
        }), 400

    data = recognition_system.recognize_frame_bytes(frame.read())

    return jsonify({
        "status": "success" if data.get("matched") or data.get("active") else "error",
        "data": data
    })


@app.route('/api/attendance/status', methods=['GET'])
def api_attendance_status():
    data = recognition_system.get_status()

    return jsonify({
        "status": "success",
        "data": data
    })


@app.route('/api/attendance/stop', methods=['POST'])
def api_attendance_stop():
    recognition_system.stop()

    return jsonify({
        "status": "success",
        "message": "Attendance recognition stopped."
    })


# ==============================
# RUN SERVER
# ==============================

if __name__ == '__main__':

    app.run(debug=True, port=5000)
