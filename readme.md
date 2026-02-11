# 📹 VIDEO DOWNLOADER - MULTI MODE  
*✨ Công cụ tải video thông minh từ Facebook, YouTube & hàng trăm trang web khác ✨*

---

## 🌟 PHẦN 1: GIỚI THIỆU

<div align="center">

| Tính năng | Mô tả chi tiết |
|-----------|----------------|
| **📘 Facebook Downloader** | Tải video Facebook chất lượng cao với cơ chế xử lý cookies thông minh (hỗ trợ tải hàng loạt) |
| **🎥 YouTube Downloader** | Tải video MP4 đa độ phân giải hoặc trích xuất audio MP3 chất lượng cao |
| **🌐 Universal Mode 3** | Công nghệ quét **10+ chiến lược** thông minh: phát hiện m3u8, iframe, JSON, CDN, meta tags... Tải đa luồng tối ưu tốc độ |
| **📡 Server Local** | Chia sẻ video qua mạng LAN - tải từ điện thoại/máy tính khác trong cùng mạng |
| **⚡ Xử lý thông minh** | Tự động chuyển file vào thư mục `finish/`, phát hiện cookies hết hạn, xử lý tên file trùng |

</div>

### 🔑 ƯU ĐIỂM NỔI BẬT
- ✅ **Không quảng cáo** - Mã nguồn mở minh bạch  
- ✅ **Đa nền tảng** - Chạy trên Windows (hỗ trợ Linux/macOS qua điều chỉnh nhỏ)  
- ✅ **Bảo mật** - Cookies chỉ lưu cục bộ trên máy bạn  
- ✅ **Tối ưu hiệu suất** - Xử lý đa luồng (6 luồng mặc định, có thể tùy chỉnh)  
- ✅ **Giao diện tiếng Việt** - Thân thiện, hướng dẫn chi tiết từng bước  

### ⚙️ YÊU CẦU HỆ THỐNG
```markdown
- Windows 7/8/10/11 (ưu tiên)
- Python 3.6+ (nếu chạy trực tiếp script)
- File engine: yt-dlp.exe + ffmpeg.exe (đặt trong thư mục `main/engine/`)
- Trình duyệt Chrome/Edge (cho extension lấy cookies Facebook)
```

---

## 📖 PHẦN 2: HƯỚNG DẪN SỬ DỤNG CHI TIẾT

### 📁 CẤU TRÚC THƯ MỤC CHUẨN
```
download/
├── main/
│   ├── engine/          # ← BẮT BUỘC: Đặt yt-dlp.exe + ffmpeg.exe vào đây
│   │   ├── yt-dlp.exe
│   │   └── ffmpeg.exe
│   ├── getlink/         # ← Tự động tạo khi chạy Chế độ Facebook
│   │   └── link.txt
│   ├── cookies.txt      # ← Dán cookies Facebook vào đây
│   ├── source.txt       # ← Dán mã nguồn Facebook vào đây
│   ├── server.py        # ← (Tùy chọn) File server chia sẻ LAN
│   └── main.py          # ← Script chính
├── finish/              # ← VIDEO SAU KHI TẢI XONG ĐỀU Ở ĐÂY!
│   ├── mode3/           # ← Video từ Chế độ 3
│   │   └── other/       # ← File phụ (nếu có)
│   └── ... 
└── run.bat              # ← CHẠY FILE NÀY ĐỂ KHỞI ĐỘNG
```

---

### 🔒 CHẾ ĐỘ 1: TẢI VIDEO FACEBOOK (HƯỚNG DẪN CHI TIẾT)

> ⚠️ **LƯU Ý QUAN TRỌNG**:  
> 🔸 Cookies Facebook **sẽ hết hạn sau 1-7 ngày** - cần cập nhật lại khi tải thất bại  
> 🔸 Luôn đăng nhập Facebook trên trình duyệt trước khi lấy cookies

#### 📌 CÁC BƯỚC THỰC HIỆN:
```markdown
1️⃣ TRUY CẬP VIDEO MONG MUỐN TRÊN TRÌNH DUYỆT
   → Nhấn chuột phải → Chọn "View Page Source" (Xem mã nguồn trang)
   → Copy TOÀN BỘ nội dung (Ctrl+A → Ctrl+C)

2️⃣ DÁN VÀO FILE `source.txt`
   → Mở thư mục `download/main/`
   → Mở file `source.txt` → Dán nội dung → Lưu file (Ctrl+S)

3️⃣ CÀI EXTENSION LẤY COOKIES
   → Cài ngay: https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
   → (Hoặc tìm "Get cookies.txt Locally" trên Chrome Web Store)

4️⃣ LẤY COOKIES FACEBOOK
   → Truy cập facebook.com (đảm bảo đã đăng nhập)
   → Nhấp vào icon extension → Nhấn nút "COPY"
   → Mở file `cookies.txt` trong thư mục `main/` → Dán nội dung → Lưu file

5️⃣ KHỞI ĐỘNG CÔNG CỤ
   → Vào thư mục `download/` → Nh double-click file `run.bat`
   → Chọn `1` (Chế độ Facebook)
   → Chọn tiếp:
      • `1`: Nhập URL video thủ công
      • `2`: Tải hàng loạt từ file `link.txt` (script tự trích xuất link từ source.txt)

6️⃣ XEM KẾT QUẢ
   → Video tải thành công nằm trong thư mục `finish/`
```

---

### 🎥 CHẾ ĐỘ 2: TẢI YOUTUBE
```markdown
1. Chạy `run.bat` → Chọn `2`
2. Dán URL video YouTube
3. Chọn định dạng:
   • `1`: Tải MP3 (audio chất lượng cao)
   • `2`: Tải MP4 → Chọn độ phân giải (hoặc `0` để tự động chọn tốt nhất)
4. File xuất ra tại `finish/`
```

---

### 🌐 CHẾ ĐỘ 3: TẢI TỪ MỌI TRANG WEB (MODE 3 - ĐA LUỒNG)
```markdown
1. Chạy `run.bat` → Chọn `3`
2. Dán URL trang web chứa video (báo, blog, diễn đàn...)
3. Công cụ TỰ ĐỘNG:
   • Quét 10+ chiến lược phát hiện link ẩn
   • Tải đồng thời nhiều luồng
   • Phân loại file: MP4/MP3 vào `finish/mode3/`, file khác vào `finish/mode3/other/`
4. Xem kết quả trong thư mục `finish/`
```

---

### 🌍 KHỞI ĐỘNG SERVER LOCAL (CHIA SẺ QUA MẠNG LAN)
```markdown
✅ TRONG MENU CHÍNH:
   • Nếu thấy "e - 🟢 Khởi động Server Local" → Nhấn `e` để BẬT
   • Nếu thấy "e - 🔴 Tắt Server Local (đang chạy)" → Nhấn `e` để TẮT

💡 CÁCH SỬ DỤNG:
   1. Khởi động server thành công → Ghi nhớ địa chỉ IP và cổng (port) hiển thị
   2. Trên điện thoại/máy tính khác (cùng mạng Wi-Fi):
      • Mở trình duyệt → Truy cập: http://[IP_CỦA_MÁY_BẠN]:[PORT]
      • Tải video trực tiếp không cần cài đặt gì thêm!
   
⚠️ LƯU Ý: 
   • Cần có file `server.py` trong thư mục `main/` (script sẽ báo lỗi nếu thiếu)
   • Tắt tường lửa Windows nếu không kết nối được
```

---

### ❗ XỬ LÝ SỰ CỐ THƯỜNG GẶP
| Vấn đề | Giải pháp |
|--------|-----------|
| **"THIẾU FILE ENGINE"** | Tải yt-dlp.exe + ffmpeg.exe → Đặt đúng vào `main/engine/` |
| **"COOKIES ĐÃ HẾT HẠN"** | Lặp lại Bước 4 & 5 trong hướng dẫn Facebook |
| **Tải về file rỗng/lỗi** | Kiểm tra URL có đúng không? Video có yêu cầu đăng nhập không? |
| **Server không kết nối** | Tắt tường lửa → Kiểm tra IP máy chủ → Đảm bảo cùng mạng LAN |
| **Link.txt trống** | Đảm bảo đã dán mã nguồn Facebook vào `source.txt` trước khi chạy |

---

### 💡 MẸO SỬ DỤNG HIỆU QUẢ
- 🔄 **Cập nhật cookies định kỳ** mỗi 3-5 ngày để tránh lỗi Facebook  
- 📱 **Dùng Server Local** để tải video Facebook/YouTube về điện thoại cực nhanh  
- 🌐 **Chế độ 3** hiệu quả nhất với trang web có video nhúng (báo điện tử, blog...)  
- ⚙️ **Tùy chỉnh luồng tải**: Mở `main.py` → Tìm `MAX_WORKERS = 6` → Sửa số phù hợp cấu hình máy  

---

<div align="center">

> 🌈 **CHÚC BẠN SỬ DỤNG CÔNG CỤ HIỆU QUẢ!**  
> 🙏 *Nếu thấy hữu ích, hãy ⭐ cho repository này nhé!*  
> 🔒 **LƯU Ý PHÁP LÝ**: Chỉ sử dụng cho mục đích cá nhân, tuân thủ bản quyền nội dung  

</div>
