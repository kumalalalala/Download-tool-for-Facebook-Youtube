# 🎬 Video Downloader Multi-Tool

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.7+-blue?style=flat-square&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/yt--dlp-required-brightgreen?style=flat-square" alt="yt-dlp">
  <img src="https://img.shields.io/badge/ffmpeg-required-orange?style=flat-square" alt="ffmpeg">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" alt="License">
</p>

**Video Downloader Multi-Tool** là công cụ tải video/audio mạnh mẽ từ **Facebook**, **YouTube** và **hầu hết các trang web** (HLS, MP4, MP3, iframe, JSON-LD...).  
Tích hợp **đa luồng**, **trích xuất URL thông minh**, **cookies** và **server local** – tất cả trong một giao diện dòng lệnh đơn giản.

---

## 📦 PHẦN 1: GIỚI THIỆU

### ✨ Tính năng nổi bật

✅ **Facebook Video** – Tải video từ post, story, fanpage (cần cookies).  
✅ **YouTube** – Tải MP4 (chọn độ phân giải) hoặc MP3 chất lượng cao nhất.  
✅ **Đa Web (Mode 3)** – Quét và tải media từ **bất kỳ website nào**:
  - HLS (`.m3u8`), DASH (`.mpd`), MP4, MP3, TS segments.
  - Phát hiện iframe, meta tags, JSON-LD, CDN, URL bị obfuscate.
  - Chạy **10+ chiến lược trích xuất**, chỉ hiển thị chiến lược **thành công**.
✅ **Đa luồng** – Tải song song với `6 workers` (có thể tùy chỉnh).  
✅ **Server Local** – Bật server để các thiết bị trong cùng mạng gửi link tải về máy trung tâm.  
✅ **Tự động phân loại** – File tải xong được chuyển vào thư mục `finish/` theo từng chế độ.  
✅ **Hỗ trợ cookies** – Dùng cho Facebook hoặc các trang yêu cầu đăng nhập.  

---

## 📁 PHẦN 2: HƯỚNG DẪN SỬ DỤNG

### 📂 2.1. Cấu trúc thư mục (bắt buộc)

```
download/                           # Thư mục gốc (tự đặt tên)
├── main/                           # Thư mục chính chứa mã nguồn
│   ├── main.py                     # File chính
│   ├── server.py                  # (Tự tạo) Server local
│   ├── engine/                    # Chứa yt-dlp.exe và ffmpeg.exe
│   │   ├── yt-dlp.exe
│   │   └── ffmpeg.exe
│   ├── cookies.txt               # Cookies Facebook (export từ trình duyệt)
│   ├── source.txt                # HTML source Facebook để trích link
│   └── getlink/                  # Thư mục chứa link.txt sau khi trích
│       └── link.txt
└── finish/                       # Tất cả video đã tải xong
    ├── mode3/                    # Video/audio từ chế độ đa web
    └── mode3/other/             # File khác (txt, json, …)
```

> ⚠️ **Bắt buộc**: Đặt `yt-dlp.exe` và `ffmpeg.exe` trong `main/engine/` **trước khi chạy**.

---

### 🛠️ 2.2. Chuẩn bị

| Yêu cầu               | Hướng dẫn                                                                         |
|-----------------------|-----------------------------------------------------------------------------------|
| **Python 3.7+**       | Tải từ [python.org](https://www.python.org/downloads/)                           |
| **yt-dlp.exe**        | [Tải mới nhất](https://github.com/yt-dlp/yt-dlp/releases) → copy vào `engine/`   |
| **ffmpeg.exe**        | [Tải bản full](https://ffmpeg.org/download.html) → copy vào `engine/`            |
| **Cookies extension** | [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) (dùng cho Facebook) |

---

## 🎯 2.3. Các chế độ tải chi tiết

<details>
<summary><b>📘 Chế độ 1 – FACEBOOK VIDEO (cần cookies)</b></summary>

#### 🟪 **Bước 1: Lấy source trang**
- Truy cập bài viết / story Facebook chứa video.
- Nhấp chuột phải → **View Page Source** (Ctrl+U).
- **Copy toàn bộ nội dung** → tạo file `main/source.txt` và dán vào.

#### 🟪 **Bước 2: Export cookies**
- Vào **Facebook.com** (đã đăng nhập).
- Mở extension **Get cookies.txt LOCALLY** → nhấn **Copy**.
- Tạo file `main/cookies.txt` và **dán nội dung vừa copy**.

#### 🟪 **Bước 3: Chạy tool và trích link**
- Mở terminal tại thư mục `download/` (hoặc nhấn `run.bat` nếu có).
- Chạy:  
  ```bash
  python main/main.py
  ```
- Chọn **`1`** (Facebook).
- Tool tự động đọc `source.txt` → sinh danh sách link tại `main/getlink/link.txt`.

#### 🟪 **Bước 4: Tải video**
- Trong menu Facebook, chọn:
  - **`1`** – Nhập link thủ công (dán từng link).
  - **`2`** – Tải tự động từ `link.txt` (đa luồng, ghi trực tiếp vào `finish/`).
- Video sẽ xuất hiện trong thư mục **`finish/`**.

> ⚠️ **Cookies có hạn**, khi hết hạn chỉ cần export lại và ghi đè vào `cookies.txt`.  
> 💡 Nếu không có `source.txt`, tool sẽ báo lỗi và hướng dẫn cụ thể.

</details>

---

<details>
<summary><b>🎥 Chế độ 2 – YOUTUBE</b></summary>

1. Tại menu chính, chọn **`2`**.
2. Dán URL video YouTube.
3. Chọn định dạng:
   - **`1`** – MP3 (audio, chất lượng cao nhất).
   - **`2`** – MP4 (video).
4. Nếu chọn MP4, tool sẽ quét các độ phân giải có sẵn → bạn chọn số tương ứng (hoặc `0` để auto).
5. Video/audio được lưu vào `finish/`.

</details>

---

<details>
<summary><b>🌐 Chế độ 3 – ĐA WEB (MODE 3 – mạnh nhất)</b></summary>

Chế độ này **tự động phát hiện và tải mọi nguồn media** từ bất kỳ website nào.

1. Tại menu chính, chọn **`3`**.
2. Dán URL trang web cần tải (Vimeo, Dailymotion, báo mạng, web phim, nhạc…).
3. Tool thực hiện:
   - 🔍 Chạy **10+ chiến lược trích xuất** (HLS, iframe, JSON, meta, CDN, decode…).
   - 📋 Gom tất cả URL media tìm được.
   - ⬇️ Tải **đa luồng** (mặc định 6 luồng).
   - 📁 Phân loại file:
     - `.mp4`, `.mp3` → `finish/mode3/`
     - File khác (`.txt`, `.json`, `.ts`…) → `finish/mode3/other/`
4. Kết thúc, tool hiển thị **bảng tổng kết chỉ với các chiến lược THÀNH CÔNG**.

✅ Hỗ trợ: `.m3u8`, `.mpd`, `.mp4`, `.mp3`, `.ts`, iframe, JSON-LD, Open Graph, Twitter Card, CDN, obfuscated URL…

</details>

---

<details>
<summary><b>🖧 TÍNH NĂNG SERVER LOCAL</b></summary>

Cho phép các thiết bị khác trong cùng mạng **gửi link tải về máy tính chạy tool**.

1. Tạo file `main/server.py` (ví dụ dùng Flask hoặc http.server).
2. Trong menu chính, nhấn **`e`**:
   - Nếu server chưa chạy → **bật**.
   - Nếu server đang chạy → **tắt**.
3. Các thiết bị khác truy cập `http://<IP_máy_tính>:<port>` và gửi URL.
4. Tool sẽ tự động tải và lưu vào `finish/`.

> 💡 Bạn có thể tự viết `server.py` đơn giản để nhận dữ liệu qua JSON hoặc form.

</details>

---

## ⌨️ 2.4. Tổng hợp lệnh nhanh

| Hành động                    | Lệnh / Phím tắt                      |
|-----------------------------|--------------------------------------|
| Chạy tool                   | `python main/main.py`               |
| Chế độ Facebook             | `1` → chọn `1` (thủ công) / `2` (tự động) |
| Chế độ YouTube              | `2` → dán link → chọn loại file     |
| Chế độ Đa Web (Mode 3)      | `3` → dán link                      |
| Bật/Tắt server local        | `e`                                 |
| Thoát tool                  | `q`                                 |

---

## ⚙️ 2.5. Tùy chỉnh nâng cao

Bạn có thể điều chỉnh các thông số trong file `main.py`:

```python
MAX_WORKERS = 6                # Số luồng tải đồng thời cho Mode 3
MODE1_MAX_WORKERS = 6         # Số luồng tải đồng thời cho Facebook
```

---

## ❓ 2.6. Khắc phục sự cố thường gặp

| Vấn đề                                  | Nguyên nhân & Cách xử lý                                                                           |
|-----------------------------------------|----------------------------------------------------------------------------------------------------|
| **Thiếu yt-dlp.exe / ffmpeg.exe**       | Tải và đặt đúng thư mục `main/engine/`. Tool sẽ báo lỗi cụ thể.                                   |
| **Facebook không tải được**             | Cookies hết hạn → export lại cookies.txt.                                                         |
| **Không tìm thấy link trong source.txt**| Source trang không chứa pattern video Facebook → thử story khác hoặc dùng link thủ công.          |
| **Mode 3 không tải được file nào**      | Trang web có DRM, yêu cầu JavaScript, hoặc token tạm thời. Tool đã cố gắng hết các chiến lược.   |
| **Server không hoạt động**              | Kiểm tra file `server.py` có tồn tại không. Viết lại server đơn giản hoặc dùng `http.server`.     |

---

## 📄 Giấy phép

Dự án được phân phối dưới giấy phép **MIT**.  
Vui lòng đọc file `LICENSE` để biết thêm chi tiết.

---

<p align="center">
  <b>🎉 Chúc bạn tải video thành công! 🎉</b><br>
  <i>Nếu gặp lỗi hoặc có ý tưởng, hãy mở issue hoặc tạo pull request.</i>
</p>
