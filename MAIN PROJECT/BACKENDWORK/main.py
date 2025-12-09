import sys
import os
import re
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox

#Import mấy cái file cần cho cái đống ở dưới
import res
import data_manager


#Hàm hỗ trợ lấy đường dẫn UI
def get_ui_path(filename):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

#Class Đổi mật khẩu
class ChangePasswordWindow(QtWidgets.QMainWindow):
    def __init__(self, username, parent=None):
        super().__init__(parent)  #parent giúp cửa sổ này luôn nằm trên cửa sổ cha
        try:
            uic.loadUi(get_ui_path("changePasswordWindow.ui"), self)
        except FileNotFoundError:
            print("Lỗi: Không tìm thấy changePasswordWindow.ui")

        self.current_username = username

        #Kết nối nút Xác nhận (Check tên nút trong Qt Designer nhé)
        if hasattr(self, 'confirmChangeBtn'):
            self.confirmChangeBtn.clicked.connect(self.handle_change_password)

        #Kết nối nút Quay về
        if hasattr(self, 'goBackBtn'):
            self.goBackBtn.clicked.connect(self.close)

    def handle_change_password(self):
        try:
            current_pass = self.currentPasswordInput.text()
            new_pass = self.newPasswordInput.text()
            retype_new = self.retypeNewPasswordInput.text()

            has_upper = any(char.isupper() for char in new_pass)
            has_digit = any(char.isdigit() for char in new_pass)
            has_special = any(not char.isalnum() for char in new_pass)

            if not current_pass or not new_pass:
                QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập đầy đủ!")
                return
            if not (has_upper and has_digit and has_special):
                QMessageBox.warning(self, "Lỗi", "Mật khẩu mới không đúng định dạng")
                return
            if len(new_pass) < 6:
                QMessageBox.warning(self, "Lỗi", "Mật khẩu mới không đúng định dạng")
                return

            if new_pass != retype_new:
                QMessageBox.warning(self, "Lỗi", "Mật khẩu mới xác nhận không khớp!")
                return


            #Gọi hàm xử lý trong data_manager
            success, msg = data_manager.change_password(self.current_username, current_pass, new_pass)

            if success:
                QMessageBox.information(self, "Thành công", msg)
                self.close()
            else:
                QMessageBox.warning(self, "Thất bại", msg)
        except AttributeError:
            QMessageBox.critical(self, "Lỗi UI", "Sai tên ô nhập liệu trong changePasswordWindow")

#Class Profile
class ProfileScreen(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        try:
            uic.loadUi(get_ui_path("profilePage.ui"), self)
        except FileNotFoundError:
            print("CẢNH BÁO: Không tìm thấy file profilePage.ui. Hãy tạo nó trong Qt Designer!")

        self.is_editing = False
        self.current_username = ""

        try:
            self.editBtn.clicked.connect(self.toggle_edit_mode)
        except AttributeError:
            print("Lỗi UI: Không tìm thấy nút 'editBtn'")

        try:
            self.changePasswordBtn.clicked.connect(self.change_password)
        except AttributeError:
            print("Lỗi UI: Không tìm thấy nút 'editBtn'")

        try:
            self.logOutBtn.clicked.connect(self.logout)
        except AttributeError:
            print("Lỗi UI: Không tìm thấy nút 'logOutBtn'")

        try:
            self.goBackBtn.clicked.connect(self.go_back)
        except AttributeError:
            print("Lỗi UI: Không tìm thấy nút 'goBackBtn'")

        self.set_fields_readonly(True)

    def load_user_info(self, user_data):
        self.current_username = user_data.get("Username", "")

        if hasattr(self, 'usernameEdit'):
            self.usernameEdit.setText(self.current_username)
            self.usernameEdit.setReadOnly(True)

        if hasattr(self, 'emailEdit'):
            self.emailEdit.setText(user_data.get("Email", ""))

        if hasattr(self, 'phoneEdit'):
            self.phoneEdit.setText(user_data.get("Phone", ""))

        self.is_editing = False
        self.set_fields_readonly(True)
    def go_back(selfs):
        widget.setCurrentIndex(0)

    #Hàm chỉnh sưa thông tin
    def set_fields_readonly(self, state):
        if hasattr(self, 'emailEdit'): self.emailEdit.setReadOnly(state)
        if hasattr(self, 'phoneEdit'): self.phoneEdit.setReadOnly(state)

        if hasattr(self, 'usernameEdit'): self.usernameEdit.setReadOnly(True)
        #Cập nhật style cho người dùng nhận biết
        if state:
            style = """
                QLineEdit {
                    background-color: white;
                    border: 1px solid #cccccc;
                    border-radius: 10px;
                    color: black;
                    padding-left: 10px;
                }
            """
        else:
            style = """
                QLineEdit {
                    background-color: #e0e0e0;
                    border: 2px solid #00aaff;
                    border-radius: 10px;
                    color: black;
                    padding-left: 10px;
                }
            """

        if hasattr(self, 'emailEdit'): self.emailEdit.setStyleSheet(style)
        if hasattr(self, 'phoneEdit'): self.phoneEdit.setStyleSheet(style)

        if hasattr(self, 'usernameEdit'):
            self.usernameEdit.setStyleSheet("""
                QLineEdit {
                    background-color: #f0f0f0;
                    border: 1px solid #cccccc; 
                    border-radius: 10px;
                    color: #555555;
                    padding-left: 10px;
                }
            """)

    def toggle_edit_mode(self):
        if not self.is_editing:
            self.is_editing = True
            self.editBtn.setText("Lưu thay đổi")
            self.set_fields_readonly(False)

            if hasattr(self, 'phoneEdit'): self.phoneEdit.setFocus()

        else:
            new_phone = self.phoneEdit.text()
            new_email = self.emailEdit.text()

            success, msg = data_manager.update_user_info(self.current_username, new_phone, new_email)

            if success:
                QMessageBox.information(self, "Thành công", msg)
                self.is_editing = False
                self.editBtn.setText("Chỉnh sửa")
                self.set_fields_readonly(True)
            else:
                QMessageBox.critical(self, "Lỗi", msg)

    def logout(self):
        reply = QMessageBox.question(self, "Xác nhận đăng xuất", "Bạn có muốn đăng xuất khỏi tài khoản không?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            widget.setCurrentIndex(0)  #Quay về Login
        else:
            pass #giữ nguyên không làm gì

    def change_password(self, password):
        self.change_pass_dialog = ChangePasswordWindow(self.current_username, self)
        self.change_pass_dialog.show()



#Class Login
class LoginScreen(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        try:
            uic.loadUi(get_ui_path("loginPage.ui"), self)
        except FileNotFoundError:
            print("Lỗi: Không tìm thấy file loginPage.ui!")

        #Nút để nhảy qua trang đăng ký
        try:
            self.toRegisterBt.clicked.connect(self.goto_register)
        except AttributeError:
            print("Lỗi UI: Không tìm thấy nút 'toRegisterBt' để chuyển trang.")
        self.loginBt.clicked.connect(self.handle_login)

        try:
            if hasattr(self, 'showPasswordBt'):
                self.showPasswordBt.clicked.connect(self.toggle_password)
        except AttributeError:
            print("Chưa có nút showPasswordBt")

    def toggle_password(self):
        try:
            if self.password.echoMode() == QtWidgets.QLineEdit.Password:
                self.password.setEchoMode(QtWidgets.QLineEdit.Normal)
                self.showPasswordBt.setText("👁")
            else:
                self.password.setEchoMode(QtWidgets.QLineEdit.Password)
                self.showPasswordBt.setText("🙈")
        except AttributeError:
            pass

    def handle_login(self):
        #B1 Lấy dữ liệu từ 2 ô nhập
        try:
            user = self.username.text()
            pwd = self.password.text()
        except AttributeError:
            QMessageBox.critical(self, "Lỗi")
            return

        #B2 Kiểm tra tài khoản và mật khẩu
        if not user or not pwd:
            QMessageBox.warning(self, "Thông báo", "Vui lòng nhập đầy đủ tên và mật khẩu!")
            return

        #Đưa vào data_manager để kiểm tra
        #Hàm checkLogin sẽ kiểm tra và trả về true hoặc false
        user_data, message = data_manager.check_login(user, pwd)

        if user_data:
            #đúng thì chuyển sang index 2 (menu)
            profile_window.load_user_info(user_data)
            widget.setCurrentIndex(2)
        else:
            #Sai thì thông báo lỗi
            QMessageBox.warning(self, "Đăng nhập thất bại", message)

    def goto_register(self):
        #Nút nhảy sang màn hình đăng ký (cái hyper link "here")
        widget.setCurrentIndex(1)


# Claas Register
class RegisterScreen(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        try:
            uic.loadUi(get_ui_path("registerPage.ui"), self)
        except FileNotFoundError:
            print("Lỗi: Không tìm thấy file registerPage.ui")

        #Nút đăng ký
        self.registerBUTTON.clicked.connect(self.handle_registration)
        #Nút quay lại trang login
        try:
            self.toLoginBt.clicked.connect(self.goto_login)
        except AttributeError:
            print("Lỗi UI: Không tìm thấy nút quay lại 'toLoginBt'.")

    def handle_registration(self):
        try:
            user = self.usernameINPUT.text().strip()
            pwd = self.passwordINPUT.text()
            retype = self.retypePasswordInput.text()
            email = self.emailINPUT.text()
            phone = self.phoneINPUT.text()

            #Yêu cầu mẫu
            email_valid = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$' #Định dạng email tiêu chuẩn
            #Định dạng mật khẩu tiêu chuẩn (phải có chữ in hoa
            #số và ký tự đặc biệt
            has_upper  = any(char.isupper() for char in pwd)
            has_digit  = any(char.isdigit() for char in pwd)
            has_special = any(not char.isalnum() for char in pwd)

            #Logic kiểm tra

            #Kiểm tra xem có để trống không
            if not user or not pwd or not email:
                QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhập đủ thông tin!")
                return
            #Kiểm tra số điện thoại xem có hợp lệ không
            if not phone.isdigit():
                QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đúng định dạng số điện thoại!")
                return
            if len(phone) < 9 or (len(phone) > 11):
                QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đúng định dạng số điện thoại!")
                return
            #Kiểm tra xem email có đúng định dạng không
            if not re.match(email_valid, email):
                QMessageBox.warning(self, "Lỗi", "Email không đúng định dạng!")
                return
            #Kiểm tra xem mật khẩu có mạnh không
            if len(pwd) < 6:
                QMessageBox.warning(self, "Lỗi", "Mật khẩu phải dài hơn 6 ký tự")
                return
            if not (has_upper and has_digit and has_special):
                QMessageBox.warning(self, "Lỗi", "Mật khẩu không đúng định dạng")
                return
            if pwd != retype:
                QMessageBox.warning(self, "Lỗi", "Mật khẩu xác nhận không trùng khớp!")
                return

            #Lưu vào file CSV
            success, message = data_manager.register_user(user, pwd, phone, email)

            if success:
                QMessageBox.information(self, "Thành công", message)
                self.goto_login()
            else:
                QMessageBox.critical(self, "Lỗi", message)

        except Exception as e:
            print(f"Lỗi logic Register: {e}")
            QMessageBox.critical(self, "Lỗi Code", str(e))

    def goto_login(self):
        widget.setCurrentIndex(0)


#Chương trình chính để khởi tạo index, khởi tạo object, căn chỉnh cửa sổ vân vân mây mây
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    #Tạo Stack chứa các màn hình
    widget = QtWidgets.QStackedWidget()

    #Khởi tạo 3 màn hình
    login_window = LoginScreen()  # Index 0
    register_window = RegisterScreen()  # Index 1
    profile_window = ProfileScreen()  # Index 2

    #Thêm vào Stack
    widget.addWidget(login_window)
    widget.addWidget(register_window)
    widget.addWidget(profile_window)

    #Cấu hình cửa sổ
    widget.resize(860, 540)
    widget.setMinimumSize(500, 700)
    widget.show()

    try:
        sys.exit(app.exec_())
    except Exception as e:
        print("Thoát chương trình:", e)