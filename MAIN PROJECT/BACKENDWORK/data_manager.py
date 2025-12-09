import csv
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_NAME = os.path.join(BASE_DIR, "users.csv")

print(f"--- DEBUG: File CSV sẽ được lưu tại: {FILE_NAME} ---")


def ensure_file_exists():
    """Đảm bảo file CSV tồn tại và có tiêu đề"""
    if not os.path.exists(FILE_NAME):
        try:
            with open(FILE_NAME, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Username", "Password", "Phone", "Email"])
            print("--- DEBUG: Đã tạo mới file users.csv ---")
        except Exception as e:
            print(f"--- LỖI: Không thể tạo file CSV: {e} ---")


def register_user(username, password, phone, email):
    ensure_file_exists()  #Chạy kiểm tra file trước

    #Kiểm tra xem tài khoản đã tồn tại chưa
    if check_user_exist(username):
        return False, "Tên đăng nhập đã tồn tại!"

    #Lưu dòng mới (tạo luôn file nếu chưa có)
    try:
        with open(FILE_NAME, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([username, password, phone, email])
        return True, "Đăng ký thành công!"
    except Exception as e:
        return False, f"Lỗi ghi file: {e}"


def check_user_exist(username):
    #Tên đăng nhập mà trùng với tài khoản khác là cho nó skbidi toilet 67 rizz luôn (cook:]])
    if not os.path.exists(FILE_NAME): return False

    try:
        with open(FILE_NAME, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["Username"] == username:
                    return True
    except:
        return False
    return False


#Logic đăng nhập
def check_login(username, password):
    #Kiểm tra đăng nhập coi có đúng không
    if not os.path.exists(FILE_NAME):
        return None, "Chưa có tài khoản nào được đăng ký!"

    try:
        with open(FILE_NAME, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["Username"] == username:
                    # So sánh password
                    if row["Password"] == password:
                        return row, "Đăng nhập thành công!"
                    else:
                        return None, "Sai mật khẩu!"

            return None, "Tài khoản không tồn tại!"
    except Exception as e:
        return None, f"Lỗi đọc dữ liệu: {e}"


def update_user_info(current_username, new_phone, new_email):
    if not os.path.exists(FILE_NAME): return False, "Không tìm thấy file data"

    updated = False
    all_rows = []
    fieldnames = ["Username", "Password", "Phone", "Email"]
    #Kiểm tra xem có sự thay đổi thông tin không
    #Có thì sửa, không thì thôi
    try:
        with open(FILE_NAME, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["Username"] == current_username:
                    row["Phone"] = new_phone
                    row["Email"] = new_email
                    updated = True
                all_rows.append(row)

        if updated:
            with open(FILE_NAME, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_rows)
            return True, "Cập nhật thành công!"
        else:
            return False, "Không tìm thấy user để update"

    except Exception as e:
        return False, f"Lỗi khi update: {e}"

def change_password(username, current_password, new_password):
    if not os.path.exists(FILE_NAME): return False, "Lỗi dữ liệu"
    updated = False
    all_rows = []
    fieldnames = ["Username", "Password", "Phone", "Email"]

    try:
        with open(FILE_NAME, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["Username"] == username:
                    #Kiểm tra mật khẩu cũ có đúng không
                    if row["Password"] == current_password:
                        row["Password"] = new_password
                        updated = True
                    else:
                        return False, "Mật khẩu hiện tại không đúng!"
                all_rows.append(row)

        if updated:
            with open(FILE_NAME, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_rows)
            return True, "Đổi mật khẩu thành công!"
        else:
            return False, "Không tìm thấy người dùng!"

    except Exception as e:
        return False, f"Lỗi hệ thống: {e}"