import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "users.db")

print(f"--- DEBUG: Database SQLite sẽ được lưu tại: {DB_NAME} ---")


def get_connection():
    """Tạo kết nối đến database SQLite"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row 
    return conn


def initialize_database():
    """Tạo bảng users nếu chưa tồn tại"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                phone TEXT,
                email TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        print("--- DEBUG: Database đã sẵn sàng ---")
    except Exception as e:
        print(f"--- LỖI: Không thể khởi tạo database: {e} ---")


# Khởi tạo database khi module được import
initialize_database()


def register_user(username, password, phone, email):
    """Đăng ký user mới"""
    #Kiểm tra xem tài khoản đã tồn tại chưa
    if check_user_exist(username):
        return False, "Tên đăng nhập đã tồn tại!"

    #Lưu user mới vào database
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password, phone, email) VALUES (?, ?, ?, ?)",
            (username, password, phone, email)
        )
        conn.commit()
        conn.close()
        return True, "Đăng ký thành công!"
    except sqlite3.IntegrityError:
        return False, "Tên đăng nhập đã tồn tại!"
    except Exception as e:
        return False, f"Lỗi ghi database: {e}"


def check_user_exist(username):
    """Kiểm tra username đã tồn tại chưa"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    except Exception as e:
        print(f"--- LỖI check_user_exist: {e} ---")
        return False


def check_login(username, password):
    """Kiểm tra đăng nhập"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE username = ?", 
            (username,)
        )
        user = cursor.fetchone()
        conn.close()
        
        if user is None:
            return None, "Tài khoản không tồn tại!"
        
        # So sánh password
        if user["password"] == password:
            user_dict = {
                "Username": user["username"],
                "Password": user["password"],
                "Phone": user["phone"],
                "Email": user["email"]
            }
            return user_dict, "Đăng nhập thành công!"
        else:
            return None, "Sai mật khẩu!"
            
    except Exception as e:
        return None, f"Lỗi đọc dữ liệu: {e}"


def update_user_info(current_username, new_phone, new_email):
    """Cập nhật thông tin user"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Kiểm tra user có tồn tại không
        cursor.execute("SELECT username FROM users WHERE username = ?", (current_username,))
        if cursor.fetchone() is None:
            conn.close()
            return False, "Không tìm thấy user để update"
        
        # Update thông tin
        cursor.execute(
            "UPDATE users SET phone = ?, email = ? WHERE username = ?",
            (new_phone, new_email, current_username)
        )
        conn.commit()
        conn.close()
        return True, "Cập nhật thành công!"
        
    except Exception as e:
        return False, f"Lỗi khi update: {e}"


def change_password(username, current_password, new_password):
    """Đổi mật khẩu"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Lấy thông tin user
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        if user is None:
            conn.close()
            return False, "Không tìm thấy người dùng!"
        
        # Kiểm tra mật khẩu cũ có đúng không
        if user["password"] != current_password:
            conn.close()
            return False, "Mật khẩu hiện tại không đúng!"
        
        # Update mật khẩu mới
        cursor.execute(
            "UPDATE users SET password = ? WHERE username = ?",
            (new_password, username)
        )
        conn.commit()
        conn.close()
        return True, "Đổi mật khẩu thành công!"
        
    except Exception as e:
        return False, f"Lỗi hệ thống: {e}"