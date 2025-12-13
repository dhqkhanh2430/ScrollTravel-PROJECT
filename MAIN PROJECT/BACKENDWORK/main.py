import sys
import os
import re
import time
import requests
import urllib3
from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtCore import QTimer, QStringListModel, Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import QMessageBox, QCompleter

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#Import mấy cái file cần cho cái đống ở dưới
import res
import data_manager


#Hàm hỗ trợ lấy đường dẫn UI
def get_ui_path(filename):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)


#Class đổi mật khẩu
class ChangePasswordWindow(QtWidgets.QMainWindow):
    def __init__(self, username, parent=None):
        super().__init__(parent)
        try:
            uic.loadUi(get_ui_path("changePasswordWindow.ui"), self)
        except FileNotFoundError:
            print("Lỗi: Không tìm thấy changePasswordWindow.ui")

        self.current_username = username

        #Tự động dò tìm nút (fix lỗi nút không chạy)
        if hasattr(self, 'confirmChangeBtn'):
            self.confirmChangeBtn.clicked.connect(self.handle_change_password)
        elif hasattr(self, 'confirmBtn'):
            self.confirmBtn.clicked.connect(self.handle_change_password)
        elif hasattr(self, 'pushButton'):
            self.pushButton.clicked.connect(self.handle_change_password)

        if hasattr(self, 'goBackBtn'):
            self.goBackBtn.clicked.connect(self.close)
        elif hasattr(self, 'backBtn'):
            self.backBtn.clicked.connect(self.close)

    def handle_change_password(self):
        try:
            #Lấy dữ liệu an toàn
            current_pass = getattr(self, 'currentPasswordInput', None)
            new_pass = getattr(self, 'newPasswordInput', None)
            retype_new = getattr(self, 'retypeNewPasswordInput', None)

            if not current_pass: return

            curr_text = current_pass.text()
            new_text = new_pass.text()
            retype_text = retype_new.text()

            #Logic kiểm tra
            if not curr_text or not new_text:
                QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập đầy đủ!")
                return

            has_upper = any(char.isupper() for char in new_text)
            has_digit = any(char.isdigit() for char in new_text)
            has_special = any(not char.isalnum() for char in new_text)

            if len(new_text) < 6:
                QMessageBox.warning(self, "Mật khẩu yếu", "Mật khẩu phải dài hơn 6 ký tự")
                return
            if not (has_upper and has_digit and has_special):
                QMessageBox.warning(self, "Mật khẩu yếu", "Mật khẩu mới cần có chữ IN HOA, SỐ và KÝ TỰ ĐẶC BIỆT")
                return
            if new_text != retype_text:
                QMessageBox.warning(self, "Lỗi", "Mật khẩu mới xác nhận không khớp!")
                return

            #Gọi Data Manager
            if hasattr(data_manager, 'change_password'):
                success, msg = data_manager.change_password(self.current_username, curr_text, new_text)
                if success:
                    QMessageBox.information(self, "Thành công", msg)
                    self.close()
                else:
                    QMessageBox.warning(self, "Thất bại", msg)
        except Exception as e:
            QMessageBox.critical(self, "Lỗi Code", str(e))


#Class Menu
class MenuScreen(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        try:
            uic.loadUi(get_ui_path("menuPage.ui"), self)
        except FileNotFoundError:
            print("CẢNH BÁO: Không tìm thấy file menuPage.ui")

        self.current_user_data = None
        self.search_thread = None  #Biến để giữ luồng đang chạy

        # Load default posts từ database
        count = self.load_default_posts()
        if count:
            print(f"Đã load {count} bài viết lên màn hình")

        if hasattr(self, 'refreshBtn'):
            self.refreshBtn.clicked.connect(self.handle_refresh)

        if hasattr(self, 'profileBtn'):
            self.profileBtn.clicked.connect(self.goto_profile)

        #Cấu hình tìm kiếm sao cho có gõ thường, không dấu cũng hiện kết quả
        if hasattr(self, 'searchINPUT'):
            self.completer = QCompleter(self)
            self.completer.setCaseSensitivity(Qt.CaseInsensitive)
            # Quan trọng: Tắt bộ lọc mặc định để tin tưởng kết quả API trả về
            self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
            self.searchINPUT.setCompleter(self.completer)
            self.searchINPUT.textChanged.connect(self.on_search_text_changed)

        #Timer Debounce
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(300)  # Giảm xuống 300ms cho mượt
        self.search_timer.timeout.connect(self.start_api_thread)  # Gọi hàm start thread

    def load_user_info(self, user_data):
        self.current_user_data = user_data

    def goto_profile(self):
        if self.current_user_data:
            profile_window.load_user_info(self.current_user_data)
        widget.setCurrentIndex(2)

    def on_search_text_changed(self, text):
        self.search_timer.start()

    #Tạo 1 luồng xử lý riêng biệt
    #Vì trong lần test đầu tiên chạy lâu quá --> bị đứng app
    #Nên phải làm vậy
    def start_api_thread(self):
        if not hasattr(self, 'searchINPUT'): return
        keyword = self.searchINPUT.text().strip()
        #Gõ 2 ký tự là tìm được rồi
        if len(keyword) < 2: return
        print(f"Đang tìm: {keyword}...")

        #Nếu đang có luồng cũ chạy dở thì tắt nó đi để chạy cái mới
        if self.search_thread and self.search_thread.isRunning():
            self.search_thread.terminate()
            self.search_thread.wait()

        #Tạo luồng mới (Không cần API Key nữa)
        self.search_thread = provinceOpenAPI(keyword, "")
        #Kết nối tín hiệu: Khi Worker làm xong -> Gọi hàm update_suggestion_list
        self.search_thread.search_finished.connect(self.update_suggestion_list)
        #Bắt đầu chạy
        self.search_thread.start()

    def update_suggestion_list(self, suggestions):
        #Hàm này chạy khi thằng con worker lấy dữ liệu xong
        model = QStringListModel()
        model.setStringList(suggestions)
        self.completer.setModel(model)

        if suggestions:
            #Set prefix rỗng để lừa Completer hiện hết danh sách
            self.completer.setCompletionPrefix('')
            self.completer.complete()

        print(f"Đã cập nhật {len(suggestions)} gợi ý.")

    def load_default_posts(self):
        """Load và hiển thị default posts từ database"""
        try:
            # Xóa các dummy posts cũ
            if hasattr(self, 'scrollAreaWidgetContents'):
                layout = self.scrollAreaWidgetContents.layout()
                if layout:
                    # Xóa tất cả widget cũ
                    while layout.count():
                        item = layout.takeAt(0)
                        if item.widget():
                            item.widget().deleteLater()
                    
                    # Lấy dữ liệu từ database
                    posts = data_manager.get_all_default_posts()
                    # Sắp xếp theo ID giảm dần (bài mới nhất lên trên)
                    posts.sort(key=lambda x: x['id'], reverse=True)
                    
                    # Tạo widget cho mỗi bài viết
                    for post in posts:
                        post_widget = self.create_post_widget(post)
                        layout.addWidget(post_widget)
                    
                    # Thêm spacer để đẩy các posts lên trên
                    spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
                    layout.addItem(spacer)
                    
                    return len(posts)
                else:
                    print("Không tìm thấy layout")
                    return 0
            else:
                print("Không tìm thấy scrollAreaWidgetContents")
                return 0
        except Exception as e:
            print(f"Lỗi khi load default posts: {e}")
            return 0

    def handle_refresh(self):
        """Xử lý khi nhấn nút refresh"""
        count = self.load_default_posts()
        print(f"Đã refresh lại Homescreen, có tổng cộng {count} bài viết")

    def create_post_widget(self, post):
        """Tạo widget card cho một bài viết"""
        # Tạo frame chính với style giống dummy posts
        frame = QtWidgets.QFrame()
        frame.setMinimumSize(500, 200)
        frame.setMaximumSize(1920, 200)
        frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #ddd;
            }
            QFrame:hover {
                border: 2px solid #00aaff;
            }
        """)
        
        # Layout ngang: ảnh bên trái, nội dung bên phải
        h_layout = QtWidgets.QHBoxLayout(frame)
        h_layout.setContentsMargins(10, 10, 10, 10)
        h_layout.setSpacing(15)
        
        # Label hiển thị ảnh
        image_label = QtWidgets.QLabel()
        image_label.setFixedSize(250, 180)
        image_label.setScaledContents(True)
        image_label.setStyleSheet("border-radius: 10px;")
        
        # Load ảnh từ đường dẫn
        image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), post['image_path'])
        if os.path.exists(image_path):
            pixmap = QtGui.QPixmap(image_path)
            image_label.setPixmap(pixmap)
        else:
            image_label.setText("No Image")
            image_label.setStyleSheet("background-color: #f0f0f0; border-radius: 10px;")
        
        h_layout.addWidget(image_label)
        
        # Layout dọc cho tiêu đề và mô tả
        v_layout = QtWidgets.QVBoxLayout()
        v_layout.setSpacing(10)
        
        # Tiêu đề
        title_label = QtWidgets.QLabel(post['title'])
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #333;
        """)
        title_label.setWordWrap(True)
        v_layout.addWidget(title_label)
        
        # Mô tả
        desc_label = QtWidgets.QLabel(post['description'])
        desc_label.setStyleSheet("""
            font-size: 14px;
            color: #666;
            line-height: 1.5;
        """)
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        v_layout.addWidget(desc_label, 1)  # stretch = 1 để chiếm hết không gian
        
        h_layout.addLayout(v_layout, 1)
        
        return frame


# Class Worker chạy ngầm gọi API
class provinceOpenAPI(QThread):
    search_finished = pyqtSignal(list)

    def __init__(self, keyword, api_key):
        super().__init__()
        self.keyword = keyword
        #Giữ tham số api_key để code bên Menu không bị lỗi gọi hàm, dù không dùng

    def run(self):
        #Sử dụng API Hành chính Việt Nam - Nhanh và Chính xác
        url = "https://provinces.open-api.vn/api/?depth=2"

        try:
            #Verify=False để tránh lỗi SSL nếu mạng trường chặn
            response = requests.get(url, timeout=5, verify=False)

            if response.status_code == 200:
                data = response.json()
                suggestions = []
                keyword_lower = self.keyword.lower()
                count = 0

                #Logic lọc dữ liệu tỉnh thành
                for province in data:
                    if count > 15: break  # Lấy tối đa 15 kết quả

                    #Kiểm tra tên Tỉnh
                    p_name = province['name']
                    if keyword_lower in p_name.lower():
                        suggestions.append(p_name)
                        count += 1
                        continue

                        #Kiểm tra tên Quận/Huyện
                    for district in province.get('districts', []):
                        d_name = district['name']
                        if keyword_lower in d_name.lower():
                            full_name = f"{d_name}, {p_name}"
                            suggestions.append(full_name)
                            count += 1
                            if count > 15: break

                self.search_finished.emit(suggestions)
            else:
                print(f"Lỗi API: {response.status_code}")
        except Exception as e:
            print(f"Lỗi mạng: {e}")

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
        self.change_pass_dialog = None

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
        self.editBtn.setText("Chỉnh sửa thông tin")
        self.set_fields_readonly(True)

    def go_back(self):
        # Quay về trang Menu (Index 3)
        widget.setCurrentIndex(3)

    #Hàm chỉnh sưa thông tin
    def set_fields_readonly(self, state):
        if hasattr(self, 'emailEdit'): self.emailEdit.setReadOnly(state)
        if hasattr(self, 'phoneEdit'): self.phoneEdit.setReadOnly(state)

        if hasattr(self, 'usernameEdit'): self.usernameEdit.setReadOnly(True)
        # Cập nhật style cho người dùng nhận biết
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
                self.editBtn.setText("Chỉnh sửa thông tin")
                self.set_fields_readonly(True)
            else:
                QMessageBox.critical(self, "Lỗi", msg)

    def logout(self):
        reply = QMessageBox.question(self, "Xác nhận đăng xuất", "Bạn có muốn đăng xuất khỏi tài khoản không?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            widget.setCurrentIndex(0)  # Quay về Login
        else:
            pass  # giữ nguyên không làm gì

    def change_password(self):
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

        try:
            self.loginBt.clicked.connect(self.handle_login)
        except AttributeError:
            print("Không có nút loginBt")

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
            #đúng thì chuyển sang index 3 (MENU PAGE)
            menu_window.load_user_info(user_data)  #Gửi dữ liệu cho Menu cầm
            widget.setCurrentIndex(3)
        else:
            #Sai thì thông báo lỗi
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
            user = self.usernameINPUT.text().strip()
            pwd = self.passwordINPUT.text()
            retype = self.retypePasswordInput.text()
            email = self.emailINPUT.text()
            phone = self.phoneINPUT.text()
            #Yêu cầu mẫu
            email_valid = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$'  # Định dạng email tiêu chuẩn
            #Định dạng mật khẩu tiêu chuẩn (phải có chữ in hoa
            #số và ký tự đặc biệt
            has_upper = any(char.isupper() for char in pwd)
            has_digit = any(char.isdigit() for char in pwd)
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

    #Khởi tạo 4 màn hình (THÊM MENU)
    login_window = LoginScreen()  # Index 0
    register_window = RegisterScreen()  # Index 1
    profile_window = ProfileScreen()  # Index 2
    menu_window = MenuScreen()  # Index 3

    #Thêm vào Stack
    widget.addWidget(login_window)
    widget.addWidget(register_window)
    widget.addWidget(profile_window)
    widget.addWidget(menu_window)

    #Cấu hình cửa sổ
    widget.resize(860, 540)
    widget.setMinimumSize(500, 700)
    widget.show()

    try:
        sys.exit(app.exec_())
    except Exception as e:
        print("Thoát chương trình:", e)