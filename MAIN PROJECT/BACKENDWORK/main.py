import sys
import os
import re
import time
import requests
import urllib3
import shutil
import datetime
import copy
from PyQt5 import QtWidgets, uic, QtGui, QtCore
from PyQt5.QtCore import QTimer, QStringListModel, Qt, QThread, pyqtSignal
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve, QEvent, QSize
from PyQt5.QtWidgets import QMessageBox, QCompleter, QVBoxLayout, QPushButton
from PyQt5.QtGui import QPixmap


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#Import mấy cái file cần cho cái đống ở dưới
import res
import data_manager
from webmap import MapWidget
from RandomImage import random_qpixmap, random_image_path
from APIcall_Places import getPlaces
from Categories_Input import Cate, SetCategories
from Input_Classify import classify_location
from add_favorite_places import add_favorite_place


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
        
        if hasattr(self, 'favoriteBtn'):
            self.favoriteBtn.clicked.connect(self.goto_favorite)

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
        self.search_timer.setInterval(300)
        self.search_timer.timeout.connect(self.start_api_thread)  #Gọi hàm start thread

        if hasattr(self, 'filterContainer'):
            #1. Ẩn container đi lúc đầu
            self.filterContainer.setMinimumHeight(0)
            self.filterContainer.setMaximumHeight(0)
            #2. Chỉnh chiều cao bung ra
            self.target_filter_height = 250

        if hasattr(self, 'filterBtn'):
            #Đảm bảo code hiểu đây là nút checkable (dù Designer chỉnh rồi thì thêm dòng này cho chắc)
            self.filterBtn.setCheckable(True)
            #Nếu nút đang lún xuống thì nhả nó ra (để đồng bộ với việc container đang đóng)
            self.filterBtn.setChecked(False)
            #Kết nối sự kiện "toggled" (bật/tắt) thay vì "clicked"
            self.filterBtn.toggled.connect(self.handle_filter_toggle)

        # Lấy danh sách category để pass qua searchResults
        self.init_temp_filters()
        self.connect_filter_buttons()
        if hasattr(self, 'searchBtn'):
            self.searchBtn.clicked.connect(self.goto_results)


    def init_temp_filters(self):
        self.temp_filters = copy.deepcopy(Cate)

    def update_temp_filter(self, group, name, checked):
        self.temp_filters[group][name] = checked

    def connect_filter_buttons(self):
        # Entertainment
        self.aquariumBtn.toggled.connect(lambda checked: self.update_temp_filter("Entertainment", "Aquarium", checked))
        self.cinemaBtn.toggled.connect(lambda checked: self.update_temp_filter("Entertainment", "Cinema", checked))
        self.cultureBtn.toggled.connect(lambda checked: self.update_temp_filter("Entertainment", "Culture", checked))
        self.themeParkBtn.toggled.connect(lambda checked: self.update_temp_filter("Entertainment", "Theme_Park", checked))
        self.waterParkBtn.toggled.connect(lambda checked: self.update_temp_filter("Entertainment", "Water_Park", checked))
        self.zooBtn.toggled.connect(lambda checked: self.update_temp_filter("Entertainment", "Zoo", checked))
        # Catering
        self.restaurantBtn.toggled.connect(lambda checked: self.update_temp_filter("Catering", "Restaurant", checked))
        self.cafeBtn.toggled.connect(lambda checked: self.update_temp_filter("Catering", "Cafe", checked))
        self.barBtn.toggled.connect(lambda checked: self.update_temp_filter("Catering", "Bar", checked))
        # Accommodation
        self.hotelBtn.toggled.connect(lambda checked: self.update_temp_filter("Accommodation", "Hotel", checked))
        self.motelBtn.toggled.connect(lambda checked: self.update_temp_filter("Accommodation", "Motel", checked))
        # Commercial
        self.supermarketBtn.toggled.connect(lambda checked: self.update_temp_filter("Commercial", "Supermarket", checked))

    def reset_filters(self):
        self.temp_filters = copy.deepcopy(Cate)

        for btn in [
            self.aquariumBtn, self.cinemaBtn, self.cultureBtn,
            self.themeParkBtn, self.waterParkBtn, self.zooBtn,
            self.restaurantBtn, self.cafeBtn, self.barBtn,
            self.hotelBtn, self.motelBtn, self.supermarketBtn
        ]:
            btn.blockSignals(True)
            btn.setChecked(False)
            btn.blockSignals(False)
        
    def goto_results(self):
        if self.current_user_data:
            try:
                username = self.current_user_data.get('Username', '')

                cateInput = SetCategories(self.temp_filters)
                if not cateInput:
                    #Gán mặc định là hotel
                    cateInput = "accommodation.hotel"
                    print("Người dùng không chọn gì -> Mặc định tìm Hotel")
                if cateInput == []:
                    QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn loại hình du lịch")
                    return

                locInput = self.searchINPUT.text().strip()
                if not locInput:
                    QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhập tên thành phố")
                    return
                addr, loc_type, coords = classify_location(locInput)

                if not coords:
                    QMessageBox.warning(self, "Không tìm thấy",
                                        f"Không tìm thấy địa điểm: {locInput}\nVui lòng kiểm tra lại chính tả.")
                    return

                if isinstance(coords, tuple):
                    lat = coords[0]
                    lon = coords[1]
                else:
                    #Phòng trường hợp nó trả về object thật (geopy location)
                    lat = coords.latitude
                    lon = coords.longitude

                radius = "20000"
                result = getPlaces(lat, lon, radius, cateInput)

                if isinstance(result, str):
                    QMessageBox.warning(self, "Thông báo từ API", result)
                    return

                #Debug: Kiểm tra xem ds có rỗng không
                if not result:
                    QMessageBox.information(self, "Thông báo", "Không tìm thấy địa điểm nào phù hợp!")
                    return

                searchResults_window.loadData(username, result)
                widget.setCurrentIndex(5)
                
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể hiển thị kết quả: {e}")
        else:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng đăng nhập trước!")

    def load_user_info(self, user_data):
        self.current_user_data = user_data
        self.load_default_posts()

    def goto_profile(self):
        if self.current_user_data:
            profile_window.load_user_info(self.current_user_data)
        widget.setCurrentIndex(2)
    
    def goto_favorite(self):
        """Chuyển sang màn hình địa điểm yêu thích"""
        if self.current_user_data:
            try:
                username = self.current_user_data.get('Username', '')
                favorite_window.load_favorites(username)
                widget.setCurrentIndex(4)
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể mở trang yêu thích: {e}")
        else:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng đăng nhập trước!")

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

    #Tạo bài viết
    def create_post_widget(self, post):
        #Tạo frame chính
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

        #Layout ngang chính
        h_layout = QtWidgets.QHBoxLayout(frame)
        h_layout.setContentsMargins(10, 10, 10, 10)
        h_layout.setSpacing(15)

        #Phần ảnh
        image_label = QtWidgets.QLabel()
        image_label.setFixedSize(250, 180)
        image_label.setScaledContents(True)
        image_label.setStyleSheet("border-radius: 10px;")

        #Xử lý đường dẫn ảnh
        #DB lưu dạng: ../ASSETS/picForDefaultPost/abc.jpg
        #Cần chuyển thành đường dẫn tuyệt đối để hiển thị
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            #post['image_path'] là ../ASSETS... nên dùng os.path.join sẽ tự lùi thư mục
            rel_path = post['image_path']
            image_abs_path = os.path.abspath(os.path.join(base_dir, rel_path))

            if os.path.exists(image_abs_path):
                pixmap = QtGui.QPixmap(image_abs_path)
                image_label.setPixmap(pixmap)
            else:
                image_label.setText("No Image")
                image_label.setStyleSheet("background-color: #f0f0f0; border-radius: 10px; color: gray;")
        except Exception:
            image_label.setText("Error Image")

        h_layout.addWidget(image_label)

        #Layout phần nội dung
        v_layout = QtWidgets.QVBoxLayout()
        v_layout.setSpacing(5)

        #Tiêu đề
        title_label = QtWidgets.QLabel(post['title'])
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333; border: none;")
        title_label.setWordWrap(True)
        v_layout.addWidget(title_label)

        #Mô tả
        desc_label = QtWidgets.QLabel(post['description'])
        desc_label.setStyleSheet("font-size: 14px; color: #666; border: none;")
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        v_layout.addWidget(desc_label, 1)  # Stretch 1 để đẩy các thành phần khác

        h_layout.addLayout(v_layout, 1)

        #Nút xóa (chỉ dành cho admin thấy)
        #Kiểm tra xem người dùng hiện tại có phải admin không
        is_admin = False
        if self.current_user_data and self.current_user_data.get('Username') == 'admin':
            is_admin = True

        if is_admin:
            #Tạo một layout dọc nhỏ bên phải để chứa nút xóa
            btn_layout = QtWidgets.QVBoxLayout()
            btn_layout.setAlignment(Qt.AlignTop)

            delete_btn = QtWidgets.QPushButton("X")
            delete_btn.setFixedSize(30, 30)
            delete_btn.setCursor(Qt.PointingHandCursor)
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ff4d4d;
                    color: white;
                    font-weight: bold;
                    border-radius: 15px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #ff0000;
                }
            """)
            #Quan trọng: Dùng lambda để truyền ID vài hàm xử lý
            #post['id'] là ID trong database
            #post['image_path'] truyền vào để tí nữa xóa file
            delete_btn.clicked.connect(lambda: self.handle_delete_post(post['id'], post['image_path']))

            btn_layout.addWidget(delete_btn)
            h_layout.addLayout(btn_layout)

        return frame
    #Xóa bài viết
    def handle_delete_post(self, post_id, image_rel_path):
        #1. Hỏi xác nhận
        reply = QMessageBox.question(
            self, "Xác nhận xóa",
            "Bạn có chắc chắn muốn xóa bài viết này không?\nHành động này không thể hoàn tác.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            #2. Xóa trong Database
            success, msg = data_manager.delete_default_post(post_id)

            if success:
                #3. Xóa file ảnh (Dọn rác)
                try:
                    base_dir = os.path.dirname(os.path.abspath(__file__))
                    image_abs_path = os.path.abspath(os.path.join(base_dir, image_rel_path))

                    if os.path.exists(image_abs_path):
                        os.remove(image_abs_path)  # Lệnh xóa file của hệ điều hành
                        print(f"Đã xóa file ảnh: {image_abs_path}")
                except Exception as e:
                    print(f"Cảnh báo: Không xóa được file ảnh: {e}")

                #4. Refresh lại giao diện
                QMessageBox.information(self, "Thành công", msg)
                self.load_default_posts()  #Load lại danh sách
            else:
                QMessageBox.critical(self, "Lỗi", msg)
    #Xử lý đóng mở filter
    def handle_filter_toggle(self, checked):
        if not hasattr(self, 'filterContainer'): return

        #Tạo hiệu ứng Animation cho mượt
        self.anim = QPropertyAnimation(self.filterContainer, b"maximumHeight")
        self.anim.setDuration(300)
        self.anim.setEasingCurve(QEasingCurve.InOutQuad)

        if checked:
            #Nếu nút BẬT -> Mở ra đến chiều cao đã định
            self.anim.setStartValue(0)
            self.anim.setEndValue(self.target_filter_height)
        else:
            #Nếu nút TẮT -> Thu về 0
            self.anim.setStartValue(self.target_filter_height)
            self.anim.setEndValue(0)

        self.anim.start()


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
# Class Profile (Đã cập nhật Admin)
class ProfileScreen(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        try:
            uic.loadUi(get_ui_path("profilePage.ui"), self)
        except FileNotFoundError:
            print("CẢNH BÁO: Không tìm thấy file profilePage.ui")

        self.is_editing = False
        self.current_username = ""
        self.change_pass_dialog = None

        #Logic admin, phải là admin mới được đăng bài
        if hasattr(self, 'postBtn'):
            self.postBtn.hide()
            self.postBtn.clicked.connect(self.open_post_dialog)

        try:
            self.editBtn.clicked.connect(self.toggle_edit_mode)
        except AttributeError:
            pass

        try:
            self.changePasswordBtn.clicked.connect(self.change_password)
        except AttributeError:
            pass

        try:
            self.logOutBtn.clicked.connect(self.logout)
        except AttributeError:
            pass

        try:
            self.goBackBtn.clicked.connect(self.go_back)
        except AttributeError:
            pass

        self.set_fields_readonly(True)

    def load_user_info(self, user_data):
        self.current_username = user_data.get("Username", "")

        #Kiểm tra có phải admin
        if hasattr(self, 'postBtn'):
            if self.current_username == "admin":
                self.postBtn.show()  #Hiện nút nếu là admin
            else:
                self.postBtn.hide()  #Ẩn nút nếu là user thường

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

    def open_post_dialog(self):
        dialog = PostDialog(self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            #Nếu đăng thành công -> Refresh Menu ngay lập tức
            if 'menu_window' in globals():
                menu_window.handle_refresh()
                widget.setCurrentIndex(3)  #Chuyển về trang chủ để xem bài mới

    def go_back(self):
        widget.setCurrentIndex(3)

    def set_fields_readonly(self, state):
        if hasattr(self, 'emailEdit'): self.emailEdit.setReadOnly(state)
        if hasattr(self, 'phoneEdit'): self.phoneEdit.setReadOnly(state)
        if hasattr(self, 'usernameEdit'): self.usernameEdit.setReadOnly(True)

        if state:
            style = "QLineEdit { background-color: white; border: 1px solid #cccccc; border-radius: 10px; color: black; padding-left: 10px; }"
        else:
            style = "QLineEdit { background-color: #e0e0e0; border: 2px solid #00aaff; border-radius: 10px; color: black; padding-left: 10px; }"

        if hasattr(self, 'emailEdit'): self.emailEdit.setStyleSheet(style)
        if hasattr(self, 'phoneEdit'): self.phoneEdit.setStyleSheet(style)
        if hasattr(self, 'usernameEdit'):
            self.usernameEdit.setStyleSheet(
                "QLineEdit { background-color: #f0f0f0; border: 1px solid #cccccc; border-radius: 10px; color: #555555; padding-left: 10px; }")

    def toggle_edit_mode(self):
        if not self.is_editing:
            self.is_editing = True
            self.editBtn.setText("Lưu thay đổi")
            self.set_fields_readonly(False)
            if hasattr(self, 'phoneEdit'): self.phoneEdit.setFocus()
        else:
            new_phone = self.phoneEdit.text()
            new_email = self.emailEdit.text()

            #Gọi hàm update từ data_manager
            success, msg = data_manager.update_user_info(self.current_username, new_phone, new_email)

            if success:
                QMessageBox.information(self, "Thành công", msg)
                self.is_editing = False
                self.editBtn.setText("Chỉnh sửa thông tin")
                self.set_fields_readonly(True)
            else:
                QMessageBox.critical(self, "Lỗi", msg)

    def logout(self):
        reply = QMessageBox.question(self, "Xác nhận", "Bạn có muốn đăng xuất?", QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            widget.setCurrentIndex(0)

    def change_password(self):
        self.change_pass_dialog = ChangePasswordWindow(self.current_username, self)
        self.change_pass_dialog.show()


class PostDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        try:
            #Load giao diện postDialog.ui
            uic.loadUi(get_ui_path("postDialog.ui"), self)
        except Exception as e:
            QMessageBox.critical(self, "Lỗi UI", f"Không tìm thấy postDialog.ui: {e}")
            return

        self.source_image_path = ""  #Đường dẫn ảnh gốc
        self.final_db_path = ""  #Đường dẫn lưu vào DB

        #Kết nối các nút bấm
        if hasattr(self, 'uploadBtn'):
            self.uploadBtn.clicked.connect(self.choose_image)
        if hasattr(self, 'confirmBtn'):
            self.confirmBtn.clicked.connect(self.handle_post)
        if hasattr(self, 'cancelBtn'):
            self.cancelBtn.clicked.connect(self.close)

    def choose_image(self):
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Chọn ảnh", "", "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )

        if file_name:
            self.source_image_path = file_name

            # Hiển thị lên imagelbl
            if hasattr(self, 'imagelbl'):
                pixmap = QtGui.QPixmap(file_name)
                # Scale ảnh
                w = self.imagelbl.width()
                h = self.imagelbl.height()
                scaled_pixmap = pixmap.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.imagelbl.setPixmap(scaled_pixmap)
                self.imagelbl.setAlignment(Qt.AlignCenter)

    #Copy dữ liệu vào database
    def handle_post(self):
        # 1. Lấy dữ liệu
        title = ""
        content = ""
        if hasattr(self, 'titleINPUT'): title = self.titleINPUT.text().strip()
        if hasattr(self, 'contextINPUT'): content = self.contextINPUT.toPlainText().strip()

        # 2. Kiểm tra dữ liệu
        if not title or not content:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập tiêu đề và nội dung!")
            return

        if not self.source_image_path:
            QMessageBox.warning(self, "Thiếu ảnh", "Vui lòng chọn ảnh minh họa!")
            return

        try:
            #3. Copy ảnh vào thư mục dự án
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            file_ext = os.path.splitext(self.source_image_path)[1]
            new_filename = f"post_{timestamp}{file_ext}"
            current_dir = os.path.dirname(os.path.abspath(__file__))
            dest_dir = os.path.join(current_dir, "..", "ASSETS", "picForDefaultPost")

            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)

            dest_path = os.path.join(dest_dir, new_filename)
            shutil.copy2(self.source_image_path, dest_path)

            #4. Lưu vào Database
            self.final_db_path = f"../ASSETS/picForDefaultPost/{new_filename}"

            success, msg = data_manager.add_default_post(title, content, self.final_db_path)

            if success:
                QMessageBox.information(self, "Thành công", "Đã đăng bài viết mới!")
                self.accept()  # Trả về kết quả thành công
            else:
                QMessageBox.critical(self, "Lỗi Database", msg)

        except Exception as e:
            QMessageBox.critical(self, "Lỗi hệ thống", f"Chi tiết lỗi: {e}")

#Class Login
class LoginScreen(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        try:
            uic.loadUi(get_ui_path("loginPage.ui"), self)
            if hasattr(self, 'password'):
                self.password.setEchoMode(QtWidgets.QLineEdit.Password)
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

        #Cho phép nhấn Enter để đăng nhập
        try:
            if hasattr(self, 'username'):
                self.username.returnPressed.connect(self.handle_login)
            if hasattr(self, 'password'):
                self.password.returnPressed.connect(self.handle_login)
        except AttributeError:
            print("Không thể kết nối Enter key")

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


#Class Register
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


#class kết quả trang tìm kiếm
class SearchResults(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        try:
            uic.loadUi(get_ui_path("searchResults.ui"), self)
        except FileNotFoundError:
            print("Lỗi: Không tìm thấy searchResults.ui")

        #------------------Nút yêu thích-----------------
        self._favorite_buttons = [
            self.favoriteButton,
            self.favoriteButton_2,
            self.favoriteButton_3,
            self.favoriteButton_4,
            self.favoriteButton_5,
            self.favoriteButton_6,
        ]

        for index, btn in enumerate(self._favorite_buttons):
            btn.clicked.connect(
                lambda checked=False, i=index: self.on_favorite_clicked(i)
            )

        # ---------------- setup cái minimap ----------------
        self.map_widget = MapWidget()
        map_layout = QVBoxLayout(self.frame)
        map_layout.setContentsMargins(0, 0, 0, 0)
        map_layout.addWidget(self.map_widget)
        self.map_widget.load_coordinates(10.775, 106.700, popup_text="Default")

        # ---------------- biến giữ dữ liệu: username & danh sách kết quả tìm kiếm ----------------
        self.data = []
        self.current_username = None

        # ---------------- Khiến những ô chứa bấm được ----------------
        self._frames = [
            self.framBox,
            self.frameBox_2,
            self.frameBox_3,
            self.frameBox_4,
            self.frameBox_5,
            self.frameBox_6,
        ]

        for frame in self._frames:
                self._install_click_filter(frame)
                frame.setCursor(QtCore.Qt.PointingHandCursor)
                frame.setAttribute(QtCore.Qt.WA_StyledBackground, True)

        if hasattr(self, 'homeButton'):
             self.homeButton.clicked.connect(self.goto_menu)

    def goto_menu(self):
        widget.setCurrentIndex(3)

    def on_favorite_clicked(self, index):
        if index >= len(self.data):
            return

        item = self.data[index]
        add_favorite_place(self.current_username,item.name,item.addr,item.lat,item.lon,random_image_path(item.category))

    def loadData(self, username, data):
        self.current_username = username
        self.data = data
        
        label_sets = [
                (self.addrLabel,   self.imageLabel,   self.nameLabel,   self.categoryLabel),
                (self.addrLabel_2, self.imageLabel_2, self.nameLabel_2, self.categoryLabel_2),
                (self.addrLabel_3, self.imageLabel_3, self.nameLabel_3, self.categoryLabel_3),
                (self.addrLabel_4, self.imageLabel_4, self.nameLabel_4, self.categoryLabel_4),
                (self.addrLabel_5, self.imageLabel_5, self.nameLabel_5, self.categoryLabel_5),
                (self.addrLabel_6, self.imageLabel_6, self.nameLabel_6, self.categoryLabel_6),
        ]

        count = min(len(self.data), len(label_sets))

        for i in range(count):
                item = self.data[i]
                addr_lbl, img_lbl, name_lbl, cate_lbl = label_sets[i]

                addr_lbl.setText(item.addr)
                img_lbl.setPixmap(QPixmap(random_image_path(item.category)))
                name_lbl.setText(item.name)
                cate_lbl.setText(item.category)

    def _install_click_filter(self, widget):
        # Install the filter on the widget and recursively on its children so clicks
        # on labels/images inside the frame are also caught.
        widget.installEventFilter(self)
        for child in widget.findChildren(QtWidgets.QWidget):
            child.installEventFilter(self)

    def eventFilter(self, obj, event):
        # Only handle mouse-press events here 
        if event.type() == QEvent.MouseButtonPress:

            if isinstance(obj, QPushButton):
                return False
            
            for index, frame in enumerate(self._frames):
                
                if obj is frame or frame.isAncestorOf(obj):
                
                    if index >= len(self.data):
                        return True

                    item = self.data[index]
                
                    self.map_widget.load_coordinates(
                        item.lat,
                        item.lon,
                        popup_text=item.name
                    )
                    return True 

        return super().eventFilter(obj, event)

    
#Chương trình chính để khởi tạo index, khởi tạo object, căn chỉnh cửa sổ vân vân mây mây
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    #Tạo Stack chứa các màn hình
    widget = QtWidgets.QStackedWidget()

    #Import FavoritePlacesWindow
    from add_favorite_places import FavoritePlacesWindow

    #Khởi tạo 6 màn hình
    login_window = LoginScreen()                  # Index 0
    register_window = RegisterScreen()            # Index 1
    profile_window = ProfileScreen()              # Index 2
    menu_window = MenuScreen()                    # Index 3
    favorite_window = FavoritePlacesWindow("")    # Index 4
    searchResults_window = SearchResults()        # Index 5

    #Thêm vào Stack
    widget.addWidget(login_window)
    widget.addWidget(register_window)
    widget.addWidget(profile_window)
    widget.addWidget(menu_window)
    widget.addWidget(favorite_window)
    widget.addWidget(searchResults_window)

    #Cấu hình cửa sổ
    widget.resize(860, 540)
    widget.setMinimumSize(500, 700)
    widget.show()

    try:
        sys.exit(app.exec_())
    except Exception as e:
        print("Thoát chương trình:", e)
