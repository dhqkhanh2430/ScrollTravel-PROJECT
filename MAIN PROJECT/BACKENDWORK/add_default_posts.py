import data_manager
import os

# Đường dẫn tương đối đến folder chứa ảnh
IMAGE_FOLDER = "../ASSETS/picForDefaultPost/"

def check_image_exists(image_path):
    """Kiểm tra xem image_path đã tồn tại trong database chưa"""
    all_posts = data_manager.get_all_default_posts()
    for post in all_posts:
        if post['image_path'] == image_path:
            return True
    return False


def show_all_posts():
    """Hiển thị tất cả bài viết mặc định"""
    all_posts = data_manager.get_all_default_posts()
    
    if not all_posts:
        print("❌ Không có bài viết nào trong database!")
        return
    
    # Sắp xếp theo ID tăng dần (bài thêm trước hiển thị trước)
    all_posts.sort(key=lambda x: x['id'])
    
    print(f"{'='*80}")
    print(f"DANH SÁCH BÀI VIẾT MẶC ĐỊNH (Tổng: {len(all_posts)} bài)")
    print(f"{'='*80}\n")
    
    for i, post in enumerate(all_posts, 1):
        print(f"[{i}] ID: {post['id']}")
        print(f"    Tiêu đề: {post['title']}")
        print(f"    Mô tả: {post['description']}")
        print(f"    Ảnh: {post['image_path']}")
        print(f"    Ngày tạo: {post['created_at']}")
        print()


def add_initial_posts():
    """Thêm các bài viết mặc định ban đầu"""
    
    posts = [
        {
            "title": "Cầu Vàng Đà Nẵng",
            "description": "Cầu Vàng chắc chắn là điểm đến hàng đầu trong danh sách. Không chỉ mang đến không gian để thư giãn và chiêm ngưỡng cảnh quan thiên nhiên, cây cầu còn là nơi lý tưởng để cho ra đời những bức ảnh tuyệt đẹp. Khung cảnh từ trên cầu thay đổi theo từng thời điểm trong ngày, mỗi khoảnh khắc đều mang đến cảm giác mới lạ.",
            "image": "cau-vang-da-nang.jpg"
        },
        {
            "title": "Nhà Thờ Đức Bà",
            "description": "Nhà Thờ Đức Bà Sài Gòn là một công trình kiến trúc Gothic cổ kính và tráng lệ, được xây dựng vào cuối thế kỷ 19. Với hai tháp chuông cao vút và những viên gạch đỏ được nhập khẩu từ Pháp, nhà thờ đã trở thành biểu tượng văn hóa và lịch sử của Thành phố Hồ Chí Minh.",
            "image": "ntdb.webp"
        },
        {
            "title": "Quảng Trường Ba Đình",
            "description": "Quảng trường Ba Đình là nơi diễn ra lễ Tuyên ngôn Độc lập lịch sử vào ngày 2/9/1945. Đây là một trong những địa điểm quan trọng và thiêng liêng nhất của dân tộc Việt Nam, thu hút hàng triệu du khách mỗi năm đến tham quan và tưởng nhớ Chủ tịch Hồ Chí Minh.",
            "image": "quang-truong-ba-dinh.jpg"
        },
        {
            "title": "Phố cổ Hội An",
            "description": "Phố cổ Hội An mang trong mình vẻ đẹp cổ kính, yên bình, và đậm đà bản sắc văn hóa. Dù bạn là người yêu thích kiến trúc, đam mê ẩm thực, hay đang tìm kiếm một nơi thư giãn đậm chất văn hóa, Hội An đều có thể đáp ứng mọi mong đợi.",
            "image": "hoian.webp"
        },
        {
            "title": "Quảng trường Lâm Viên Đà Lạt",
            "description": "Quảng trường Lâm Viên được xây dựng từ năm 2009 và phải mất 6 năm công trình này mới được hoàn thiện sau đó đi vào hoạt động năm 2016. Đây được coi là một trong những địa điểm du lịch siêu HOT ở Đà Lạt ",
            "image": "quang-truong-lam-vien.jpg"
        },
        {
            "title": "Vũng Tàu",
            "description": "Vũng Tàu là một thành phố biển nổi tiếng với những bãi biển đẹp, các khu du lịch sinh thái và các món hải sản tươi ngon. Đây là điểm đến lý tưởng cho những ai muốn tận hưởng không khí trong lành và thư giãn bên bờ biển.",
            "image": "vung-tau.jpg"
        },
        {
            "title": "Biển Sầm Sơn Thanh Hóa",
            "description": "Biển Sầm Sơn là một trong những bãi biển nổi tiếng ở Thanh Hóa, thu hút đông đảo du khách mỗi năm với bãi cát dài, nước biển trong xanh và nhiều hoạt động giải trí hấp dẫn.",
            "image": "sam-son-thanh-hoa.jpg"
        },
        
    ]
    
    print("Bắt đầu thêm bài viết mặc định...")
    
    added_count = 0  # Đếm số bài viết được thêm thành công
    
    for post in posts:
        image_path = os.path.join(IMAGE_FOLDER, post["image"])
        
        # Kiểm tra trùng image_path
        if check_image_exists(image_path):
            print(f"○ Bỏ qua (đã tồn tại): {post['title']}")
            continue
        
        success, message = data_manager.add_default_post(
            title=post["title"],
            description=post["description"],
            image_path=image_path
        )
        
        if success:
            print(f"✓ Đã thêm: {post['title']}")
            added_count += 1
        else:
            print(f"✗ Lỗi khi thêm {post['title']}: {message}")
    
    # Kiểm tra có bài viết nào được thêm không
    if added_count == 0:
        print("\n❌ Không có địa điểm mới nào được thêm!")
    else:
        print(f"\n✅ Hoàn thành! Đã thêm {added_count} bài viết mới.")


if __name__ == "__main__":
    import sys
    
    print("="*50)
    print("QUẢN LÝ BÀI VIẾT MẶC ĐỊNH")
    print("="*50)
    print("1. Thêm bài viết")
    print("2. Xem danh sách bài viết")
    print("="*50)
    
    choice = input("Chọn chức năng (1 hoặc 2): ").strip()
    
    if choice == "1":
        print()
        add_initial_posts()
    elif choice == "2":
        print()
        show_all_posts()
    else:
        print("❌ Lựa chọn không hợp lệ!")
