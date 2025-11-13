from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from jose import jwt
import json
import time
import requests
import os
import datetime # Cần thiết cho việc xử lý ngày (dob)

# ---- OIDC config lấy từ biến môi trường (đặt trong docker-compose) ----
ISSUER = os.getenv("OIDC_ISSUER", "http://keycloak:8080/realms/master")
AUDIENCE = os.getenv("OIDC_AUDIENCE", "myapp") # client_id
JWKS_URL = f"{ISSUER}/protocol/openid-connect/certs"

# ---- Database Config (Lấy từ Docker Compose) ----
# Chúng ta sẽ dùng tên database 'studentdb' mà bạn đã tạo
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "root")
DB_HOST = os.getenv("DB_HOST", "relational-database-server")
DB_NAME = os.getenv("DB_NAME", "studentdb") 
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:3306/{DB_NAME}"

# ---- Cấu hình đường dẫn cho tệp JSON ----
# Lấy đường dẫn thư mục CHÍNH XÁC nơi tệp app.py này đang nằm
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Tạo đường dẫn đầy đủ đến tệp students.json
JSON_PATH = os.path.join(BASE_DIR, "students.json")


app = Flask(__name__)

# ---- App Config ----
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Khởi tạo SQLAlchemy
db = SQLAlchemy(app)

# ---- Database Model (Ánh xạ tới bảng 'students') ----
class Student(db.Model):
    __tablename__ = 'students'
    
    # Các cột này phải khớp với tệp 002_studentdb.sql của bạn
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.String(10))
    fullname = db.Column(db.String(100))
    dob = db.Column(db.Date)
    major = db.Column(db.String(50))

    # Hàm helper để chuyển đổi model thành dictionary (để jsonify)
    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "fullname": self.fullname,
            "dob": self.dob.isoformat() if self.dob else None, # Chuyển date thành string
            "major": self.major
        }

# ---- JWKS cache & verify (Giữ nguyên) ----
_JWKS = None
_JWKS_TS = 0
def get_jwks():
    global _JWKS, _JWKS_TS
    if (not _JWKS) or (time.time() - _JWKS_TS > 300):
        resp = requests.get(JWKS_URL, timeout=5)
        resp.raise_for_status()
        _JWKS = resp.json()
        _JWKS_TS = time.time()
    return _JWKS

def verify_token(auth_header: str):
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise ValueError("Missing or invalid Authorization header")
    token = auth_header.split(" ", 1)[1].strip()
    unverified = jwt.get_unverified_header(token)
    kid = unverified.get("kid")
    jwks = get_jwks()
    key = None
    for k in jwks.get("keys", []):
        if k.get("kid") == kid:
            key = k
            break
    if not key:
        raise ValueError("JWKS key not found for kid")
    payload = jwt.decode(
        token,
        key,
        algorithms=["RS256"],
        audience=AUDIENCE,
        issuer=ISSUER,
        options={"verify_at_hash": False},
    )
    return payload

# ---- Public Routes ----
@app.get("/hello")
def hello():
    return jsonify(message="Hello from App Server! (public)")

@app.get("/secure")
def secure():
    try:
        payload = verify_token(request.headers.get("Authorization"))
        return jsonify(
            message="Secure resource OK",
            sub=payload.get("sub"),
            preferred_username=payload.get("preferred_username"),
        )
    except Exception as e:
        return jsonify(error=str(e)), 401

# ---- Endpoint /student (Đọc từ file JSON) ----
@app.get("/student")
def student_from_json():
    """ Đọc dữ liệu sinh viên từ tệp students.json (công khai) """
    try:
        # Sử dụng đường dẫn tuyệt đối (JSON_PATH)
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        # Trả về lỗi 404 nếu tệp không tồn tại
        return jsonify(error=f"File not found at path: {JSON_PATH}"), 404
    except Exception as e:
        # Bắt các lỗi khác (ví dụ: JSON sai định dạng)
        return jsonify(error=f"An error occurred: {str(e)}"), 500


# ---- Student Database API Routes (Tiền tố /db/...) ----

@app.post("/db/students/add-student")
def create_student():
    """ (CREATE) Tạo một sinh viên mới trong DB - Tương đương INSERT """ 
    try:
        data = request.json
        if not data or 'fullname' not in data or 'student_id' not in data:
             return jsonify(error="Missing required fields: fullname, student_id"), 400
        
        new_student = Student(
            student_id=data['student_id'],
            fullname=data['fullname'],
            major=data.get('major'), # .get() cho phép trường này là optional
            dob=datetime.date.fromisoformat(data['dob']) if data.get('dob') else None
        )
        db.session.add(new_student)
        db.session.commit()
        
        return jsonify(new_student.to_dict()), 201 # 201 Created
        
    except Exception as e:
        db.session.rollback() # Hoàn tác nếu có lỗi
        return jsonify(error=f"Database error or invalid data: {str(e)}"), 500

@app.get("/db/students/get-all")
def get_all_students():
    """ (READ) Lấy TẤT CẢ sinh viên từ DB - Tương đương SELECT * """
    try:
        students = Student.query.all()
        # Chuyển đổi danh sách các object student thành list các dictionary
        return jsonify([s.to_dict() for s in students])
    except Exception as e:
        return jsonify(error=f"Database error: {str(e)}"), 500

@app.get("/db/students/get/<int:pk>")
def get_one_student(pk):
    """ (READ) Lấy MỘT sinh viên từ DB bằng ID (primary key) - Tương đương SELECT ... WHERE id=... """
    try:
        # db.session.get là cách hiện đại để lấy bằng primary key
        student = db.session.get(Student, pk) 
        if not student:
            return jsonify(error="Student not found"), 404
        return jsonify(student.to_dict())
    except Exception as e:
        return jsonify(error=f"Database error: {str(e)}"), 500

@app.post("/db/students/update/<int:pk>")
def update_student(pk):
    """ (UPDATE) Cập nhật thông tin sinh viên trong DB - Tương đương UPDATE """
    try:
        student = db.session.get(Student, pk)
        if not student:
            return jsonify(error="Student not found"), 404
        
        data = request.json
        # Cập nhật các trường nếu chúng tồn tại trong request JSON
        if 'fullname' in data:
            student.fullname = data['fullname']
        if 'major' in data:
            student.major = data['major']
        if 'student_id' in data:
            student.student_id = data['student_id']
        if 'dob' in data:
            student.dob = datetime.date.fromisoformat(data['dob']) if data.get('dob') else None
            
        db.session.commit() # Lưu thay đổi
        return jsonify(student.to_dict())
        
    except Exception as e:
        db.session.rollback()
        return jsonify(error=f"Database error or invalid data: {str(e)}"), 500

@app.post("/db/students/delete/<int:pk>")
def delete_student(pk):
    """ (DELETE) Xóa sinh viên khỏi DB - Tương đương DELETE """
    try:
        student = db.session.get(Student, pk)
        if not student:
            return jsonify(error="Student not found"), 404
            
        db.session.delete(student) # Xóa
        db.session.commit() # Lưu thay đổi
        return jsonify(message="Student deleted successfully"), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify(error=f"Database error: {str(e)}"), 500


if __name__ == "__main__":
    # Tạo các bảng nếu chúng chưa tồn tại
    # (trong môi trường production, bạn nên dùng Alembic/migrations)
    with app.app_context():
        db.create_all()
        
    # Quan trọng: lắng nghe trên 0.0.0.0:8081 để Docker publish ra được
    app.run(host="0.0.0.0", port=8081)