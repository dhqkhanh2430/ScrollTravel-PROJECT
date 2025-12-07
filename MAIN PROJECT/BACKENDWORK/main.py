import sys
import os
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox

#Import mấy cái file cần cho cái đống ở dưới
import res
import data_manager


#Hàm hỗ trợ lấy đường dẫn UI
def get_ui_path(filename):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)


#Class Menu (chưa có gì)
class MenuScreen(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        try:
            uic.loadUi(get_ui_path("menuPage.ui"), self)
        except FileNotFoundError:
            print("CẢNH BÁO: Không tìm thấy file menuPage.ui. Hãy tạo nó trong Qt Designer!")

    def logout(self):
        widget.setCurrentIndex(0) #Quay về Login


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
        success, message = data_manager.check_login(user, pwd)

        if success:
            #đúng thì chuyển sang index 2 (menu)
            widget.setCurrentIndex(2)
        else:
            #Sai th thông báo lỗi
            QMessageBox.warning(self, "Đăng nhập thất bại", message)

    def goto_register(self):
        #Nút nhảy sang màn hình đăng ký (cái hyper link "here")
        widget.setCurrentIndex(1)


#Claas Register
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
            user = self.usernameINPUT.text()
            pwd = self.passwordINPUT.text()
            retype = self.retypePasswordInput.text()
            email = self.emailINPUT.text()
            phone = self.phoneINPUT.text()

            #Logic kiểm tra
            if not user or not pwd or not email:
                QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhập đủ thông tin!")
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
    login_window = LoginScreen()  #Index 0
    register_window = RegisterScreen()  #Index 1
    menu_window = MenuScreen()  #Index 2

    #Thêm vào Stack
    widget.addWidget(login_window)
    widget.addWidget(register_window)
    widget.addWidget(menu_window)

    #Cấu hình cửa sổ
    widget.resize(860, 540)
    widget.setMinimumSize(500, 700)
    widget.show()

    try:
        sys.exit(app.exec_())
    except Exception as e:
        print("Thoát chương trình:", e)
        