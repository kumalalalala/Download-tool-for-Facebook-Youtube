# 📥 Download Tool for Facebook & YouTube

<div align="center">

![Python](https://img.shields.io/badge/Python-3.x-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-green)
![Engine](https://img.shields.io/badge/Engine-yt--dlp%20%2B%20ffmpeg-orange)

**Công cụ hỗ trợ tải video từ Facebook, YouTube và nhiều nền tảng khác.**  
Hỗ trợ đọc source HTML, sử dụng cookies Facebook, chạy đa luồng và xuất file vào thư mục hoàn tất.

</div>

---

# 📌 PHẦN 1 — GIỚI THIỆU

## 🎯 Mục đích

Công cụ này được thiết kế để:

- 📄 Đọc và xử lý source HTML (Facebook Stories / Post)
- 🔐 Sử dụng cookies Facebook để tải nội dung private
- 🔗 Tự động hoặc thủ công nhập link
- ⚡ Tải đa luồng (Facebook Mode)
- 📂 Xuất file hoàn tất vào thư mục `finish`
- 🌐 Hỗ trợ bật server nội bộ để tải từ thiết bị khác trong cùng mạng LAN

---

## 🗂 Cấu trúc thư mục chuẩn

```
Download-tool-for-Facebook-Youtube/
│
├── download/
│   ├── main/
│   │   ├── main.py
│   │   ├── cookies.txt
│   │   ├── source.txt
│   │   ├── getlink/
│   │   │   └── link.txt
│   │   └── server.py
│   │
│   ├── engine/
│   │   ├── yt-dlp.exe
│   │   └── ffmpeg.exe
│   │
│   └── run.bat
│
├── finish/      ← Nơi chứa file tải xong
└── README.md
```

> ⚠ Nếu `finish/` trống, hãy thêm file `.gitkeep` để GitHub hiển thị folder.

---

# ⚙ YÊU CẦU HỆ THỐNG

- ✅ Windows
- ✅ Python 3.x (`python --version`)
- ✅ yt-dlp.exe (đặt trong `engine/`)
- ✅ ffmpeg.exe (đặt trong `engine/`)
- ✅ Cookies Facebook hợp lệ (nếu tải nội dung private)

---

# 🚀 PHẦN 2 — HƯỚNG DẪN SỬ DỤNG

---

## 🟦 BƯỚC 1 — Lấy Source Facebook

1. Vào bài viết / stories mong muốn.
2. Nhấn chuột phải → **View Page Source** (hoặc `Ctrl + U`)
3. Copy toàn bộ nội dung HTML.
4. Dán vào file:

```
download/main/source.txt
```

> 🔴 Bắt buộc đối với chế độ Facebook.

---

## 🟦 BƯỚC 2 — Lấy Cookies Facebook

1. Cài extension Chrome:  
   https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc

2. Vào facebook.
3. Bật extension.
4. Nhấn **Copy**.
5. Dán vào:

```
download/main/cookies.txt
```

> 🔁 Cookies sẽ hết hạn theo thời gian → cần cập nhật khi lỗi xác thực.

---

## 🟦 BƯỚC 3 — Chuẩn bị link

Bạn có 2 cách:

### Cách 1 — Tự động
Tool sẽ đọc `source.txt` và tự trích xuất link vào:

```
download/main/getlink/link.txt
```

### Cách 2 — Thủ công
Tự thêm link vào file:

```
download/main/getlink/link.txt
```

Mỗi dòng là một URL.

---

## 🟦 BƯỚC 4 — Chạy Tool

### Cách 1: Dùng file batch

```
download/run.bat
```

### Cách 2: Chạy Python trực tiếp

```bash
cd download/main
python main.py
```

---

## 🟢 Các chế độ

| Mode | Chức năng |
|------|-----------|
| 1 | Facebook (đa luồng, dùng cookies + source) |
| 2 | YouTube |
| 3 | Multi website |

---

## 🟦 BƯỚC 5 — Xem kết quả

Sau khi tải xong, mở:

```
finish/
```

Toàn bộ video/audio sẽ nằm tại đây.

---

# 🌐 BẬT SERVER LAN (TUỲ CHỌN)

Cho phép tải video từ thiết bị khác trong cùng mạng WiFi.

### Cách bật:

Chạy:

```bash
python download/main/server.py
```

Hoặc bật từ menu trong `main.py`.

Sau đó truy cập địa chỉ IP hiển thị trên terminal từ thiết bị khác.

> ⚠ Chỉ dùng trong mạng nội bộ. Không mở ra Internet.

---

# 🔥 GHI ĐÈ TOÀN BỘ REPO (Force Push)

Nếu bạn muốn thay toàn bộ nội dung repo bằng trạng thái hiện tại:

```bash
git add .
git commit -m "Full update project"
git branch -M main
git push -f origin main
```

> ⚠ Force push sẽ ghi đè lịch sử trên GitHub.

---

# 🛠 TROUBLESHOOTING

### ❌ Lỗi 403 / Login Required
→ Cookies hết hạn → cập nhật `cookies.txt`

### ❌ Không thấy folder trống trên GitHub
→ Thêm file `.gitkeep` vào folder đó

### ❌ Báo thiếu yt-dlp hoặc ffmpeg
→ Đặt file `.exe` vào `download/engine/`

---

# 🧠 LƯU Ý QUAN TRỌNG

- Không commit `cookies.txt` nếu repo public.
- Không expose server ra Internet.
- Không lạm dụng tool vào mục đích vi phạm chính sách nền tảng.

---

# 📜 LICENSE

Chỉ dùng cho mục đích học tập và cá nhân.

---

<div align="center">

**Made with Python & yt-dlp**  
⭐ Nếu thấy hữu ích, hãy star repo.

</div>
