# 🎬 Video Downloader - Multi Mode

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.7%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)

**Công cụ tải video đa nền tảng mạnh mẽ với hỗ trợ Facebook, YouTube và hơn 1000+ trang web khác**

[Tính năng](#-tính-năng) •
[Cài đặt](#-cài-đặt) •
[Hướng dẫn sử dụng](#-hướng-dẫn-sử-dụng) •
[FAQ](#-câu-hỏi-thường-gặp)

</div>

---

## 📋 Giới thiệu

**Video Downloader - Multi Mode** là một công cụ Python mạnh mẽ cho phép bạn tải video từ nhiều nguồn khác nhau với giao diện dòng lệnh thân thiện. Công cụ hỗ trợ tải video chất lượng cao với nhiều tùy chọn linh hoạt.

### ✨ Tính năng

<table>
<tr>
<td width="33%">

#### 📘 Facebook Video
- ✅ Tải video Facebook chất lượng cao
- ✅ Hỗ trợ download đa luồng (6 threads)
- ✅ Xử lý cookies tự động
- ✅ Trích xuất URL từ source page

</td>
<td width="33%">

#### 🎥 YouTube Video/Audio
- ✅ Tải video/audio từ YouTube
- ✅ Chọn chất lượng tùy ý
- ✅ Hỗ trợ playlist
- ✅ Tách/ghép audio-video

</td>
<td width="33%">

#### 🌐 Đa Web Advanced
- ✅ Hỗ trợ 1000+ trang web
- ✅ 11 strategies tải thông minh
- ✅ Xử lý HLS/M3U8 streams
- ✅ Tải đa luồng (6 threads)

</td>
</tr>
</table>

### 🚀 Công nghệ sử dụng

- **yt-dlp**: Engine tải video mạnh mẽ
- **FFmpeg**: Xử lý video/audio chuyên nghiệp
- **Multi-threading**: Tải song song tối ưu tốc độ
- **Cookie-based auth**: Xác thực an toàn cho Facebook

---

## 🔧 Cài đặt

### Yêu cầu hệ thống

- Python 3.7 trở lên
- Windows / Linux / macOS
- Kết nối Internet ổn định

### Bước 1: Clone repository

```bash
git clone https://github.com/your-username/video-downloader.git
cd video-downloader
```

### Bước 2: Chuẩn bị Engine files

> [!IMPORTANT]
> Bạn cần tải 2 file engine và đặt vào thư mục `download/main/engine/`

**📥 Tải các file cần thiết:**

| File | Link tải | Mô tả |
|------|----------|-------|
| **yt-dlp.exe** | [yt-dlp releases](https://github.com/yt-dlp/yt-dlp/releases) | Engine tải video chính |
| **ffmpeg.exe** | [FFmpeg builds](https://www.gyan.dev/ffmpeg/builds/) | Xử lý video/audio |

**📁 Cấu trúc thư mục cần có:**

```
download/
├── main/
│   ├── engine/
│   │   ├── yt-dlp.exe      ← Đặt file ở đây
│   │   └── ffmpeg.exe      ← Đặt file ở đây
│   ├── python/
│   │   └── main.py
│   ├── cookies.txt
│   └── source.txt
├── finish/
└── run.bat
```

---

## 📖 Hướng dẫn sử dụng

### 🎯 Chế độ 1: Facebook Video (Chuyên sâu)

> [!NOTE]
> Chế độ này yêu cầu cookies để tải video Facebook. Đây là phương pháp an toàn và hợp pháp.

#### **Bước 1️⃣: Lấy Source Page**

1. Mở Facebook và vào story/video muốn tải
2. Click chuột phải → chọn **"View Page Source"** (hoặc `Ctrl+U`)
3. Copy toàn bộ nội dung source code

#### **Bước 2️⃣: Lưu Source Code**

Paste nội dung vào file `download/main/source.txt`

```plaintext
📄 download/main/source.txt
└── [Paste toàn bộ HTML source ở đây]
```

#### **Bước 3️⃣: Cài đặt Extension lấy Cookies**

1. Vào Chrome Web Store: [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
2. Cài đặt extension **"Get cookies.txt LOCALLY"**

#### **Bước 4️⃣: Lấy Cookies**

1. Vào trang **facebook.com** (đăng nhập tài khoản của bạn)
2. Click icon extension **Get cookies.txt** trên thanh toolbar
3. Click nút **"Copy"** để copy cookies

![Get Cookies Extension](https://img.shields.io/badge/Extension-Get%20Cookies.txt-orange?logo=googlechrome)

#### **Bước 5️⃣: Lưu Cookies**

Paste cookies vào file `download/main/cookies.txt`

```plaintext
📄 download/main/cookies.txt
└── [Paste cookies ở đây]
```

> [!WARNING]
> **Cookies có thời hạn sử dụng!** Khi hết hạn (thường sau vài tuần), bạn cần lấy cookies mới bằng cách lặp lại bước 4-5.

#### **Bước 6️⃣: Chạy chương trình**

**Cách 1: Sử dụng file .bat (Windows)**

```bash
cd download
run.bat
```

**Cách 2: Chạy trực tiếp Python**

```bash
cd download/main/python
python main.py
```

Chọn **option 1** trong menu, sau đó:

- **Nhập thủ công**: Paste link video Facebook
- **Tự động từ file**: Đặt links vào `download/main/getlink/link.txt` (mỗi link một dòng)

#### **Bước 7️⃣: Xem kết quả**

Video đã tải sẽ được lưu trong thư mục:

```plaintext
📁 download/finish/
└── video_downloaded.mp4
```

---

### 🎵 Chế độ 2: YouTube Video/Audio

> [!TIP]
> Đơn giản và không cần cookies!

1. Chạy chương trình → chọn **option 2**
2. Paste link YouTube video
3. Chọn chất lượng (nếu được hỏi)
4. Đợi tải xong → kiểm tra thư mục `download/finish/`

**Ví dụ:**

```bash
> 2
Nhập URL YouTube:
> https://www.youtube.com/watch?v=dQw4w9WgXcQ

✅ Đang tải video...
✅ Hoàn thành! File lưu tại: download/finish/
```

---

### 🌐 Chế độ 3: Đa Web - Advanced (Multi-thread)

> [!TIP]
> Hỗ trợ hơn 1000+ trang web với 11 strategies tải thông minh!

#### **Các Strategy được hỗ trợ:**

| # | Strategy | Mô tả |
|---|----------|-------|
| 1️⃣ | **HLS/TS Specialist** | Chuyên xử lý M3U8, HLS streams |
| 2️⃣ | **Direct YT-DLP** | Tải trực tiếp qua yt-dlp |
| 3️⃣ | **Extract Streams** | Trích xuất stream URLs |
| 4️⃣ | **iFrame Detection** | Phát hiện video trong iframe |
| 5️⃣ | **Aggressive Scan** | Quét toàn bộ source code |
| 6️⃣ | **With Cookies** | Sử dụng cookies auth |
| 7️⃣ | **JSON Extraction** | Trích xuất từ JSON data |
| 8️⃣ | **Meta Tags & Schema** | Đọc metadata |
| 9️⃣ | **HTML5 Video Tags** | Tìm thẻ `<video>` |
| 🔟 | **CDN Detection** | Phát hiện CDN URLs |
| 1️⃣1️⃣ | **Decode Obfuscated** | Giải mã URLs ẩn |

#### **Cách sử dụng:**

1. Chạy chương trình → chọn **option 3**
2. Paste URL trang web chứa video
3. Hệ thống tự động chạy **11 strategies song song**
4. Video tải về sẽ lưu tại `download/finish/mode3/`

**Ví dụ:**

```bash
> 3
Dán URL trang web:
> https://example.com/video-page

🚀 Đang chạy 11 strategies đồng thời...
✅ Strategy 1: HLS Specialist - Tải thành công!
✅ Strategy 3: Extract Streams - Tải thành công!
...
🎉 Tổng cộng: 3/11 strategies thành công
📁 File lưu tại: download/finish/mode3/
```

---

### 🖥️ Server Mode (Tải từ thiết bị khác)

> [!NOTE]
> Khởi động server để tải video từ các thiết bị trong cùng mạng LAN!

#### **Bật Server:**

Trong menu chính, chọn **option e**

```bash
> e
🚀 Đang khởi động server...
✅ Server đã khởi động!
🌐 Truy cập từ: http://192.168.1.XXX:8000
```

#### **Sử dụng từ thiết bị khác:**

1. Mở browser trên điện thoại/máy tính khác (cùng mạng WiFi)
2. Truy cập địa chỉ IP hiển thị (ví dụ: `http://192.168.1.100:8000`)
3. Paste link video → submit
4. Server sẽ tải và lưu vào `download/finish/`

#### **Tắt Server:**

Chọn **option e** lần nữa hoặc nhấn `Ctrl+C`

---

## 🗂️ Cấu trúc thư mục chi tiết

```plaintext
video-downloader/
│
├── 📁 download/
│   │
│   ├── 📁 main/
│   │   │
│   │   ├── 📁 engine/           ⭐ Engine files
│   │   │   ├── yt-dlp.exe
│   │   │   └── ffmpeg.exe
│   │   │
│   │   ├── 📁 python/           ⭐ Source code
│   │   │   ├── main.py
│   │   │   └── server.py
│   │   │
│   │   ├── 📁 getlink/          ⭐ File chứa links
│   │   │   └── link.txt         (Mỗi link 1 dòng)
│   │   │
│   │   ├── 📄 cookies.txt       ⭐ Facebook cookies
│   │   └── 📄 source.txt        ⭐ Page source
│   │
│   ├── 📁 finish/               ⭐ Thư mục output
│   │   ├── 📁 mode3/            (Chế độ 3)
│   │   │   ├── *.mp4
│   │   │   └── 📁 other/
│   │   └── *.mp4                (Chế độ 1, 2)
│   │
│   └── 📄 run.bat               ⭐ File chạy nhanh (Windows)
│
└── 📄 README.md
```

---

## 💡 Câu hỏi thường gặp

<details>
<summary><b>❓ Cookies Facebook bị hết hạn, phải làm sao?</b></summary>

<br>

Cookies thường hết hạn sau 2-4 tuần. Bạn cần:

1. Mở lại Facebook trong browser
2. Dùng extension "Get cookies.txt LOCALLY" để lấy cookies mới
3. Paste vào file `cookies.txt`
4. Chạy lại chương trình

</details>

<details>
<summary><b>❓ Tại sao không tải được video Facebook?</b></summary>

<br>

Kiểm tra các điểm sau:

- ✅ Đã paste đúng **source page** vào `source.txt`?
- ✅ Cookies trong `cookies.txt` còn hạn?
- ✅ Link video có public hoặc bạn có quyền xem?
- ✅ File `yt-dlp.exe` và `ffmpeg.exe` đã có trong thư mục `engine/`?

</details>

<details>
<summary><b>❓ Chế độ 3 tải video bị lỗi?</b></summary>

<br>

Một số trang web có DRM hoặc yêu cầu đăng nhập:

- 🔸 Video có DRM (Netflix, Disney+, ...) → **Không thể tải**
- 🔸 Trang yêu cầu login → Thử dùng cookies (chế độ 6)
- 🔸 Video dạng livestream → Có thể không hỗ trợ

Công cụ hỗ trợ **hầu hết** trang web thông thường nhưng không phải tất cả.

</details>

<details>
<summary><b>❓ Làm sao tăng tốc độ tải?</b></summary>

<br>

Có thể chỉnh số luồng tải trong file `main.py`:

```python
# Dòng 45-49
MAX_WORKERS = 6          # Chế độ 3 (tăng lên 10-12 nếu mạng tốt)
MODE1_MAX_WORKERS = 6    # Chế độ 1 (tăng lên 8-10)
```

⚠️ **Chú ý:** Tăng quá cao có thể gây quá tải CPU/mạng.

</details>

<details>
<summary><b>❓ Server mode hoạt động như thế nào?</b></summary>

<br>

Server tạo một web interface cho phép:

- 📱 Tải video từ điện thoại (cùng WiFi)
- 💻 Tải từ máy tính khác trong mạng LAN
- 🌐 Truy cập qua địa chỉ IP: `http://192.168.x.x:8000`

Chỉ cần **cùng mạng WiFi/LAN** là dùng được!

</details>

---

## ⚠️ Lưu ý quan trọng

> [!WARNING]
> **Cookies bảo mật:**
> - Không chia sẻ file `cookies.txt` cho người khác
> - Cookies chứa thông tin đăng nhập Facebook của bạn
> - Xóa cookies khi không sử dụng nữa

> [!CAUTION]
> **Bản quyền:**
> - Chỉ tải video bạn có quyền truy cập
> - Không phân phối lại nội dung có bản quyền
> - Tool chỉ phục vụ mục đích cá nhân, học tập

---

## 🤝 Đóng góp

Mọi đóng góp đều được chào đón! Nếu bạn muốn cải thiện project:

1. Fork repository
2. Tạo branch mới (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Tạo Pull Request

---

## 📜 License

Dự án này được phân phối dưới giấy phép MIT. Xem file `LICENSE` để biết thêm chi tiết.

---

## 📞 Liên hệ & Hỗ trợ

- 🐛 **Báo lỗi:** [Issues](https://github.com/your-username/video-downloader/issues)
- 💬 **Thảo luận:** [Discussions](https://github.com/your-username/video-downloader/discussions)
- ⭐ **Nếu thấy hữu ích, hãy cho project 1 star nhé!**

---

<div align="center">

**Made with ❤️ by [Your Name]**

⬆️ [Back to top](#-video-downloader---multi-mode)

</div>
