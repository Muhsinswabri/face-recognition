// ===============================
// Alert Helper
// ===============================
function showAlert(message, type = 'success') {
    const alertBox = document.getElementById('customAlert');
    if (!alertBox) return;

    alertBox.className = `custom-alert alert alert-${type} alert-dismissible fade show glass-panel`;
    alertBox.innerHTML = `
        <strong>${type === 'success' ? 'Success!' : 'Notice'}</strong> ${message}
        <button type="button" class="btn-close btn-close-white" onclick="this.parentElement.style.display='none'"></button>
    `;

    alertBox.style.display = 'block';

    setTimeout(() => {
        alertBox.style.display = 'none';
    }, 5000);
}


// ===============================
// STUDENT LOGIN
// ===============================
const studentLoginForm = document.getElementById('studentLoginForm');

if (studentLoginForm) {
    studentLoginForm.addEventListener('submit', async (e) => {

        e.preventDefault();

        const studentId = document.getElementById('studentId').value;
        const btn = e.target.querySelector('button');

        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Loading...';

        try {

            const res = await fetch('/api/student/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ student_id: studentId })
            });

            const data = await res.json();

            if (res.ok) {
                window.location.href = '/student_dashboard';
            } else {
                showAlert(data.message, 'danger');
            }

        } catch (err) {
            showAlert('Connection error', 'danger');
        }

        btn.disabled = false;
        btn.innerHTML = 'Login to Dashboard';
    });
}


// ===============================
// ADMIN LOGIN
// ===============================
const adminLoginForm = document.getElementById('adminLoginForm');

if (adminLoginForm) {

    adminLoginForm.addEventListener('submit', async (e) => {

        e.preventDefault();

        const email = document.getElementById('adminEmail').value;
        const password = document.getElementById('adminPassword').value;
        const btn = e.target.querySelector('button');

        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Loading...';

        try {

            const res = await fetch('/api/admin/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });

            const data = await res.json();

            if (res.ok) {
                window.location.href = '/admin_dashboard';
            } else {
                showAlert(data.message, 'danger');
            }

        } catch (err) {
            showAlert('Connection error', 'danger');
        }

        btn.disabled = false;
        btn.innerHTML = 'Login as Admin';
    });
}


// ===============================
// ADD STUDENT
// ===============================
const addStudentForm = document.getElementById('addStudentForm');

if (addStudentForm) {

    addStudentForm.addEventListener('submit', async (e) => {

        e.preventDefault();

        const btn = document.getElementById('submitStudentBtn');
        const originalText = btn.innerHTML;

        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Registering...';

        const formData = new FormData();

        formData.append('name', document.getElementById('studentName').value);
        formData.append('student_id', document.getElementById('newStudentId').value);
        formData.append('student_major', document.getElementById('studentMajor').value);
        formData.append('student_year', document.getElementById('studentYear').value);

        const image = document.getElementById('studentImage').files[0];

        if (image) {
            formData.append('image', image);
        }

        try {

            const res = await fetch('/api/admin/add_student', {
                method: 'POST',
                body: formData
            });

            const data = await res.json();

            if (res.ok) {

                showAlert(data.message, 'success');

                const modalElement = document.getElementById('addStudentModal');
                const modal = bootstrap.Modal.getInstance(modalElement);

                modal.hide();

                addStudentForm.reset();

                loadAdminStats();

            } else {

                showAlert(data.message, 'danger');

            }

        } catch (err) {

            showAlert('System error occurred', 'danger');

        }

        btn.disabled = false;
        btn.innerHTML = originalText;

    });

}

// ===============================
// student DASHBOARD STATS
// ===============================

async function loadStudentStats() {

    try {

        const res = await fetch('/api/student/stats');

        if (res.status === 401) {
            window.location.href = '/student_login';
            return;
        }

        const data = await res.json();

        if (!data.data) return;

        const d = data.data;

        document.getElementById("stName").innerText = d.student_name;
        document.getElementById("stId").innerText = d.student_id;
        document.getElementById("stMajor").innerText = d.student_major;

        document.getElementById("stTotalDays").innerText = d.total_working_days;
        document.getElementById("stDaysAttended").innerText = d.days_attended;

        const workingList = document.getElementById("workingDaysList");
        if (workingList && d.working_dates) {
            workingList.innerHTML = d.working_dates.length ? 
                d.working_dates.map(date => `<li class="list-group-item text-white bg-transparent border-secondary text-center">${date}</li>`).join('') :
                '<li class="list-group-item text-muted bg-transparent border-secondary text-center">No working days recorded.</li>';
        }

        const attendedList = document.getElementById("attendedDaysList");
        if (attendedList && d.attended_dates) {
            attendedList.innerHTML = d.attended_dates.length ? 
                d.attended_dates.map(date => `<li class="list-group-item text-white bg-transparent border-secondary text-center"><i class="fas fa-check text-success me-2"></i>${date}</li>`).join('') :
                '<li class="list-group-item text-muted bg-transparent border-secondary text-center">No attendance recorded yet.</li>';
        }

        document.getElementById("progressText").innerText =
            Math.round(d.attendance_percentage) + "%";

        const circle = document.getElementById("progressCircle");

        let color = "#ef4444";

        if (d.attendance_percentage >= 75) color = "#10b981";
        else if (d.attendance_percentage >= 50) color = "#f59e0b";

        circle.style.background =
            `conic-gradient(${color} ${d.attendance_percentage}%, #1f2937 0)`;

        const stImageEl = document.getElementById('stImage');
        if (stImageEl) {
            stImageEl.src = `/static/student_images/${d.student_id}.jpg`;
            stImageEl.style.display = 'inline-block';
            stImageEl.onerror = function() {
                this.style.display = 'none';
            };
        }

        const requiredContent = document.getElementById('requirementMetric');
        if (requiredContent) {
            if (d.attendance_percentage >= 75 || d.total_working_days === 0) {
                requiredContent.innerHTML = `<span class="text-success fw-bold"><i class="fas fa-check-circle"></i> Requirements Met (≥75%)</span>`;
            } else {
                const daysNeeded = Math.ceil(3 * d.total_working_days - 4 * d.days_attended);
                requiredContent.innerHTML = `<span class="text-warning fw-bold"><i class="fas fa-exclamation-triangle"></i> Action Required</span><br/><small class="text-muted mt-2 d-block">You must attend exactly <strong>${Math.max(1, daysNeeded)}</strong> consecutive days to reach 75%.</small>`;
            }
        }

    } catch (err) {
        console.log("Error loading stats:", err);
    }

}

// ===============================
// ADMIN DASHBOARD STATS
// ===============================
async function loadAdminStats() {

    try {

        const res = await fetch('/api/admin/stats');

        if (res.status === 401) {
            window.location.href = '/admin_login';
            return;
        }

        const data = await res.json();

        if (res.ok && data.data) {

            const d = data.data;

            document.getElementById('totalStudents').innerText = d.total_students;
            document.getElementById('presentToday').innerText = d.present_today;
            document.getElementById('absentToday').innerText = d.absent_today;
            document.getElementById('attendancePerc').innerText = d.percentage_today + '%';

            // Populate Total Students List
            const totalListEl = document.getElementById('totalStudentsList');
            if (totalListEl && d.students_list) {
                totalListEl.innerHTML = d.students_list.length ? 
                    d.students_list.map(s => `<li class="list-group-item text-white bg-transparent border-secondary d-flex justify-content-between align-items-center"><span>${s.name}</span> <small class="text-muted">ID: ${s.id}</small></li>`).join('') :
                    '<li class="list-group-item text-muted bg-transparent border-secondary text-center">No students found.</li>';
            }

            // Populate Present Students List
            const presentListEl = document.getElementById('presentTodayList');
            if (presentListEl && d.present_list) {
                presentListEl.innerHTML = d.present_list.length ? 
                    d.present_list.map(s => `<li class="list-group-item text-white bg-transparent border-secondary d-flex justify-content-between align-items-center"><span class="text-success"><i class="fas fa-check me-2"></i>${s.name}</span> <small class="text-muted">ID: ${s.id}</small></li>`).join('') :
                    '<li class="list-group-item text-muted bg-transparent border-secondary text-center">No one is present today.</li>';
            }

            // Populate Absent Students List
            const absentListEl = document.getElementById('absentTodayList');
            if (absentListEl && d.absent_list) {
                absentListEl.innerHTML = d.absent_list.length ? 
                    d.absent_list.map(s => `<li class="list-group-item text-white bg-transparent border-secondary d-flex justify-content-between align-items-center"><span class="text-danger"><i class="fas fa-xmark me-2"></i>${s.name}</span> <small class="text-muted">ID: ${s.id}</small></li>`).join('') :
                    '<li class="list-group-item text-muted bg-transparent border-secondary text-center">Everyone is present today!</li>';
            }

        }

    } catch (err) {

        console.error(err);

    }

}


// ===============================
// START FACE RECOGNITION
// ===============================
const startAttendanceBtn = document.getElementById('startAttendanceBtn');
const globalAttendanceBtn = document.getElementById('globalStartAttendanceBtn');
const stopAttendanceBtn = document.getElementById('stopAttendanceBtn');
const attendanceViewer = document.getElementById('attendanceViewer');
const attendanceVideo = document.getElementById('attendanceVideo');
const attendanceCanvas = document.getElementById('attendanceCanvas');
const attendancePlaceholder = document.getElementById('attendancePlaceholder');
const attendancePlaceholderTitle = document.getElementById('attendancePlaceholderTitle');
const attendancePlaceholderText = document.getElementById('attendancePlaceholderText');
const attendanceStatusBadge = document.getElementById('attendanceStatusBadge');
const attendanceLastEvent = document.getElementById('attendanceLastEvent');
const attendanceStudent = document.getElementById('attendanceStudent');
const attendanceResult = document.getElementById('attendanceResult');
const attendanceResultTitle = document.getElementById('attendanceResultTitle');
const attendanceResultMessage = document.getElementById('attendanceResultMessage');
const attendanceResultIcon = document.getElementById('attendanceResultIcon');
const recognizedStudentImage = document.getElementById('recognizedStudentImage');
const recognizedStudentPlaceholder = document.getElementById('recognizedStudentPlaceholder');
const recognizedStudentName = document.getElementById('recognizedStudentName');
const recognizedStudentId = document.getElementById('recognizedStudentId');
const recognizedStudentMajor = document.getElementById('recognizedStudentMajor');
const recognizedStudentYear = document.getElementById('recognizedStudentYear');
const recognizedStudentSimilarity = document.getElementById('recognizedStudentSimilarity');

const cameraBtn = globalAttendanceBtn || startAttendanceBtn;
let attendanceStartInFlight = false;
let attendanceStream = null;
let recognitionLoopTimer = null;
let recognitionRequestInFlight = false;

function updateAttendanceBadge(active, hasError = false) {
    if (!attendanceStatusBadge) return;

    attendanceStatusBadge.className = 'badge';

    if (hasError) {
        attendanceStatusBadge.classList.add('text-bg-danger');
        attendanceStatusBadge.innerText = 'Error';
        return;
    }

    if (active) {
        attendanceStatusBadge.classList.add('text-bg-success');
        attendanceStatusBadge.innerText = 'Live';
        return;
    }

    attendanceStatusBadge.classList.add('text-bg-secondary');
    attendanceStatusBadge.innerText = 'Offline';
}

function showAttendanceViewer() {
    if (attendanceViewer) {
        attendanceViewer.classList.remove('d-none');
    }
}

function updateAttendancePlaceholder(title, message) {
    if (attendancePlaceholderTitle) {
        attendancePlaceholderTitle.innerText = title;
    }

    if (attendancePlaceholderText) {
        attendancePlaceholderText.innerText = message;
    }
}

function updateAttendanceResult(type, title, message) {
    if (!attendanceResult || !attendanceResultTitle || !attendanceResultMessage || !attendanceResultIcon) {
        return;
    }

    attendanceResult.classList.remove('d-none', 'attendance-result-success', 'attendance-result-warning');

    if (type === 'success') {
        attendanceResult.classList.add('attendance-result-success');
        attendanceResultIcon.innerHTML = '<i class="fas fa-check-circle"></i>';
    } else if (type === 'warning') {
        attendanceResult.classList.add('attendance-result-warning');
        attendanceResultIcon.innerHTML = '<i class="fas fa-clock-rotate-left"></i>';
    } else {
        attendanceResultIcon.innerHTML = '<i class="fas fa-camera"></i>';
    }

    attendanceResultTitle.innerText = title;
    attendanceResultMessage.innerText = message;
}

function updateRecognizedStudentCard(data = {}) {
    if (!recognizedStudentName) return;

    const hasMatch = Boolean(data.student_id);

    recognizedStudentName.innerText = hasMatch ? (data.student_name || data.student_id) : 'Waiting for recognition';
    recognizedStudentId.innerText = hasMatch ? data.student_id : '-';
    recognizedStudentMajor.innerText = hasMatch ? (data.student_major || 'Not available') : '-';
    recognizedStudentYear.innerText = hasMatch ? (data.student_year || 'Not available') : '-';
    recognizedStudentSimilarity.innerText = typeof data.similarity === 'number'
        ? `${(data.similarity * 100).toFixed(1)}%`
        : '-';

    if (!recognizedStudentImage || !recognizedStudentPlaceholder) return;

    if (hasMatch && data.student_image_url) {
        recognizedStudentImage.src = data.student_image_url;
        recognizedStudentImage.classList.remove('d-none');
        recognizedStudentPlaceholder.classList.add('d-none');
        recognizedStudentImage.onerror = function () {
            recognizedStudentImage.classList.add('d-none');
            recognizedStudentPlaceholder.classList.remove('d-none');
        };
    } else {
        recognizedStudentImage.removeAttribute('src');
        recognizedStudentImage.classList.add('d-none');
        recognizedStudentPlaceholder.classList.remove('d-none');
    }
}

async function parseApiResponse(res) {
    const contentType = res.headers.get('content-type') || '';

    if (contentType.includes('application/json')) {
        return await res.json();
    }

    const text = await res.text();
    return {
        status: res.ok ? 'success' : 'error',
        message: text || `Request failed with status ${res.status}`
    };
}

function setAttendanceFeedActive(active) {
    if (!attendanceVideo || !attendancePlaceholder) return;

    if (active) {
        attendanceVideo.classList.remove('d-none');
        attendancePlaceholder.classList.add('d-none');
        return;
    }

    attendanceVideo.classList.add('d-none');
    attendancePlaceholder.classList.remove('d-none');
    if (attendanceVideo) {
        attendanceVideo.srcObject = null;
    }
}

async function startBrowserCamera() {
    if (!attendanceVideo) return;

    updateAttendancePlaceholder(
        'Requesting camera access',
        'Allow camera permission in the browser to begin scanning.'
    );

    const stream = await navigator.mediaDevices.getUserMedia({
        video: {
            facingMode: 'user',
            width: { ideal: 1280 },
            height: { ideal: 720 }
        },
        audio: false
    });

    attendanceStream = stream;
    attendanceVideo.srcObject = stream;
    await attendanceVideo.play();
    setAttendanceFeedActive(true);
    updateAttendancePlaceholder(
        'Camera connected',
        'Live browser preview is active. Hold still while recognition checks your face.'
    );
}

function stopBrowserCamera() {
    if (recognitionLoopTimer) {
        clearInterval(recognitionLoopTimer);
        recognitionLoopTimer = null;
    }

    if (attendanceStream) {
        attendanceStream.getTracks().forEach(track => track.stop());
        attendanceStream = null;
    }

    setAttendanceFeedActive(false);
}

async function captureAndRecognizeFrame() {
    if (!attendanceVideo || !attendanceCanvas || recognitionRequestInFlight) return;
    if (!attendanceStream || attendanceVideo.readyState < 2) return;

    recognitionRequestInFlight = true;

    try {
        attendanceCanvas.width = attendanceVideo.videoWidth || 640;
        attendanceCanvas.height = attendanceVideo.videoHeight || 480;

        const context = attendanceCanvas.getContext('2d');
        context.drawImage(attendanceVideo, 0, 0, attendanceCanvas.width, attendanceCanvas.height);

        const blob = await new Promise(resolve => {
            attendanceCanvas.toBlob(resolve, 'image/jpeg', 0.85);
        });

        if (!blob) {
            throw new Error('Could not capture camera frame');
        }

        const formData = new FormData();
        formData.append('frame', blob, 'frame.jpg');

        const res = await fetch('/api/attendance/recognize_frame', {
            method: 'POST',
            body: formData
        });

        const payload = await parseApiResponse(res);
        const data = payload.data || {};

        if (!res.ok) {
            throw new Error(payload.message || 'Recognition request failed');
        }

        if (attendanceLastEvent) {
            const elapsed = typeof data.elapsed_ms === 'number' ? ` (${data.elapsed_ms} ms)` : '';
            attendanceLastEvent.innerText = `${data.last_error || data.last_event || 'Scanning...'}${elapsed}`;
        }

        if (attendanceStudent) {
            attendanceStudent.innerText = data.student_name || data.student_id || 'Waiting for match';
        }

        updateRecognizedStudentCard(data);

        updateAttendanceBadge(Boolean(data.active), Boolean(data.last_error));

        if (data.last_event_type === 'attendance_marked') {
            const studentName = data.student_name || data.student_id || 'Student';
            updateAttendanceResult(
                'success',
                'Attendance Marked Successfully',
                `${studentName} has been marked present successfully.`
            );
            showAlert(`${studentName} attendance marked successfully`, 'success');
            await stopAttendanceRecognition({
                showSuccessToast: false,
                preserveResult: true
            });
        } else if (data.last_event_type === 'attendance_already_marked') {
            const studentName = data.student_name || data.student_id || 'Student';
            updateAttendanceResult(
                'warning',
                'Attendance Already Marked',
                `${studentName} has already been marked present for today.`
            );
            showAlert(`${studentName} attendance is already marked for today`, 'warning');
            await stopAttendanceRecognition({
                showSuccessToast: false,
                preserveResult: true
            });
        } else if (data.last_event_type === 'attendance_error') {
            updateAttendanceResult(
                'warning',
                'Attendance Mark Failed',
                data.last_error || data.message || 'The system could not save attendance right now.'
            );
            showAlert(data.last_error || data.message || 'Attendance could not be marked', 'danger');
        }
    } catch (err) {
        const message = err?.message || 'Recognition failed';

        updateAttendanceBadge(false, true);
        if (attendanceLastEvent) {
            attendanceLastEvent.innerText = message;
        }
        updateAttendanceResult(
            'warning',
            'Recognition Delayed',
            message
        );
    } finally {
        recognitionRequestInFlight = false;
    }
}

function startRecognitionLoop() {
    if (recognitionLoopTimer) {
        clearInterval(recognitionLoopTimer);
    }

    recognitionLoopTimer = setInterval(() => {
        captureAndRecognizeFrame();
    }, 1200);
}

async function startAttendanceRecognition(buttonOverride = cameraBtn) {
    if (!buttonOverride || attendanceStartInFlight) return;

    const originalText = buttonOverride.innerHTML;
    attendanceStartInFlight = true;

    buttonOverride.disabled = true;
    buttonOverride.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Launching...';

    try {

        const res = await fetch('/api/start_attendance', {
            method: 'POST'
        });

        const data = await parseApiResponse(res);

        if (res.ok) {
            showAttendanceViewer();
            updateAttendanceBadge(true);
            if (attendanceLastEvent) {
                attendanceLastEvent.innerText = data.message;
            }
            updateAttendanceResult(
                'neutral',
                'Scanner Started',
                'Recognition is running. Once a face is confirmed, attendance status will appear here.'
            );
            await startBrowserCamera();
            startRecognitionLoop();
            showAlert(data.message, 'success');
        } else {
            updateAttendanceBadge(false, true);
            if (attendanceLastEvent) {
                attendanceLastEvent.innerText = data.message;
            }
            updateAttendancePlaceholder(
                'Unable to start scanner',
                data.message
            );
            showAlert(data.message, 'danger');
        }

    } catch (err) {
        const message = err?.message || 'Failed to launch recognition';
        updateAttendanceBadge(false, true);
        if (attendanceLastEvent) {
            attendanceLastEvent.innerText = message;
        }
        updateAttendancePlaceholder(
            'Unable to start scanner',
            message
        );
        showAlert(message, 'danger');
    }

    setTimeout(() => {
        buttonOverride.disabled = false;
        buttonOverride.innerHTML = originalText;
        attendanceStartInFlight = false;
    }, 3000);
}

async function stopAttendanceRecognition(options = {}) {
    const {
        showSuccessToast = true,
        preserveResult = false
    } = options;

    if (stopAttendanceBtn) {
        stopAttendanceBtn.disabled = true;
    }

    try {
        const res = await fetch('/api/attendance/stop', {
            method: 'POST'
        });

        const data = await parseApiResponse(res);

        if (res.ok) {
            stopBrowserCamera();
            updateAttendanceBadge(false);

            if (attendanceLastEvent) {
                attendanceLastEvent.innerText = data.message;
            }

            if (attendanceStudent) {
                attendanceStudent.innerText = 'Waiting for match';
            }

            if (!preserveResult) {
                updateAttendanceResult(
                    'neutral',
                    'Scanner Stopped',
                    'Start the scanner again to continue marking attendance.'
                );
            }

            if (showSuccessToast) {
                showAlert(data.message, 'success');
            }
        } else {
            showAlert(data.message || 'Failed to stop recognition', 'danger');
        }
    } catch (err) {
        showAlert('Failed to stop recognition', 'danger');
    }

    if (stopAttendanceBtn) {
        stopAttendanceBtn.disabled = false;
    }
}

if (cameraBtn) {

    cameraBtn.addEventListener('click', async () => {
        await startAttendanceRecognition(cameraBtn);
    });

}

if (stopAttendanceBtn) {
    stopAttendanceBtn.addEventListener('click', async () => {
        await stopAttendanceRecognition();
    });
}

if (startAttendanceBtn && startAttendanceBtn.dataset.autoStart === 'true') {
    setTimeout(() => {
        if (attendanceStream) {
            return;
        }
        startAttendanceRecognition(startAttendanceBtn);
    }, 300);
}


// ===============================
// LOGOUT
// ===============================
document.querySelectorAll('.logout-btn').forEach(btn => {

    btn.addEventListener('click', async (e) => {

        const type = e.target.dataset.type;

        await fetch(`/api/${type}/logout`, {
            method: 'POST'
        });

        window.location.href = '/';

    });

});
