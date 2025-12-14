import sqlite3
import os
import shutil
from datetime import datetime
from data_manager import get_connection, DB_NAME

# Đường dẫn thư mục lưu ảnh địa điểm yêu thích
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FAVORITE_PLACES_DIR = os.path.join(BASE_DIR, "..", "ASSETS", "addToFavoritePlaces")
def initialize_favorite_places_table():
    """Tạo bảng favorite_places nếu chưa tồn tại"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS favorite_places (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                address TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                image_path TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"--- LỖI: Không thể tạo bảng favorite_places: {e} ---")
initialize_favorite_places_table()


def get_user_id_by_username(username):
    """Lấy user_id từ username"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        conn.close()
        return result["id"] if result else None
    except Exception as e:
        print(f"--- LỖI get_user_id_by_username: {e} ---")
        return None


def save_image_to_favorites(source_image_path, place_title):
    """
    Lưu ảnh vào thư mục ASSETS/addToFavoritePlaces
    
    Args:
        source_image_path: Đường dẫn đến ảnh gốc
        place_title: Tên địa điểm (dùng để đặt tên file)
    
    Returns:
        Đường dẫn tương đối của ảnh đã lưu hoặc None nếu lỗi
    """
    try:
        # Kiểm tra file gốc có tồn tại không
        if not os.path.exists(source_image_path):
            print(f"--- LỖI: Không tìm thấy ảnh gốc: {source_image_path} ---")
            return None
        
        # Lấy phần mở rộng của file (jpg, png, etc.)
        file_extension = os.path.splitext(source_image_path)[1]
        
        # Tạo tên file mới (dùng timestamp để tránh trùng lặp)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Loại bỏ ký tự đặc biệt trong tên địa điểm
        safe_title = "".join(c for c in place_title if c.isalnum() or c in (' ', '_')).strip()
        safe_title = safe_title.replace(' ', '_')
        new_filename = f"{safe_title}_{timestamp}{file_extension}"
        
        # Đường dẫn đầy đủ của file đích
        destination_path = os.path.join(FAVORITE_PLACES_DIR, new_filename)
        
        # Copy ảnh
        shutil.copy2(source_image_path, destination_path)
        
        # Trả về đường dẫn tương đối
        relative_path = os.path.join("ASSETS", "addToFavoritePlaces", new_filename)
        print(f"--- DEBUG: Đã lưu ảnh tại: {relative_path} ---")
        return relative_path
        
    except Exception as e:
        print(f"--- LỖI save_image_to_favorites: {e} ---")
        return None


def add_favorite_place(username, title, address, latitude, longitude, image_path):
    """
    Thêm địa điểm yêu thích của người dùng
    
    Args:
        username: Tên đăng nhập của người dùng
        title: Tên địa điểm
        address: Địa chỉ
        latitude: Vĩ độ (tọa độ vệ tinh)
        longitude: Kinh độ (tọa độ vệ tinh)
        image_path: Đường dẫn đến ảnh đại diện
    
    Returns:
        (success: bool, message: str)
    """
    try:
        # Lấy user_id
        user_id = get_user_id_by_username(username)
        if user_id is None:
            return False, "Không tìm thấy người dùng!"
        
        # Lưu ảnh vào thư mục
        saved_image_path = save_image_to_favorites(image_path, title)
        if saved_image_path is None:
            return False, "Không thể lưu ảnh địa điểm!"
        
        # Kiểm tra địa điểm đã được lưu chưa
        if check_favorite_place_exists(user_id, title, latitude, longitude):
            return False, "Địa điểm này đã có trong danh sách yêu thích!"
        
        # Thêm vào database
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO favorite_places 
            (user_id, title, address, latitude, longitude, image_path)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, title, address, latitude, longitude, saved_image_path))
        conn.commit()
        conn.close()
        
        return True, "Đã thêm địa điểm vào danh sách yêu thích!"
        
    except Exception as e:
        return False, f"Lỗi khi thêm địa điểm yêu thích: {e}"


def check_favorite_place_exists(user_id, title, latitude, longitude):
    """Kiểm tra địa điểm đã được lưu chưa (dựa vào tọa độ)"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id FROM favorite_places 
            WHERE user_id = ? 
            AND ABS(latitude - ?) < 0.0001 
            AND ABS(longitude - ?) < 0.0001
        ''', (user_id, latitude, longitude))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    except Exception as e:
        print(f"--- LỖI check_favorite_place_exists: {e} ---")
        return False


def get_user_favorite_places(username):
    """
    Lấy tất cả địa điểm yêu thích của người dùng
    
    Args:
        username: Tên đăng nhập
    
    Returns:
        Danh sách các địa điểm yêu thích (list of dict)
    """
    try:
        user_id = get_user_id_by_username(username)
        if user_id is None:
            return []
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, title, address, latitude, longitude, image_path, created_at
            FROM favorite_places
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))
        places = cursor.fetchall()
        conn.close()
        
        return [dict(place) for place in places]
        
    except Exception as e:
        print(f"--- LỖI get_user_favorite_places: {e} ---")
        return []


def get_favorite_place_by_id(place_id, username):
    """
    Lấy thông tin chi tiết của một địa điểm yêu thích
    
    Args:
        place_id: ID của địa điểm
        username: Tên đăng nhập (để xác thực quyền truy cập)
    
    Returns:
        Dict chứa thông tin địa điểm hoặc None
    """
    try:
        user_id = get_user_id_by_username(username)
        if user_id is None:
            return None
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, title, address, latitude, longitude, image_path, created_at
            FROM favorite_places
            WHERE id = ? AND user_id = ?
        ''', (place_id, user_id))
        place = cursor.fetchone()
        conn.close()
        
        return dict(place) if place else None
        
    except Exception as e:
        print(f"--- LỖI get_favorite_place_by_id: {e} ---")
        return None


def remove_favorite_place(place_id, username):
    """
    Xóa địa điểm khỏi danh sách yêu thích
    
    Args:
        place_id: ID của địa điểm
        username: Tên đăng nhập
    
    Returns:
        (success: bool, message: str)
    """
    try:
        user_id = get_user_id_by_username(username)
        if user_id is None:
            return False, "Không tìm thấy người dùng!"
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Lấy thông tin ảnh trước khi xóa
        cursor.execute('''
            SELECT image_path FROM favorite_places
            WHERE id = ? AND user_id = ?
        ''', (place_id, user_id))
        result = cursor.fetchone()
        
        if result is None:
            conn.close()
            return False, "Không tìm thấy địa điểm hoặc bạn không có quyền xóa!"
        
        # Xóa khỏi database
        cursor.execute('''
            DELETE FROM favorite_places
            WHERE id = ? AND user_id = ?
        ''', (place_id, user_id))
        conn.commit()
        conn.close()
        
        # Xóa file ảnh
        try:
            image_full_path = os.path.join(BASE_DIR, "..", result["image_path"])
            if os.path.exists(image_full_path):
                os.remove(image_full_path)
                print(f"--- DEBUG: Đã xóa ảnh: {image_full_path} ---")
        except Exception as img_error:
            print(f"--- CẢNH BÁO: Không thể xóa ảnh: {img_error} ---")
        
        return True, "Đã xóa địa điểm khỏi danh sách yêu thích!"
        
    except Exception as e:
        return False, f"Lỗi khi xóa địa điểm: {e}"


def update_favorite_place(place_id, username, title=None, address=None, 
                         latitude=None, longitude=None, new_image_path=None):
    """
    Cập nhật thông tin địa điểm yêu thích
    
    Args:
        place_id: ID của địa điểm
        username: Tên đăng nhập
        title: Tên mới (optional)
        address: Địa chỉ mới (optional)
        latitude: Vĩ độ mới (optional)
        longitude: Kinh độ mới (optional)
        new_image_path: Đường dẫn ảnh mới (optional)
    
    Returns:
        (success: bool, message: str)
    """
    try:
        user_id = get_user_id_by_username(username)
        if user_id is None:
            return False, "Không tìm thấy người dùng!"
        
        # Lấy thông tin hiện tại
        current_place = get_favorite_place_by_id(place_id, username)
        if current_place is None:
            return False, "Không tìm thấy địa điểm!"
        
        # Chuẩn bị dữ liệu update
        update_fields = []
        update_values = []
        
        if title is not None:
            update_fields.append("title = ?")
            update_values.append(title)
        
        if address is not None:
            update_fields.append("address = ?")
            update_values.append(address)
        
        if latitude is not None:
            update_fields.append("latitude = ?")
            update_values.append(latitude)
        
        if longitude is not None:
            update_fields.append("longitude = ?")
            update_values.append(longitude)
        
        # Xử lý ảnh mới nếu có
        if new_image_path is not None:
            new_title = title if title is not None else current_place["title"]
            saved_image_path = save_image_to_favorites(new_image_path, new_title)
            if saved_image_path:
                update_fields.append("image_path = ?")
                update_values.append(saved_image_path)
                
                # Xóa ảnh cũ
                try:
                    old_image_path = os.path.join(BASE_DIR, "..", current_place["image_path"])
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                except Exception as e:
                    print(f"--- CẢNH BÁO: Không thể xóa ảnh cũ: {e} ---")
        
        if not update_fields:
            return False, "Không có thông tin nào để cập nhật!"
        
        # Update database
        update_values.extend([place_id, user_id])
        query = f"UPDATE favorite_places SET {', '.join(update_fields)} WHERE id = ? AND user_id = ?"
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, update_values)
        conn.commit()
        conn.close()
        
        return True, "Cập nhật địa điểm thành công!"
        
    except Exception as e:
        return False, f"Lỗi khi cập nhật địa điểm: {e}"


def search_favorite_places(username, keyword):
    """
    Tìm kiếm địa điểm yêu thích theo từ khóa
    
    Args:
        username: Tên đăng nhập
        keyword: Từ khóa tìm kiếm (tìm trong title và address)
    
    Returns:
        Danh sách các địa điểm phù hợp
    """
    try:
        user_id = get_user_id_by_username(username)
        if user_id is None:
            return []
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, title, address, latitude, longitude, image_path, created_at
            FROM favorite_places
            WHERE user_id = ? 
            AND (title LIKE ? OR address LIKE ?)
            ORDER BY created_at DESC
        ''', (user_id, f"%{keyword}%", f"%{keyword}%"))
        places = cursor.fetchall()
        conn.close()
        
        return [dict(place) for place in places]
        
    except Exception as e:
        print(f"--- LỖI search_favorite_places: {e} ---")
        return []


# ===== UI CLASS =====
from PyQt5 import QtWidgets, QtCore, QtGui, uic
from PyQt5.QtWidgets import QMainWindow, QLabel, QPushButton, QVBoxLayout, QMessageBox, QWidget
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap


class FavoritePlaceCard(QWidget):
    """Widget hiển thị 1 địa điểm yêu thích với ảnh + tên + nút xóa"""
    deleted = pyqtSignal(int)  # Signal khi xóa địa điểm (gửi place_id)
    clicked = pyqtSignal(dict)  # Signal khi click vào card (gửi place info)
    
    def __init__(self, place_info, parent=None):
        super().__init__(parent)
        self.place_info = place_info
        self.place_id = place_info['id']
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Card container với styling
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 10px;
                border: 2px solid #e0e0e0;
            }
            QWidget:hover {
                border: 2px solid #ff6b6b;
                background-color: #fff5f5;
            }
        """)
        self.setFixedSize(200, 250)
        self.setCursor(Qt.PointingHandCursor)
        
        # Ảnh địa điểm
        image_label = QLabel()
        image_path = os.path.join(BASE_DIR, "..", self.place_info['image_path'])
        
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            scaled_pixmap = pixmap.scaled(180, 150, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            image_label.setPixmap(scaled_pixmap)
        else:
            image_label.setText("📷")
            image_label.setStyleSheet("font-size: 48px; color: #ccc;")
        
        image_label.setFixedSize(180, 150)
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                border-radius: 8px;
                border: 1px solid #ddd;
            }
        """)
        
        # Tên địa điểm
        title_label = QLabel(self.place_info['title'])
        title_label.setWordWrap(True)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: bold;
                color: #333;
                border: none;
                background-color: transparent;
            }
        """)
        title_label.setMaximumHeight(40)
        
        # Nút xóa
        delete_btn = QPushButton("🗑️ Xóa")
        delete_btn.setFixedHeight(30)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        delete_btn.clicked.connect(self.on_delete_clicked)
        
        layout.addWidget(image_label)
        layout.addWidget(title_label)
        layout.addWidget(delete_btn)
        
        self.setLayout(layout)
    
    def on_delete_clicked(self):
        reply = QMessageBox.question(
            self, 
            'Xác nhận xóa',
            f'Bạn có chắc muốn xóa "{self.place_info["title"]}" khỏi danh sách yêu thích?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.deleted.emit(self.place_id)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.place_info)


class FavoritePlacesWindow(QMainWindow):
    """Cửa sổ hiển thị danh sách địa điểm yêu thích"""
    
    def __init__(self, username, parent=None):
        super().__init__(parent)
        self.username = username
        self.all_places = []
        self.current_places = []
        
        # Load UI file
        ui_path = os.path.join(BASE_DIR, "favorite.ui")
        uic.loadUi(ui_path, self)
        
        self.init_connections()
        self.load_favorite_places()
    
    def init_connections(self):
        """Kết nối các signal/slot"""
        self.searchBtn.clicked.connect(self.on_search)
        self.clearBtn.clicked.connect(self.on_clear_search)
        self.backBtn.clicked.connect(self.go_back_to_menu)
        self.searchInput.returnPressed.connect(self.on_search)
    
    def load_favorites(self, username):
        """Load danh sách yêu thích cho user mới"""
        self.username = username
        self.load_favorite_places()
    
    def go_back_to_menu(self):
        """Quay về màn hình menu"""
        from PyQt5.QtWidgets import QApplication
        for widget in QApplication.topLevelWidgets():
            if hasattr(widget, 'setCurrentIndex'):
                widget.setCurrentIndex(3)  # Index 3 là menu
                break
    
    def load_favorite_places(self, keyword=None):
        """Load danh sách địa điểm yêu thích"""
        try:
            if keyword:
                self.current_places = search_favorite_places(self.username, keyword)
            else:
                self.current_places = get_user_favorite_places(self.username)
            
            self.all_places = get_user_favorite_places(self.username)
            self.display_places()
            self.update_count()
            
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải danh sách: {e}")
    
    def display_places(self):
        """Hiển thị danh sách địa điểm dạng grid"""
        # Xóa các widget cũ
        grid_layout = self.placesContainer.layout()
        while grid_layout.count():
            child = grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Nếu không có địa điểm nào
        if not self.current_places:
            no_data_label = QLabel("💔 Chưa có địa điểm yêu thích nào")
            no_data_label.setAlignment(Qt.AlignCenter)
            no_data_label.setStyleSheet("""
                font-size: 18px;
                color: #999;
                padding: 50px;
            """)
            grid_layout.addWidget(no_data_label, 0, 0, 1, 4)
            return
        
        # Hiển thị theo grid (4 cột)
        columns = 4
        for index, place in enumerate(self.current_places):
            row = index // columns
            col = index % columns
            
            card = FavoritePlaceCard(place)
            card.deleted.connect(self.on_place_deleted)
            card.clicked.connect(self.on_place_clicked)
            
            grid_layout.addWidget(card, row, col)
    
    def update_count(self):
        """Cập nhật số lượng địa điểm"""
        total = len(self.all_places)
        showing = len(self.current_places)
        
        if showing == total:
            self.countLabel.setText(f"Tổng số: {total} địa điểm")
        else:
            self.countLabel.setText(f"Hiển thị: {showing}/{total} địa điểm")
    
    def on_search(self):
        """Xử lý tìm kiếm"""
        keyword = self.searchInput.text().strip()
        if keyword:
            self.load_favorite_places(keyword)
        else:
            self.on_clear_search()
    
    def on_clear_search(self):
        """Xóa tìm kiếm và hiển thị tất cả"""
        self.searchInput.clear()
        self.load_favorite_places()
    
    def on_place_deleted(self, place_id):
        """Xử lý khi xóa địa điểm"""
        success, message = remove_favorite_place(place_id, self.username)
        
        if success:
            QMessageBox.information(self, "Thành công", message)
            self.load_favorite_places()
        else:
            QMessageBox.warning(self, "Lỗi", message)
    
    def on_place_clicked(self, place_info):
        """Xử lý khi click vào card địa điểm"""
        details = f"""
<b>📍 {place_info['title']}</b><br><br>
<b>Địa chỉ:</b> {place_info['address']}<br>
<b>Tọa độ:</b> {place_info['latitude']}, {place_info['longitude']}<br>
<b>Ngày lưu:</b> {place_info['created_at']}<br>
        """
        QMessageBox.information(self, "Chi tiết địa điểm", details)


# ===== MAIN TEST =====
if __name__ == "__main__":
    import sys
    
    app = QtWidgets.QApplication(sys.argv)
    
    # Test với username
    test_username = "testuser"
    
    window = FavoritePlacesWindow(test_username)
    window.show()
    
    sys.exit(app.exec_())
