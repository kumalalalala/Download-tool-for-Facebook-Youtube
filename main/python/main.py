#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
import shutil
import glob
import re
import json
from pathlib import Path
import urllib.request
import urllib.error
import urllib.parse
import base64
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse

# ================== CẤU TRÚC THƯ MỤC ==================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # download/main/python/
MAIN_DIR = os.path.dirname(SCRIPT_DIR)  # download/main/
DOWNLOAD_DIR = os.path.dirname(MAIN_DIR)  # download/

ENGINE_DIR = os.path.join(MAIN_DIR, "engine")
YTDLP_EXE = os.path.join(ENGINE_DIR, "yt-dlp.exe")
FFMPEG_EXE = os.path.join(ENGINE_DIR, "ffmpeg.exe")

COOKIES_FILE = os.path.join(MAIN_DIR, "cookies.txt")
SOURCE_FILE = os.path.join(MAIN_DIR, "source.txt")

GETLINK_DIR = os.path.join(MAIN_DIR, "getlink")
LINK_FILE = os.path.join(GETLINK_DIR, "link.txt")

FINISH_DIR = os.path.join(DOWNLOAD_DIR, "finish")

# Mode 3 specific folders
MODE3_DIR = os.path.join(FINISH_DIR, "mode3")
MODE3_OTHER_DIR = os.path.join(MODE3_DIR, "other")

# Global flag to indicate mode3 active
MODE3_ACTIVE = False

# Threadpool config for mode3 downloads
MAX_WORKERS = 6  
# you can increase/decrease depending on your environment

# Threadpool config for mode1 (Facebook)
MODE1_MAX_WORKERS = 6  # số luồng đồng thời cho chế độ 1

# Server process management
SERVER_FILE = os.path.join(SCRIPT_DIR, "server.py")
server_process = None  # Global variable to track server process

# ================== REGEX PATTERN ==================
VIDEO_URL_REGEX = re.compile(
    r"https://www\.facebook\.com/[a-zA-Z0-9.\-_]+/videos/\d+/"
)

# ================== SERVER MANAGEMENT (ĐÃ CHỈNH SỬA) ==================
def is_server_running():
    """Kiểm tra xem server có đang chạy không"""
    global server_process
    if server_process is None:
        return False
    # Check if process is still running
    if server_process.poll() is None:
        return True
    else:
        server_process = None
        return False

def start_server():
    """Khởi động server.py"""
    global server_process
    
    if not os.path.isfile(SERVER_FILE):
        print(f"\n❌ Không tìm thấy file server.py tại: {SERVER_FILE}")
        print("📋 Vui lòng tạo file server.py trong thư mục: " + MAIN_DIR)
        input("\nNhấn Enter để quay lại...")
        return False
    
    try:
        # CHỈNH SỬA: Thông báo ngắn gọn
        print("\n🚀 Đang khởi động server...")
        
        # Start server process and redirect output to current console
        if sys.platform == "win32":
            # Windows: Use creationflags to show console output
            server_process = subprocess.Popen(
                [sys.executable, SERVER_FILE],
                cwd=MAIN_DIR,
                stdout=sys.stdout,
                stderr=sys.stderr,
                stdin=sys.stdin,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            # Unix-like systems
            server_process = subprocess.Popen(
                [sys.executable, SERVER_FILE],
                cwd=MAIN_DIR,
                stdout=sys.stdout,
                stderr=sys.stderr,
                stdin=sys.stdin,
                preexec_fn=os.setsid
            )
        
        # Wait a bit to check if server started successfully
        time.sleep(1)
        if server_process.poll() is None:
            # CHỈNH SỬA: Chỉ hiện thông báo thành công và return ngay
            print("✅ Server đã khởi động thành công!")
            return True
        else:
            print("❌ Server khởi động thất bại (process terminated immediately)")
            server_process = None
            input("\nNhấn Enter để quay lại...")
            return False
            
    except Exception as e:
        print(f"\n❌ Lỗi khi khởi động server: {str(e)}")
        server_process = None
        input("\nNhấn Enter để quay lại...")
        return False

def stop_server():
    """Tắt server đang chạy"""
    global server_process
    
    if server_process is None:
        print("\n⚠️  Không có server nào đang chạy")
        # CHỈNH SỬA: Bỏ input wait
        return False
    
    try:
        print("\n🛑 Đang tắt server...")
        
        if sys.platform == "win32":
            # Windows: Terminate process
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()
                server_process.wait()
        else:
            # Unix-like: Kill process group
            try:
                os.killpg(os.getpgid(server_process.pid), 15)  # SIGTERM
                server_process.wait(timeout=5)
            except:
                try:
                    os.killpg(os.getpgid(server_process.pid), 9)  # SIGKILL
                except:
                    pass
        
        # CHỈNH SỬA: Thông báo xong và return ngay
        print("✅ Server đã được tắt")
        server_process = None
        return True
        
    except Exception as e:
        print(f"\n❌ Lỗi khi tắt server: {str(e)}")
        # Force reset
        server_process = None
        input("\nNhấn Enter để quay lại...")
        return False

def toggle_server():
    """Toggle server state (start if stopped, stop if running)"""
    if is_server_running():
        return stop_server()
    else:
        return start_server()

# ================== KIỂM TRA FILE ENGINE ==================
def check_engine_files():
    """Kiểm tra yt-dlp.exe và ffmpeg.exe"""
    missing = []

    if not os.path.isfile(YTDLP_EXE):
        missing.append(("yt-dlp.exe", ENGINE_DIR))

    if not os.path.isfile(FFMPEG_EXE):
        missing.append(("ffmpeg.exe", ENGINE_DIR))

    if missing:
        error_msg = f"❌ THIẾU {len(missing)} FILE ENGINE:\n"
        for filename, directory in missing:
            error_msg += f"   - {filename} (cần đặt trong: {directory})\n"
        error_msg += "\n📋 HƯỚNG DẪN:\n   1. Tải các file còn thiếu\n   2. Đặt vào đúng thư mục như trên\n   3. Chạy lại chương trình"
        return False, error_msg

    return True, None


# ================== MOVE FINISHED FILE (DÙ PHẦN LỚN KHÔNG CẦN CHO MODE1) ==================
def move_finished_videos(before_files):
    """Di chuyển video đã tải vào thư mục finish/ (phiên bản cũ cho các chế độ khác)"""
    after_files = set(glob.glob(os.path.join(DOWNLOAD_DIR, "*.*")))
    new_files = after_files - before_files

    for file in new_files:
        base = os.path.basename(file)
        dst = os.path.join(FINISH_DIR, base)
        try:
            shutil.move(file, dst)
            print(f"📁 Đã chuyển vào finish/: {base}")
        except Exception:
            try:
                shutil.move(file, dst)
            except:
                pass


def move_new_files_to_mode3(before_files, output_dir=DOWNLOAD_DIR):
    """
    Di chuyển các tệp mới (sau download) vào finish/mode3 (mp3/mp4)
    Các file khác -> finish/mode3/other
    Trả về danh sách các file đã chuyển (tuples: (src, dst))
    """
    os.makedirs(MODE3_DIR, exist_ok=True)
    os.makedirs(MODE3_OTHER_DIR, exist_ok=True)

    after_files = set(glob.glob(os.path.join(output_dir, "*.*")))
    new_files = after_files - before_files
    moved = []

    for file in new_files:
        name = os.path.basename(file)
        ext = os.path.splitext(name)[1].lower()
        try:
            if ext in (".mp4", ".mp3"):
                dst = os.path.join(MODE3_DIR, name)
            else:
                dst = os.path.join(MODE3_OTHER_DIR, name)

            # If destination exists, add timestamp suffix
            if os.path.exists(dst):
                base, e = os.path.splitext(name)
                dst = os.path.join(os.path.dirname(dst), f"{base}_{int(time.time())}{e}")

            shutil.move(file, dst)
            moved.append((file, dst))
        except Exception as e:
            # best effort
            print(f"⚠️ Không thể di chuyển {name}: {str(e)[:80]}")
    return moved


# ========================================================================
# ======================= CHẾ ĐỘ 1: FACEBOOK =============================
# ========================================================================

def extract_links_silent():
    """Đọc source.txt → xuất link.txt vào folder getlink/"""
    os.makedirs(GETLINK_DIR, exist_ok=True)

    source_path = Path(SOURCE_FILE)

    if not source_path.exists():
        return False, f"❌ THIẾU FILE: {SOURCE_FILE}\n\n📋 HƯỚNG DẪN:\n   1. Tạo file 'source.txt' trong thư mục: {MAIN_DIR}\n   2. Dán HTML source code của Facebook vào file đó\n   3. Chạy lại chương trình"

    try:
        raw_html = source_path.read_text(encoding="utf-8", errors="ignore")
        html = raw_html.replace("\\/", "/")
        matches = set(VIDEO_URL_REGEX.findall(html))

        output_path = Path(LINK_FILE)
        if output_path.exists():
            output_path.unlink()

        with open(LINK_FILE, "w", encoding="utf-8") as f:
            for link in sorted(matches):
                f.write(link + "\n")

        return True, None

    except Exception as e:
        return False, f"❌ LỖI khi xử lý source.txt: {str(e)}"


def check_facebook_files():
    """Kiểm tra cookies.txt cho Facebook"""
    if not os.path.isfile(COOKIES_FILE):
        return False, f"❌ THIẾU FILE: cookies.txt\n\n📋 HƯỚNG DẪN:\n   1. Tạo file 'cookies.txt' trong thư mục: {MAIN_DIR}\n   2. Export cookies từ Facebook\n   3. Chạy lại chương trình"
    return True, None


def is_cookie_expired(stderr_text: str) -> bool:
    """Kiểm tra cookies có hết hạn không"""
    keywords = [
        "login required",
        "you must log in",
        "this video is private",
        "http error 403",
        "forbidden",
        "cookies",
        "unsupported url"
    ]

    text = (stderr_text or "").lower()
    return any(k in text for k in keywords)


def download_facebook_video(url):
    """Tải video từ URL Facebook (phiên bản cũ, đồng bộ)"""
    before_files = set(glob.glob(os.path.join(DOWNLOAD_DIR, "*.*")))

    cmd = [
        YTDLP_EXE,
        "--ffmpeg-location", ENGINE_DIR,
        "--cookies", COOKIES_FILE,
        "--no-playlist",
        "-f", "bv*+ba/b",
        "--merge-output-format", "mp4",
        url
    ]

    print("\n⬇ Đang tải...\n")

    result = subprocess.run(
        cmd,
        stdout=None,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        if is_cookie_expired(result.stderr):
            print("\n🚨 COOKIES FACEBOOK ĐÃ HẾT HẠN / KHÔNG HỢP LỆ")
            print("👉 Vui lòng export lại cookies.txt rồi chạy lại tool.")
            input("\nNhấn Enter để thoát...")
            sys.exit(1)

        print("❌ Tải thất bại (lỗi khác).")
        return

    print("✅ Tải xong.")
    move_finished_videos(before_files)


def facebook_mode_manual():
    """Facebook: Nhập link thủ công"""
    while True:
        url = input("\nDán URL video Facebook (q để quay lại):\n> ").strip()

        if url.lower() in ("q", "quit", "exit"):
            break

        if not url:
            print("⚠️  URL trống.")
            continue

        download_facebook_video(url)


# ========== New: multi-threaded Facebook worker and parallel runner (WRITE DIRECTLY TO FINISH) ==========

def facebook_download_worker(tmp_index, url):
    """
    Worker chạy yt-dlp cho một URL Facebook **và ghi trực tiếp vào FINISH_DIR**.
    Sử dụng unique_suffix (timestamp + index) để tránh xung đột tên.
    Trả về dict: {"url": url, "success": bool, "error": str or None, "cookie_expired": bool, "files": [paths]}
    """
    result_info = {"url": url, "success": False, "error": None, "cookie_expired": False, "files": []}
    unique_suffix = f"{int(time.time())}_{tmp_index}"
    output_template = os.path.join(FINISH_DIR, f"%(title)s_{unique_suffix}.%(ext)s")

    # Ensure finish dir exists
    os.makedirs(FINISH_DIR, exist_ok=True)

    cmd = [
        YTDLP_EXE,
        "--ffmpeg-location", ENGINE_DIR,
        "--cookies", COOKIES_FILE,
        "--no-playlist",
        "-f", "bv*+ba/b",
        "--merge-output-format", "mp4",
        "-o", output_template,
        url
    ]

    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3600)
        stderr = proc.stderr or ""
        stdout = proc.stdout or ""

        if proc.returncode != 0:
            # check cookie expired
            if is_cookie_expired(stderr):
                result_info["error"] = "cookies_expired"
                result_info["cookie_expired"] = True
                return result_info

            # otherwise failure
            # Capture some stderr for debugging but keep concise
            err = stderr.strip().splitlines()
            result_info["error"] = err[-1][:400] if err else "unknown_error"
            return result_info

        # Success: locate files in FINISH_DIR that include our unique_suffix
        pattern = os.path.join(FINISH_DIR, f"*_{unique_suffix}.*")
        matched = glob.glob(pattern)
        # It's possible yt-dlp used different naming (rare). If none matched, attempt to find recently modified files.
        if not matched:
            # fallback: find files modified in last 120 seconds
            now = time.time()
            recent = []
            for f in glob.glob(os.path.join(FINISH_DIR, "*.*")):
                try:
                    mtime = os.path.getmtime(f)
                    if now - mtime < 120:
                        recent.append(f)
                except:
                    continue
            matched = recent

        # Record found files
        for f in matched:
            # ignore temporary .Part or incomplete? include them as user requested direct writes
            result_info["files"].append(f)

        if result_info["files"]:
            result_info["success"] = True
        else:
            # If no files found, still treat as failure
            result_info["error"] = result_info.get("error") or "no_files_found_after_ytdlp"
            result_info["success"] = False

        return result_info

    except subprocess.TimeoutExpired:
        result_info["error"] = "timeout"
        return result_info
    except Exception as e:
        result_info["error"] = f"exception: {str(e)}"
        return result_info


def facebook_mode_from_file():
    """Facebook: Đọc link từ file link.txt và tải nhiều luồng cùng lúc (ghi trực tiếp vào finish/)"""
    if not os.path.isfile(LINK_FILE):
        print(f"❌ Không tìm thấy {LINK_FILE}")
        print("💡 Hãy chạy lại từ đầu hoặc tạo file link.txt thủ công")
        return

    with open(LINK_FILE, "r", encoding="utf-8") as f:
        links = [l.strip() for l in f if l.strip()]

    if not links:
        print("⚠️  link.txt trống, không có link nào để tải.")
        return

    # kiểm tra cookies trước khi chạy đa luồng
    success, error = check_facebook_files()
    if not success:
        print(error)
        input("\n❌ Không thể tiếp tục. Nhấn Enter để quay lại...")
        return

    total = len(links)
    print(f"\n📄 Đang tải {total} link từ link.txt (đa luồng với {MODE1_MAX_WORKERS} workers). Ghi trực tiếp vào {FINISH_DIR}\n")

    # Run with ThreadPoolExecutor
    results = []
    cookie_issue_detected = False

    with ThreadPoolExecutor(max_workers=MODE1_MAX_WORKERS) as executor:
        future_to_url = {}
        for i, url in enumerate(links, start=1):
            future = executor.submit(facebook_download_worker, i, url)
            future_to_url[future] = url

        completed = 0
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                info = future.result()
            except Exception as e:
                info = {"url": url, "success": False, "error": f"exception: {str(e)}"}
            results.append(info)
            completed += 1
            status = "OK" if info.get("success") else "FAIL"
            # Minimal progress print
            print(f"Progress: {completed}/{total} — {status} — {url[:80]}")
            if info.get("cookie_expired"):
                cookie_issue_detected = True

    # Summary
    success_count = sum(1 for r in results if r.get("success"))
    fail_count = total - success_count

    print("\n" + "=" * 60)
    print("📊 TÓM TẮT FACEBOOK DOWNLOAD (MODE 1)")
    print("=" * 60)
    print(f"  Tổng links: {total}")
    print(f"  Tải thành công: {success_count}")
    print(f"  Tải thất bại: {fail_count}")
    if cookie_issue_detected:
        print("\n🚨 Một số tải thất bại do cookies hết hạn / không hợp lệ.")
        print("👉 Vui lòng cập nhật file cookies.txt và thử lại các links thất bại thủ công.")
    print("=" * 60)


def mode_facebook():
    """Chế độ tải Facebook"""
    print("\n" + "="*60)
    print("📘 CHẾ ĐỘ: FACEBOOK VIDEO DOWNLOADER")
    print("="*60)

    # Kiểm tra file
    success, error = extract_links_silent()
    if not success:
        print(error)
        input("\n❌ Không thể tiếp tục. Nhấn Enter để quay lại...")
        return

    success, error = check_facebook_files()
    if not success:
        print(error)
        input("\n❌ Không thể tiếp tục. Nhấn Enter để quay lại...")
        return

    # Menu Facebook
    while True:
        print("\n1 - Nhập link trực tiếp")
        print("2 - Đọc link từ link.txt (đa luồng vào finish/)")
        print("q - Quay lại menu chính")

        c = input("> ").strip().lower()

        if c == "1":
            facebook_mode_manual()
        elif c == "2":
            facebook_mode_from_file()
        elif c == "q":
            break
        else:
            print("⚠️  Lựa chọn không hợp lệ.")


# ========================================================================
# ======================= CHẾ ĐỘ 2: YOUTUBE =============================
# ========================================================================

def get_youtube_formats(url):
    """Quét các format của video YouTube"""
    cmd = [
        YTDLP_EXE,
        "--ffmpeg-location", ENGINE_DIR,
        "--list-formats",
        "--no-playlist",
        url
    ]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:
            return None

        return result.stdout

    except Exception as e:
        print(f"❌ Lỗi khi quét format: {str(e)}")
        return None


def extract_video_resolutions(format_list):
    """Trích xuất các độ phân giải video từ danh sách format"""
    resolutions = {}

    lines = format_list.split('\n')
    for line in lines:
        # Tìm các dòng chứa thông tin format
        if 'mp4' in line.lower() and 'x' in line:
            parts = line.split()
            format_id = parts[0] if parts else None

            # Tìm độ phân giải (ví dụ: 1920x1080, 1280x720)
            for part in parts:
                if 'x' in part and part.replace('x', '').replace('p', '').isdigit():
                    resolution = part
                    if resolution not in resolutions and format_id:
                        resolutions[resolution] = format_id
                    break

    return resolutions


def download_youtube_mp3(url):
    """Tải audio từ YouTube với chất lượng cao nhất"""
    before_files = set(glob.glob(os.path.join(DOWNLOAD_DIR, "*.*")))

    cmd = [
        YTDLP_EXE,
        "--ffmpeg-location", ENGINE_DIR,
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "0",
        "--no-playlist",
        "-o", os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s"),
        url
    ]

    print("\n⬇ Đang tải MP3 (chất lượng cao nhất)...\n")

    result = subprocess.run(cmd, stdout=None, stderr=subprocess.PIPE, text=True)

    if result.returncode != 0:
        print("❌ Tải thất bại.")
        return

    print("✅ Tải xong.")
    move_finished_videos(before_files)


def download_youtube_mp4(url, resolution=None):
    """Tải video từ YouTube"""
    before_files = set(glob.glob(os.path.join(DOWNLOAD_DIR, "*.*")))

    if resolution:
        # Tải với độ phân giải cụ thể
        cmd = [
            YTDLP_EXE,
            "--ffmpeg-location", ENGINE_DIR,
            "-f", f"bestvideo[height<={resolution}]+bestaudio/best[height<={resolution}]",
            "--merge-output-format", "mp4",
            "--no-playlist",
            "-o", os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s"),
            url
        ]
    else:
        # Tải với chất lượng tốt nhất
        cmd = [
            YTDLP_EXE,
            "--ffmpeg-location", ENGINE_DIR,
            "-f", "bestvideo+bestaudio/best",
            "--merge-output-format", "mp4",
            "--no-playlist",
            "-o", os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s"),
            url
        ]

    print(f"\n⬇ Đang tải MP4{' (' + str(resolution) + 'p)' if resolution else ' (chất lượng cao nhất)'}...\n")

    result = subprocess.run(cmd, stdout=None, stderr=subprocess.PIPE, text=True)

    if result.returncode != 0:
        print("❌ Tải thất bại.")
        return

    print("✅ Tải xong.")
    move_finished_videos(before_files)


def mode_youtube():
    """Chế độ tải YouTube"""
    print("\n" + "="*60)
    print("🎥 CHẾ ĐỘ: YOUTUBE DOWNLOADER")
    print("="*60)

    while True:
        url = input("\nDán URL video YouTube (q để quay lại):\n> ").strip()

        if url.lower() in ("q", "quit", "exit"):
            break

        if not url:
            print("⚠️  URL trống.")
            continue

        # Chọn định dạng
        print("\nChọn định dạng:")
        print("1 - MP3 (Audio)")
        print("2 - MP4 (Video)")
        print("q - Hủy")

        format_choice = input("> ").strip().lower()

        if format_choice == "q":
            continue
        elif format_choice == "1":
            download_youtube_mp3(url)
        elif format_choice == "2":
            # Quét độ phân giải
            print("\n🔍 Đang quét các độ phân giải có sẵn...")

            format_list = get_youtube_formats(url)

            if not format_list:
                print("❌ Không thể quét độ phân giải. Tải với chất lượng mặc định...")
                download_youtube_mp4(url)
                continue

            resolutions = extract_video_resolutions(format_list)

            if not resolutions:
                print("⚠️  Không tìm thấy độ phân giải cụ thể. Tải với chất lượng tốt nhất...")
                download_youtube_mp4(url)
                continue

            # Hiển thị danh sách độ phân giải
            print("\nCác độ phân giải có sẵn:")
            sorted_res = sorted(resolutions.keys(), key=lambda x: int(x.split('x')[1]) if 'x' in x else 0, reverse=True)

            for i, res in enumerate(sorted_res, 1):
                print(f"{i} - {res}")
            print("0 - Chất lượng cao nhất (auto)")
            print("q - Hủy")

            res_choice = input("> ").strip().lower()

            if res_choice == "q":
                continue
            elif res_choice == "0":
                download_youtube_mp4(url)
            elif res_choice.isdigit():
                idx = int(res_choice) - 1
                if 0 <= idx < len(sorted_res):
                    selected_res = sorted_res[idx]
                    # Lấy height từ resolution (ví dụ: 1920x1080 → 1080)
                    height = selected_res.split('x')[1] if 'x' in selected_res else selected_res.replace('p', '')
                    download_youtube_mp4(url, height)
                else:
                    print("⚠️  Lựa chọn không hợp lệ.")
            else:
                print("⚠️  Lựa chọn không hợp lệ.")
        else:
            print("⚠️  Lựa chọn không hợp lệ.")


# ========================================================================
# ============= CHẾ ĐỘ 3: ĐA WEB (NÂNG CẤP — CHẾ ĐỘ MỚI) ================
# ========================================================================

# ---------- Các helper fetch/extract (mở rộng để tìm MP3 nữa) ----------

def fetch_page_source(url):
    """Tải source code của trang web"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': url,
        }

        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read().decode('utf-8', errors='ignore')
        return content
    except Exception as e:
        # Silent fail for mode3
        return None


def extract_stream_urls(page_source):
    """Trích xuất m3u8/mpd/mp4/mp3 URLs từ page source (mở rộng mp3)"""
    if not page_source:
        return []

    stream_urls = []

    # Pattern cho m3u8
    m3u8_pattern = re.compile(r'(https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*)', re.IGNORECASE)
    m3u8_matches = m3u8_pattern.findall(page_source)
    stream_urls.extend(m3u8_matches)

    # Pattern cho mpd (DASH)
    mpd_pattern = re.compile(r'(https?://[^\s"\'<>]+\.mpd[^\s"\'<>]*)', re.IGNORECASE)
    mpd_matches = mpd_pattern.findall(page_source)
    stream_urls.extend(mpd_matches)

    # Pattern cho mp4 URLs
    mp4_pattern = re.compile(r'(https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*)', re.IGNORECASE)
    mp4_matches = mp4_pattern.findall(page_source)
    stream_urls.extend(mp4_matches)

    # Pattern cho mp3 URLs (mở rộng)
    mp3_pattern = re.compile(r'(https?://[^\s"\'<>]+\.mp3[^\s"\'<>]*)', re.IGNORECASE)
    mp3_matches = mp3_pattern.findall(page_source)
    stream_urls.extend(mp3_matches)

    # Clean URLs (remove HTML entities, quotes, etc.)
    cleaned_urls = []
    for url in stream_urls:
        url = re.sub(r'["\'\)>\]]+$', '', url)
        url = url.replace('&amp;', '&')
        if url and url not in cleaned_urls:
            cleaned_urls.append(url)

    return cleaned_urls


def extract_iframe_sources(page_source):
    """Trích xuất iframe video/audio sources"""
    if not page_source:
        return []

    iframe_pattern = re.compile(r'<iframe[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)
    iframes = iframe_pattern.findall(page_source)

    video_iframes = []
    media_keywords = ['player', 'embed', 'video', 'stream', 'vimeo', 'youtube', 'jwplayer', 'kaltura', 'brightcove', 'wistia', 'audio', 'soundcloud']

    for iframe in iframes:
        if any(keyword in iframe.lower() for keyword in media_keywords):
            if iframe.startswith('//'):
                iframe = 'https:' + iframe
            elif iframe.startswith('/'):
                # we can attempt to skip or make absolute later
                continue
            video_iframes.append(iframe)

    return video_iframes


def extract_json_video_urls(page_source):
    """Extract video/audio URLs từ JSON objects trong page source (mở rộng mp3)"""
    if not page_source:
        return []

    video_urls = []

    video_keys = [
        'videoUrl', 'videoURL', 'video_url',
        'streamUrl', 'streamURL', 'stream_url',
        'hlsUrl', 'hlsURL', 'hls_url', 'hls',
        'dashUrl', 'dashURL', 'dash_url', 'dash',
        'mp4Url', 'mp4URL', 'mp4_url', 'mp4',
        'mp3Url', 'mp3URL', 'mp3_url', 'mp3',
        'src', 'source', 'url', 'file',
        'playbackUrl', 'playback_url',
        'contentUrl', 'content_url',
        'm3u8', 'mpd'
    ]

    # Try to find JSON-like patterns
    json_patterns = [
        r'\{[^{}]*(?:"(?:' + '|'.join(video_keys) + r')":\s*"([^"]*(?:\.m3u8|\.mpd|\.mp4|\.mp3)[^"]*)")',
        r'\{[^{}]*(?:\'(?:' + '|'.join(video_keys) + r')\'\s*:\s*\'([^\']*(?:\.m3u8|\.mpd|\.mp4|\.mp3)[^\']*)\'))',
    ]

    for pattern in json_patterns:
        matches = re.findall(pattern, page_source, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                for m in match:
                    if m and ('http' in m or '.m3u8' in m or '.mp3' in m):
                        url = m.replace('\\/', '/')
                        video_urls.append(url)
            elif match and ('http' in match or '.m3u8' in match or '.mp3' in match):
                url = match.replace('\\/', '/')
                video_urls.append(url)

    # JSON-LD schema
    json_ld_pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
    json_ld_matches = re.findall(json_ld_pattern, page_source, re.DOTALL)

    for json_str in json_ld_matches:
        try:
            data = json.loads(json_str)
            if isinstance(data, dict):
                for key in ['contentUrl', 'embedUrl', 'url']:
                    if key in data and isinstance(data[key], str):
                        if any(ext in data[key] for ext in ['.mp4', '.m3u8', '.mp3']):
                            video_urls.append(data[key])
        except:
            pass

    return list(set(video_urls))


def extract_meta_video_urls(page_source):
    """Extract video/audio URLs từ meta tags và schema (mở rộng mp3)"""
    if not page_source:
        return []

    video_urls = []

    og_patterns = [
        r'<meta\s+property=["\']og:video:url["\']\s+content=["\'](.*?)["\']',
        r'<meta\s+property=["\']og:video:secure_url["\']\s+content=["\'](.*?)["\']',
        r'<meta\s+property=["\']og:video["\']\s+content=["\'](.*?)["\']',
        r'<meta\s+content=["\'](.*?)["\']\s+property=["\']og:video["\']',
    ]

    twitter_patterns = [
        r'<meta\s+name=["\']twitter:player:stream["\']\s+content=["\'](.*?)["\']',
        r'<meta\s+name=["\']twitter:player["\']\s+content=["\'](.*?)["\']',
    ]

    schema_patterns = [
        r'"@type"\s*:\s*"VideoObject"[^}]*"contentUrl"\s*:\s*"(.*?)"',
        r'"@type"\s*:\s*"VideoObject"[^}]*"embedUrl"\s*:\s*"(.*?)"',
    ]

    all_patterns = og_patterns + twitter_patterns + schema_patterns

    for pattern in all_patterns:
        matches = re.findall(pattern, page_source, re.IGNORECASE)
        for match in matches:
            if match and 'http' in match:
                url = match.replace('&amp;', '&').replace('&#x2F;', '/')
                video_urls.append(url)

    # Also look for audio meta tags (e.g., og:audio)
    audio_patterns = [
        r'<meta\s+property=["\']og:audio["\']\s+content=["\'](.*?)["\']',
        r'<meta\s+property=["\']og:audio:secure_url["\']\s+content=["\'](.*?)["\']',
    ]
    for pattern in audio_patterns:
        matches = re.findall(pattern, page_source, re.IGNORECASE)
        for match in matches:
            if match and 'http' in match:
                url = match.replace('&amp;', '&')
                video_urls.append(url)

    return list(set(video_urls))


def extract_video_tag_urls(page_source, base_url=None):
    """Extract URLs từ <video>, <audio> và <source> tags (mở rộng để include audio)"""
    if not page_source:
        return []

    video_urls = []

    video_src_patterns = [
        r'<video[^>]+src=["\']([^"\']+)["\']',
        r'<video[^>]+data-src=["\']([^"\']+)["\']',
        r'<video[^>]+data-video-src=["\']([^"\']+)["\']',
    ]

    audio_src_patterns = [
        r'<audio[^>]+src=["\']([^"\']+)["\']',
        r'<audio[^>]+data-src=["\']([^"\']+)["\']',
    ]

    source_patterns = [
        r'<source[^>]+src=["\']([^"\']+)["\']',
        r'<source[^>]+data-src=["\']([^"\']+)["\']',
    ]

    all_patterns = video_src_patterns + audio_src_patterns + source_patterns

    for pattern in all_patterns:
        matches = re.findall(pattern, page_source, re.IGNORECASE)
        for match in matches:
            if match:
                if any(ext in match.lower() for ext in ['.mp4', '.webm', '.ogg', '.m3u8', '.mpd', '.mp3', 'audio', 'video']):
                    url = match
                    if url.startswith('//'):
                        url = 'https:' + url
                    elif url.startswith('/'):
                        if base_url:
                            url = urljoin(base_url, url)
                        else:
                            continue
                    video_urls.append(url)

    return list(set(video_urls))


def extract_cdn_video_urls(page_source):
    """Extract video/audio URLs từ CDN và streaming services (mở rộng mp3)"""
    if not page_source:
        return []

    video_urls = []

    cdn_patterns = [
        r'https?://[^\s"\']+\.m3u8[^\s"\']*',
        r'https?://[^\s"\']+\.mpd[^\s"\']*',
        r'https?://[^\s"\']+\.mp4[^\s"\']*',
        r'https?://[^\s"\']+\.mp3[^\s"\']*',
        r'https?://[^/]*cloudflare[^/]*[^\s"\']*(?:\.mp4|\.m3u8|\.mp3)?',
        r'https?://[^/]*\.cloudflarestream\.com[^\s"\']*',
        r'https?://[^/]*\.cloudfront\.net[^\s"\']*(?:\.mp4|\.m3u8|\.mp3)?',
        r'https?://[^/]*\.b-cdn\.net[^\s"\']*(?:\.mp4|\.m3u8|\.mp3)?',
        r'https?://[^/]*\.fastly\.net[^\s"\']*(?:\.mp4|\.m3u8|\.mp3)?',
        r'https?://[^/]*\.akamaized\.net[^\s"\']*(?:\.mp4|\.m3u8|\.mp3)?',
        r'https?://[^/]*vimeocdn\.com[^\s"\']*',
        r'https?://[^/]*\.jwplatform\.com[^\s"\']*',
        r'https?://[^/]*\.wistia\.com[^\s"\']*',
        r'https?://[^/]*\.brightcove[^/]*[^\s"\']*',
        r'https?://[^/]*cdn[^/]*\.[^/]+[^\s"\'<>]*(?:\.mp4|\.m3u8|\.mpd|\.mp3)?',
    ]

    for pattern in cdn_patterns:
        matches = re.findall(pattern, page_source, re.IGNORECASE)
        for match in matches:
            url = match.replace('\\/', '/').strip().strip('"').strip("'")
            if url and url.startswith('http'):
                video_urls.append(url)

    return list(set(video_urls))


def decode_obfuscated_urls(page_source):
    """Decode các URLs bị encode/obfuscate (mở rộng mp3)"""
    if not page_source:
        return []

    decoded_urls = []

    # Base64
    base64_pattern = r'[A-Za-z0-9+/]{40,}={0,2}'
    base64_matches = re.findall(base64_pattern, page_source)
    for b64_str in base64_matches[:50]:
        try:
            decoded = base64.b64decode(b64_str).decode('utf-8', errors='ignore')
            if 'http' in decoded and any(ext in decoded for ext in ['.mp4', '.m3u8', '.mpd', '.mp3']):
                url_match = re.search(r'https?://[^\s"\'<>]+', decoded)
                if url_match:
                    decoded_urls.append(url_match.group(0))
        except:
            continue

    # percent encoded
    encoded_pattern = r'(?:https?%3A%2F%2F|http%3A%2F%2F)[A-Za-z0-9%._-]+'
    encoded_matches = re.findall(encoded_pattern, page_source)
    for encoded_url in encoded_matches:
        try:
            decoded = urllib.parse.unquote(encoded_url)
            if 'http' in decoded and any(ext in decoded for ext in ['.mp4', '.m3u8', '.mpd', '.mp3']):
                decoded_urls.append(decoded)
        except:
            continue

    # unicode escapes
    unicode_pattern = r'(?:\\u[0-9a-fA-F]{4})+'
    unicode_matches = re.findall(unicode_pattern, page_source)
    for unicode_str in unicode_matches[:20]:
        try:
            decoded = unicode_str.encode().decode('unicode-escape')
            if 'http' in decoded and any(ext in decoded for ext in ['.mp4', '.m3u8', '.mpd', '.mp3']):
                url_match = re.search(r'https?://[^\s"\'<>]+', decoded)
                if url_match:
                    decoded_urls.append(url_match.group(0))
        except:
            continue

    # hex encoded
    hex_pattern = r'\\x[0-9a-fA-F]{2}'
    if re.search(hex_pattern, page_source):
        hex_segments = re.findall(r'(?:\\x[0-9a-fA-F]{2}){10,}', page_source)
        for hex_seg in hex_segments[:10]:
            try:
                decoded = bytes.fromhex(hex_seg.replace('\\x', '')).decode('utf-8', errors='ignore')
                if 'http' in decoded:
                    url_match = re.search(r'https?://[^\s"\'<>]+', decoded)
                    if url_match and any(ext in url_match.group(0) for ext in ['.mp4', '.m3u8', '.mpd', '.mp3']):
                        decoded_urls.append(url_match.group(0))
            except:
                continue

    return list(set(decoded_urls))


def extract_all_m3u8_ts_urls(page_source, base_url=None):
    """
    Extract TẤT CẢ m3u8 và ts URLs từ page source
    """
    urls = {
        'm3u8': [],
        'ts': []
    }

    if not page_source:
        return urls

    m3u8_patterns = [
        r'https?://[^\s"\'<>]+\.m3u8(?:\?[^\s"\'<>]*)?',
        r'https?://[^\s"\'<>]+\.m3u(?:\?[^\s"\'<>]*)?',
        r'["\']([^"\']+\.m3u8(?:\?[^"\']*)?)["\']',
    ]

    ts_patterns = [
        r'https?://[^\s"\'<>]+\.ts(?:\?[^\s"\'<>]*)?',
        r'["\']([^"\']+\.ts(?:\?[^"\']*)?)["\']',
    ]

    for pattern in m3u8_patterns:
        matches = re.findall(pattern, page_source, re.IGNORECASE)
        for match in matches:
            url = match if match.startswith('http') else match
            if url and url not in urls['m3u8']:
                if base_url and not url.startswith('http'):
                    url = urljoin(base_url, url)
                if url.startswith('http'):
                    urls['m3u8'].append(url)

    for pattern in ts_patterns:
        matches = re.findall(pattern, page_source, re.IGNORECASE)
        for match in matches:
            url = match if match.startswith('http') else match
            if url and url not in urls['ts']:
                if base_url and not url.startswith('http'):
                    url = urljoin(base_url, url)
                if url.startswith('http'):
                    urls['ts'].append(url)

    urls['m3u8'] = list(set(urls['m3u8']))
    urls['ts'] = list(set(urls['ts']))

    return urls


# ---------- Download helpers specific for mode3 ----------

def download_direct_file_streaming(url, dest_path, referer=None, timeout=60):
    """Download a direct file (mp3/mp4/other) via streaming to dest_path with headers."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': referer or ''
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            # Determine filename extension if not provided
            CHUNK = 8192
            with open(dest_path, 'wb') as f:
                while True:
                    chunk = response.read(CHUNK)
                    if not chunk:
                        break
                    f.write(chunk)
        return True
    except Exception as e:
        return False


def run_yt_dlp_for_url(url, output_dir, referer=None, extra_args=None):
    """
    Sử dụng yt-dlp để tải URL. output_dir là thư mục tạm (DOWNLOAD_DIR).
    Trả về True nếu thành công (file sẽ được move bởi caller).
    """
    cmd = [
        YTDLP_EXE,
        "--ffmpeg-location", ENGINE_DIR,
        "-f", "best",
        "--merge-output-format", "mp4",
        "--no-playlist",
        "-o", os.path.join(output_dir, "%(title)s.%(ext)s"),
    ]

    if referer:
        cmd.extend(["--add-header", f"Referer:{referer}"])

    cmd.extend(["--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"])

    if extra_args:
        cmd.extend(extra_args)

    cmd.append(url)

    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.returncode == 0
    except Exception:
        return False


def mode3_download_worker(url, referer=None, idx=None, total=None):
    """
    Worker to download a single URL in mode3.
    Strategy:
    - If URL contains .m3u8 -> try yt-dlp (optimized HLS), fallback ffmpeg direct (if configured)
    - If URL endswith .mp4/.mp3 (direct file) -> stream download via urllib
    - Otherwise try yt-dlp
    """
    # Display simple progress
    if idx is not None and total is not None:
        prefix = f"Downloading {idx}/{total}: "
    else:
        prefix = "Downloading: "

    # Decide method
    u = url.lower()
    before_files = set(glob.glob(os.path.join(DOWNLOAD_DIR, "*.*")))

    try:
        # m3u8 -> use yt-dlp (it handles HLS nicely)
        if ".m3u8" in u or ".mpd" in u:
            success = run_yt_dlp_for_url(url, DOWNLOAD_DIR, referer=referer, extra_args=[
                "--hls-prefer-native",
                "--external-downloader", "ffmpeg",
                "--external-downloader-args", "ffmpeg:-protocol_whitelist file,http,https,tcp,tls,crypto"
            ])
            if success:
                move_new_files_to_mode3(before_files, output_dir=DOWNLOAD_DIR)
                return True, url

            # fallback: try ffmpeg direct (if binary exists)
            try:
                timestamp = int(time.time())
                tmp_out = os.path.join(DOWNLOAD_DIR, f"video_{timestamp}.mp4")
                cmd = [
                    FFMPEG_EXE,
                    "-protocol_whitelist", "file,http,https,tcp,tls,crypto",
                    "-user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                ]
                if referer:
                    cmd.extend(["-headers", f"Referer: {referer}\r\n"])
                cmd.extend(["-i", url, "-c", "copy", "-bsf:a", "aac_adtstoasc", "-y", tmp_out])
                r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if r.returncode == 0 and os.path.exists(tmp_out):
                    moved = move_new_files_to_mode3(set([tmp_out]), output_dir=DOWNLOAD_DIR)
                    return True, url
            except Exception:
                pass

            return False, url

        # direct mp4 or mp3
        if u.endswith(".mp4") or u.endswith(".mp3"):
            # Stream download directly
            parsed = urlparse(url)
            filename = os.path.basename(parsed.path)
            if not filename:
                filename = f"file_{int(time.time())}{'.mp3' if u.endswith('.mp3') else '.mp4'}"
            dest_dir = MODE3_DIR if u.endswith((".mp4", ".mp3")) else MODE3_OTHER_DIR
            os.makedirs(dest_dir, exist_ok=True)
            dest_path = os.path.join(dest_dir, filename)
            # avoid overwrite
            if os.path.exists(dest_path):
                base, ext = os.path.splitext(filename)
                dest_path = os.path.join(dest_dir, f"{base}_{int(time.time())}{ext}")
            ok = download_direct_file_streaming(url, dest_path, referer=referer)
            if ok and os.path.exists(dest_path):
                return True, url
            else:
                return False, url

        # other: try yt-dlp as general fallback (supports many sources)
        success = run_yt_dlp_for_url(url, DOWNLOAD_DIR, referer=referer)
        if success:
            move_new_files_to_mode3(before_files, output_dir=DOWNLOAD_DIR)
            return True, url

        # if we reach here, fail
        return False, url

    except Exception:
        return False, url


# ---------- Strategy extract-only runners for mode3 ----------
# Each runner returns list of discovered URLs (no download).
# Mode3 will then download these lists concurrently.

def strategy_extractor_hls_ts(url):
    page_source = fetch_page_source(url)
    if not page_source:
        return []
    hls = extract_all_m3u8_ts_urls(page_source, base_url=url)
    results = hls.get('m3u8', []) + hls.get('ts', [])
    return results


def strategy_extractor_streams(url):
    page_source = fetch_page_source(url)
    if not page_source:
        return []
    return extract_stream_urls(page_source)


def strategy_extractor_iframes(url):
    page_source = fetch_page_source(url)
    if not page_source:
        return []
    return extract_iframe_sources(page_source)


def strategy_extractor_aggressive(url):
    page_source = fetch_page_source(url)
    if not page_source:
        return []
    all_urls = re.findall(r'https?://[^\s"\'<>]+', page_source)
    video_keywords = ['.mp4', '.m3u8', '.mpd', '.mp3', 'video', 'stream', 'media', 'cdn', 'player', 'audio']
    potential_urls = [u for u in all_urls if any(k in u.lower() for k in video_keywords)]
    return list(set(potential_urls))


def strategy_extractor_json(url):
    page_source = fetch_page_source(url)
    if not page_source:
        return []
    return extract_json_video_urls(page_source)


def strategy_extractor_meta(url):
    page_source = fetch_page_source(url)
    if not page_source:
        return []
    return extract_meta_video_urls(page_source)


def strategy_extractor_video_tags(url):
    page_source = fetch_page_source(url)
    if not page_source:
        return []
    return extract_video_tag_urls(page_source, base_url=url)


def strategy_extractor_cdn(url):
    page_source = fetch_page_source(url)
    if not page_source:
        return []
    return extract_cdn_video_urls(page_source)


def strategy_extractor_decode(url):
    page_source = fetch_page_source(url)
    if not page_source:
        return []
    return decode_obfuscated_urls(page_source)


# Map of strategy display names -> extractor functions for mode3
MODE3_STRATEGIES = [
    ("HLS/TS SPECIALIST", strategy_extractor_hls_ts),
    ("EXTRACT STREAMS", strategy_extractor_streams),
    ("IFRAME DETECTION", strategy_extractor_iframes),
    ("AGGRESSIVE SCAN", strategy_extractor_aggressive),
    ("WITH COOKIES", strategy_extractor_streams),  # same extractor but mode3 will pass referer/cookies if needed
    ("JSON EXTRACTION", strategy_extractor_json),
    ("META TAGS & SCHEMA", strategy_extractor_meta),
    ("HTML5 VIDEO TAGS", strategy_extractor_video_tags),
    ("CDN DETECTION", strategy_extractor_cdn),
    ("DECODE OBFUSCATED", strategy_extractor_decode),
    # DIRECT YT-DLP not as extractor here; mode3 will attempt fallback via yt-dlp on URLs already found
]


def download_universal_web_mode3(url):
    """
    New Mode 3 workflow:
    1) For each strategy, run its extractor to gather URLs (no downloads)
    2) Only display strategies that found URLs (print number found)
    3) Deduplicate and prepare download queue
    4) Download with ThreadPoolExecutor concurrently
    5) Move files appropriately into finish/mode3 and finish/mode3/other
    6) Print compact progress and a final summary table (only successful strategies shown)
    """
    global MODE3_ACTIVE
    MODE3_ACTIVE = True
    os.makedirs(FINISH_DIR, exist_ok=True)
    os.makedirs(MODE3_DIR, exist_ok=True)
    os.makedirs(MODE3_OTHER_DIR, exist_ok=True)

    print("\n" + "=" * 60)
    print("🌐 CHẾ ĐỘ: ĐA WEB - MODE 3 (MULTI-THREAD DOWNLOAD)")
    print("=" * 60)
    print(f"\n🎯 Target: {url}\n")
    print("📌 Running multiple extractors and downloading discovered media concurrently...\n")

    strategy_results = {}  # name -> list(urls)
    total_urls_set = set()

    # Run extractors (sequentially; extractors are usually fast). We intentionally do NOT print failures.
    for name, extractor in MODE3_STRATEGIES:
        try:
            urls = extractor(url)
            if urls:
                # normalize urls (unescape basic HTML entities)
                normalized = []
                for u in urls:
                    uu = u.replace('&amp;', '&').replace('\\/', '/').strip()
                    if uu.startswith('//'):
                        uu = 'https:' + uu
                    if uu.startswith('/'):
                        # make absolute if possible
                        parsed_base = urlparse(url)
                        uu = f"{parsed_base.scheme}://{parsed_base.netloc}{uu}"
                    normalized.append(uu)
        
                normalized = list(set(normalized))
                if normalized:
                    strategy_results[name] = normalized
                    for u in normalized:
                        total_urls_set.add(u)
            # If extractor didn't find anything, we do not print anything (hidden)
        except Exception:
            # ignore extractor errors (hidden)
            continue

    if not strategy_results:
        print("❌ Không tìm thấy media bằng các strategies mode3.")
        print("ℹ️ Gợi ý: trang có thể cần JavaScript, đăng nhập hoặc có DRM.")
        return False

    # Print only strategies that succeeded (only counts)
    print("✓ Các strategy tìm được URL (chỉ hiển thị số URL):")
    for name, urls in strategy_results.items():
        print(f"  - {name}: {len(urls)} URL(s)")

    all_urls = list(total_urls_set)
    print(f"\n📥 Tổng số URL duy nhất được tìm thấy: {len(all_urls)}")
    if not all_urls:
        print("❌ Không có URL để tải.")
        return False

    # Prepare download queue: keep order stable but dedup
    all_urls_sorted = sorted(all_urls)
    total = len(all_urls_sorted)

    print("\n🚀 Bắt đầu tải (đa luồng). Chỉ hiển thị tiến trình cơ bản.\n")

    # Thread pool executor for concurrent downloads
    results_map = {}  # url -> (success True/False)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_url = {}
        for i, u in enumerate(all_urls_sorted, start=1):
            # Submit worker: we pass idx and total so worker can print progress if desired
            future = executor.submit(mode3_download_worker, u, url, i, total)
            future_to_url[future] = u

        completed = 0
        for future in as_completed(future_to_url):
            u = future_to_url[future]
            try:
                success, _ = future.result(timeout=None)
            except Exception:
                success = False
            results_map[u] = success
            completed += 1
            # Print minimal progress
            print(f"Progress: {completed}/{total} — {'OK' if success else 'FAIL'} — {u[:80]}")

    # Summarize per-strategy successes (count how many of its urls succeeded)
    strategy_success_counts = {}
    total_success = 0
    for name, urls in strategy_results.items():
        cnt = sum(1 for u in urls if results_map.get(u, False))
        if cnt > 0:
            strategy_success_counts[name] = cnt
            total_success += cnt
        # If cnt == 0, per requirement we hide failures (do not list)

    # Final compact summary table — only show successful strategies
    print("\n" + "=" * 60)
    print("📊 KẾT QUẢ TỔNG QUÁT (chỉ show các strategy thành công)")
    print("=" * 60)
    if strategy_success_counts:
        for name, cnt in strategy_success_counts.items():
            print(f"{name:25s}: ✅ {cnt} file(s)")
    else:
        print("❌ KHÔNG CÓ STRATEGY NÀO TẢI THÀNH CÔNG FILE NÀO")

    print("\n" + "=" * 60)
    print(f"🎉 TỔNG CỘNG ĐÃ TẢI THÀNH CÔNG: {total_success} FILE(S)")
    print("=" * 60)

    return total_success > 0


# ========================================================================
# Các strategy cũ (vẫn giữ cho các chế độ khác sử dụng, không thay đổi logic cơ bản)
# ========================================================================

def download_from_stream_url(stream_url, referer=None):
    """Tải video từ stream URL (m3u8/mpd/mp4) — original behavior (sequential)"""
    before_files = set(glob.glob(os.path.join(DOWNLOAD_DIR, "*.*")))

    cmd = [
        YTDLP_EXE,
        "--ffmpeg-location", ENGINE_DIR,
        "-f", "best",
        "--merge-output-format", "mp4",
        "--no-playlist",
        "-o", os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s"),
    ]

    if referer:
        cmd.extend(["--add-header", f"Referer:{referer}"])

    cmd.extend(["--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"])

    cmd.append(stream_url)

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if result.returncode == 0:
        move_finished_videos(before_files)
        return True

    return False


def strategy_1_direct_ytdlp(url):
    """STRATEGY 1: Tải trực tiếp bằng yt-dlp (phương pháp mặc định)"""
    print("\n🔧 STRATEGY 1: Tải trực tiếp với yt-dlp...")

    before_files = set(glob.glob(os.path.join(DOWNLOAD_DIR, "*.*")))

    cmd = [
        YTDLP_EXE,
        "--ffmpeg-location", ENGINE_DIR,
        "-f", "bestvideo+bestaudio/best",
        "--merge-output-format", "mp4",
        "--ignore-errors",
        "--no-playlist",
        "-o", os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s"),
        url
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if result.returncode == 0:
        move_finished_videos(before_files)
        print("✅ Strategy 1 thành công!")
        return 1

    print("❌ Strategy 1 thất bại.")
    return 0


def strategy_2_extract_streams(url):
    """STRATEGY 2: Extract m3u8/mpd/mp4 URLs từ page source"""
    print("\n🔧 STRATEGY 2: Phát hiện stream URLs trong page...")
    page_source = fetch_page_source(url)
    if not page_source:
        print("❌ Strategy 2 thất bại (không tải được page source).")
        return 0

    stream_urls = extract_stream_urls(page_source)
    if not stream_urls:
        print("❌ Strategy 2 thất bại (không tìm thấy stream URLs).")
        return 0

    print(f"✓ Tìm thấy {len(stream_urls)} stream URL(s)")
    print(f"📥 Sẽ tải TẤT CẢ {len(stream_urls)} stream URLs...")

    success_count = 0
    for i, stream_url in enumerate(stream_urls, 1):
        print(f"\n  → Đang tải stream {i}/{len(stream_urls)}: {stream_url[:80]}...")
        if download_from_stream_url(stream_url, referer=url):
            print(f"✅ Tải thành công stream {i}!")
            success_count += 1
        else:
            print(f"❌ Tải thất bại stream {i}")

    if success_count > 0:
        print(f"\n✅ Strategy 2: Đã tải thành công {success_count}/{len(stream_urls)} stream(s)")
    else:
        print("\n❌ Strategy 2 thất bại (không tải được stream nào).")

    return success_count


def strategy_3_iframe_detection(url):
    """STRATEGY 3: Detect và tải từ iframe embeddings"""
    print("\n🔧 STRATEGY 3: Phát hiện iframe embeddings...")
    page_source = fetch_page_source(url)
    if not page_source:
        print("❌ Strategy 3 thất bại (không tải được page source).")
        return 0

    iframes = extract_iframe_sources(page_source)
    if not iframes:
        print("❌ Strategy 3 thất bại (không tìm thấy iframe).")
        return 0

    print(f"✓ Tìm thấy {len(iframes)} iframe(s)")
    print(f"📥 Sẽ tải TẤT CẢ {len(iframes)} iframe(s)...")

    success_count = 0
    for i, iframe_url in enumerate(iframes, 1):
        print(f"\n  → Đang tải iframe {i}/{len(iframes)}: {iframe_url[:80]}...")
        before_files = set(glob.glob(os.path.join(DOWNLOAD_DIR, "*.*")))
        cmd = [
            YTDLP_EXE,
            "--ffmpeg-location", ENGINE_DIR,
            "-f", "best",
            "--merge-output-format", "mp4",
            "--no-playlist",
            "-o", os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s"),
            iframe_url
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            move_finished_videos(before_files)
            print(f"✅ Tải thành công iframe {i}!")
            success_count += 1
        else:
            print(f"❌ Tải thất bại iframe {i}")

    if success_count > 0:
        print(f"\n✅ Strategy 3: Đã tải thành công {success_count}/{len(iframes)} iframe(s)")
    else:
        print("\n❌ Strategy 3 thất bại (không tải được iframe nào).")

    return success_count


def strategy_4_aggressive_extraction(url):
    """STRATEGY 4: Aggressive extraction - quét tất cả URLs có thể"""
    print("\n🔧 STRATEGY 4: Aggressive scan - tìm mọi URL video...")
    page_source = fetch_page_source(url)
    if not page_source:
        print("❌ Strategy 4 thất bại.")
        return 0

    all_urls = re.findall(r'https?://[^\s"\'<>]+', page_source)
    video_keywords = ['.mp4', '.m3u8', '.mpd', '.mp3', 'video', 'stream', 'media', 'cdn', 'player']
    potential_urls = [u for u in all_urls if any(k in u.lower() for k in video_keywords)]

    potential_urls = list(set(potential_urls))
    if not potential_urls:
        print("❌ Strategy 4 thất bại (không tìm thấy potential URLs).")
        return 0

    print(f"✓ Tìm thấy {len(potential_urls)} potential URL(s)")
    urls_to_try = potential_urls[:20]
    print(f"📥 Sẽ tải TẤT CẢ {len(urls_to_try)} URLs (giới hạn 20)...")

    success_count = 0
    for i, video_url in enumerate(urls_to_try, 1):
        print(f"\n  → Đang tải URL {i}/{len(urls_to_try)}: {video_url[:80]}...")
        if download_from_stream_url(video_url, referer=url):
            print(f"✅ Tải thành công URL {i}!")
            success_count += 1
        else:
            print(f"❌ Tải thất bại URL {i}")

    if success_count > 0:
        print(f"\n✅ Strategy 4: Đã tải thành công {success_count}/{len(urls_to_try)} URL(s)")
    else:
        print("\n❌ Strategy 4 thất bại (không tải được URL nào).")

    return success_count


def strategy_5_with_cookies(url):
    """STRATEGY 5: Thử với cookies (nếu có file cookies.txt)"""
    if not os.path.isfile(COOKIES_FILE):
        print("\n⚠️  STRATEGY 5: Bỏ qua (không có cookies.txt)")
        return 0

    print("\n🔧 STRATEGY 5: Thử với cookies...")

    before_files = set(glob.glob(os.path.join(DOWNLOAD_DIR, "*.*")))

    cmd = [
        YTDLP_EXE,
        "--ffmpeg-location", ENGINE_DIR,
        "--cookies", COOKIES_FILE,
        "-f", "best",
        "--merge-output-format", "mp4",
        "--no-playlist",
        "-o", os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s"),
        url
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if result.returncode == 0:
        move_finished_videos(before_files)
        print("✅ Strategy 5 thành công!")
        return 1

    print("❌ Strategy 5 thất bại.")
    return 0


def strategy_6_json_extraction(url):
    """STRATEGY 6: Extract video URLs từ JSON/API responses"""
    print("\n🔧 STRATEGY 6: Tìm video URLs trong JSON data")
    from urllib.request import Request, urlopen

    try:
        req = Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response = urlopen(req, timeout=15)
        page_source = response.read().decode('utf-8', errors='ignore')
    except:
        print("❌ Strategy 6 thất bại (không tải được page source).")
        return 0

    video_urls = extract_json_video_urls(page_source)
    if not video_urls:
        print("❌ Strategy 6 thất bại (không tìm thấy JSON video URLs).")
        return 0

    print(f"✓ Tìm thấy {len(video_urls)} video URL(s) trong JSON data")
    print(f"📥 Sẽ tải TẤT CẢ {len(video_urls)} URLs...")

    success_count = 0
    for i, video_url in enumerate(video_urls, 1):
        print(f"\n  → Đang tải JSON URL {i}/{len(video_urls)}: {video_url[:80]}...")
        if download_from_stream_url(video_url, referer=url):
            print(f"✅ Tải thành công URL {i}!")
            success_count += 1
        else:
            print(f"❌ Tải thất bại URL {i}")

    if success_count > 0:
        print(f"\n✅ Strategy 6: Đã tải thành công {success_count}/{len(video_urls)} URL(s)")
    else:
        print("\n❌ Strategy 6 thất bại (không tải được URL nào).")

    return success_count


def extract_meta_video_urls(page_source):
    """(Đã định nghĩa ở trên)"""
    # This function is already implemented above for mode3 extraction.
    return []


def strategy_7_meta_tags(url):
    """STRATEGY 7: Extract từ meta tags (Open Graph, Twitter Cards, Schema.org)"""
    print("\n🔧 STRATEGY 7: Tìm video qua Meta Tags & Schema...")
    from urllib.request import Request, urlopen

    try:
        req = Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response = urlopen(req, timeout=15)
        page_source = response.read().decode('utf-8', errors='ignore')
    except:
        print("❌ Strategy 7 thất bại (không tải được page source).")
        return 0

    video_urls = extract_meta_video_urls(page_source)
    if not video_urls:
        print("❌ Strategy 7 thất bại (không tìm thấy meta video URLs).")
        return 0

    print(f"✓ Tìm thấy {len(video_urls)} video URL(s) trong meta tags")
    print(f"📥 Sẽ tải TẤT CẢ {len(video_urls)} URLs...")

    success_count = 0
    for i, video_url in enumerate(video_urls, 1):
        print(f"\n  → Đang tải meta URL {i}/{len(video_urls)}: {video_url[:80]}...")
        before_files = set(glob.glob(os.path.join(DOWNLOAD_DIR, "*.*")))
        cmd = [
            YTDLP_EXE,
            "--ffmpeg-location", ENGINE_DIR,
            "-f", "best",
            "--merge-output-format", "mp4",
            "--no-playlist",
            "-o", os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s"),
            "--referer", url,
            video_url
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            move_finished_videos(before_files)
            print(f"✅ Tải thành công URL {i}!")
            success_count += 1
        else:
            print(f"❌ Tải thất bại URL {i}")

    if success_count > 0:
        print(f"\n✅ Strategy 7: Đã tải thành công {success_count}/{len(video_urls)} URL(s)")
    else:
        print("\n❌ Strategy 7 thất bại (không tải được URL nào).")

    return success_count


def strategy_8_video_tags(url):
    """STRATEGY 8: Extract từ HTML5 <video> và <source> tags"""
    print("\n🔧 STRATEGY 8: Phân tích HTML5 video tags...")
    from urllib.request import Request, urlopen

    try:
        req = Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response = urlopen(req, timeout=15)
        page_source = response.read().decode('utf-8', errors='ignore')
    except:
        print("❌ Strategy 8 thất bại (không tải được page source).")
        return 0

    video_urls = extract_video_tag_urls(page_source, base_url=url)
    if not video_urls:
        print("❌ Strategy 8 thất bại (không tìm thấy video tags).")
        return 0

    print(f"✓ Tìm thấy {len(video_urls)} video URL(s) trong HTML5 tags")
    print(f"📥 Sẽ tải TẤT CẢ {len(video_urls)} URLs...")

    success_count = 0
    for i, video_url in enumerate(video_urls, 1):
        print(f"\n  → Đang tải video tag {i}/{len(video_urls)}: {video_url[:80]}...")
        if download_from_stream_url(video_url, referer=url):
            print(f"✅ Tải thành công URL {i}!")
            success_count += 1
        else:
            print(f"❌ Tải thất bại URL {i}")

    if success_count > 0:
        print(f"\n✅ Strategy 8: Đã tải thành công {success_count}/{len(video_urls)} URL(s)")
    else:
        print("\n❌ Strategy 8 thất bại (không tải được URL nào).")

    return success_count


def strategy_9_cdn_detection(url):
    """STRATEGY 9: Detect video URLs từ CDN và streaming services"""
    print("\n🔧 STRATEGY 9: Quét CDN & Streaming Services...")
    from urllib.request import Request, urlopen

    try:
        req = Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response = urlopen(req, timeout=15)
        page_source = response.read().decode('utf-8', errors='ignore')
    except:
        print("❌ Strategy 9 thất bại (không tải được page source).")
        return 0

    video_urls = extract_cdn_video_urls(page_source)
    if not video_urls:
        print("❌ Strategy 9 thất bại (không tìm thấy CDN URLs).")
        return 0

    print(f"✓ Tìm thấy {len(video_urls)} CDN URL(s)")
    print(f"📥 Sẽ tải TẤT CẢ {len(video_urls)} URLs...")

    success_count = 0
    for i, video_url in enumerate(video_urls, 1):
        print(f"\n  → Đang tải CDN URL {i}/{len(video_urls)}: {video_url[:80]}...")
        if download_from_stream_url(video_url, referer=url):
            print(f"✅ Tải thành công URL {i}!")
            success_count += 1
        else:
            print(f"❌ Tải thất bại URL {i}")

    if success_count > 0:
        print(f"\n✅ Strategy 9: Đã tải thành công {success_count}/{len(video_urls)} URL(s)")
    else:
        print("\n❌ Strategy 9 thất bại (không tải được URL nào).")

    return success_count


def strategy_10_decode_obfuscated(url):
    """STRATEGY 10: Decode encoded/obfuscated URLs"""
    print("\n🔧 STRATEGY 10: Giải mã encoded/obfuscated URLs...")
    from urllib.request import Request, urlopen

    try:
        req = Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response = urlopen(req, timeout=15)
        page_source = response.read().decode('utf-8', errors='ignore')
    except:
        print("❌ Strategy 10 thất bại (không tải được page source).")
        return 0

    video_urls = decode_obfuscated_urls(page_source)
    if not video_urls:
        print("❌ Strategy 10 thất bại (không tìm thấy encoded URLs).")
        return 0

    print(f"✓ Đã decode {len(video_urls)} URL(s)")
    print(f"📥 Sẽ tải TẤT CẢ {len(video_urls)} URLs...")

    success_count = 0
    for i, video_url in enumerate(video_urls, 1):
        print(f"\n  → Đang tải decoded URL {i}/{len(video_urls)}: {video_url[:80]}...")
        if download_from_stream_url(video_url, referer=url):
            print(f"✅ Tải thành công URL {i}!")
            success_count += 1
        else:
            print(f"❌ Tải thất bại URL {i}")

    if success_count > 0:
        print(f"\n✅ Strategy 10: Đã tải thành công {success_count}/{len(video_urls)} URL(s)")
    else:
        print("\n❌ Strategy 10 thất bại (không tải được URL nào).")

    return success_count


def parse_m3u8_playlist(m3u8_url, content=None):
    """(Hàm dùng trong strategy 11 — giữ nguyên, đã có ở file gốc)"""
    from urllib.request import Request, urlopen
    try:
        if content is None:
            req = Request(m3u8_url, headers={'User-Agent': 'Mozilla/5.0'})
            response = urlopen(req, timeout=15)
            content = response.read().decode('utf-8', errors='ignore')
    except:
        return None

    parsed = urlparse(m3u8_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}{'/'.join(parsed.path.split('/')[:-1])}/"

    result = {'master': False, 'variants': [], 'segments': [], 'base_url': base_url}

    lines = content.strip().split('\n')
    if any('#EXT-X-STREAM-INF' in line for line in lines):
        result['master'] = True
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('#EXT-X-STREAM-INF'):
                resolution = None
                bandwidth = None
                if 'RESOLUTION=' in line:
                    res_match = re.search(r'RESOLUTION=(\d+x\d+)', line)
                    if res_match:
                        resolution = res_match.group(1)
                if 'BANDWIDTH=' in line:
                    bw_match = re.search(r'BANDWIDTH=(\d+)', line)
                    if bw_match:
                        bandwidth = int(bw_match.group(1))
                if i + 1 < len(lines):
                    variant_url = lines[i + 1].strip()
                    if not variant_url.startswith('http'):
                        variant_url = urljoin(m3u8_url, variant_url)
                    result['variants'].append({'url': variant_url, 'resolution': resolution, 'bandwidth': bandwidth})
                i += 2
            else:
                i += 1
    else:
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if line.endswith('.ts') or '.ts?' in line:
                segment_url = line
                if not segment_url.startswith('http'):
                    segment_url = urljoin(m3u8_url, segment_url)
                result['segments'].append(segment_url)

    return result


def find_best_m3u8_variant(variants):
    if not variants:
        return None
    sorted_variants = sorted(variants, key=lambda x: x.get('bandwidth', 0), reverse=True)
    return sorted_variants[0]['url'] if sorted_variants else None


def detect_m3u8_type(url):
    if not ('.m3u8' in url.lower() or url.lower().endswith('.m3u')):
        return None
    try:
        parsed = parse_m3u8_playlist(url)
        if parsed:
            return 'master' if parsed['master'] else 'variant'
    except:
        pass
    return 'unknown'


def download_m3u8_with_ytdlp(m3u8_url, output_dir, referer=None):
    before_files = set(glob.glob(os.path.join(output_dir, "*.*")))
    cmd = [
        YTDLP_EXE,
        "--ffmpeg-location", ENGINE_DIR,
        "--hls-prefer-native",
        "--hls-use-mpegts",
        "--external-downloader", "ffmpeg",
        "--external-downloader-args", "ffmpeg:-protocol_whitelist file,http,https,tcp,tls,crypto",
        "-f", "best",
        "--merge-output-format", "mp4",
        "--no-playlist",
        "--no-warnings",
        "-o", os.path.join(output_dir, "%(title)s.%(ext)s"),
    ]
    if referer:
        cmd.extend(["--add-header", f"Referer:{referer}"])
    cmd.extend(["--user-agent", "Mozilla/5.0"])
    cmd.append(m3u8_url)
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode == 0:
        after_files = set(glob.glob(os.path.join(output_dir, "*.*")))
        new_files = after_files - before_files
        if new_files:
            for file in new_files:
                dst = os.path.join(FINISH_DIR, os.path.basename(file))
                try:
                    shutil.move(file, dst)
                except:
                    pass
            return True
    return False


def download_m3u8_with_ffmpeg_direct(m3u8_url, output_dir, referer=None):
    # fallback method — kept small since mode3 primarily uses yt-dlp or ffmpeg direct in worker
    try:
        timestamp = int(time.time())
        output_file = os.path.join(output_dir, f"video_{timestamp}.mp4")
        cmd = [
            FFMPEG_EXE,
            "-protocol_whitelist", "file,http,https,tcp,tls,crypto",
            "-user_agent", "Mozilla/5.0",
        ]
        if referer:
            cmd.extend(["-headers", f"Referer: {referer}\r\n"])
        cmd.extend(["-i", m3u8_url, "-c", "copy", "-bsf:a", "aac_adtstoasc", "-y", output_file])
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0 and os.path.exists(output_file):
            dst = os.path.join(FINISH_DIR, os.path.basename(output_file))
            try:
                shutil.move(output_file, dst)
                return True
            except:
                return False
    except Exception:
        pass
    return False


def download_ts_segments_and_merge(ts_urls, output_dir, referer=None):
    # unchanged from original, kept for completeness
    import tempfile
    if not ts_urls:
        return False

    if len(ts_urls) > 500:
        ts_urls = ts_urls[:500]

    temp_dir = tempfile.mkdtemp(prefix="ts_segments_")
    try:
        downloaded = []
        for i, ts_url in enumerate(ts_urls, 1):
            segment_file = os.path.join(temp_dir, f"segment_{i:04d}.ts")
            try:
                req = urllib.request.Request(ts_url, headers={
                    'User-Agent': 'Mozilla/5.0',
                    'Referer': referer or ''
                })
                response = urllib.request.urlopen(req, timeout=30)
                with open(segment_file, 'wb') as f:
                    f.write(response.read())
                downloaded.append(segment_file)
            except Exception:
                continue

        if not downloaded:
            return False

        concat_file = os.path.join(temp_dir, "concat_list.txt")
        with open(concat_file, 'w') as f:
            for seg_file in downloaded:
                f.write(f"file '{seg_file}'\n")

        timestamp = int(time.time())
        output_file = os.path.join(output_dir, f"merged_video_{timestamp}.mp4")
        cmd = [
            FFMPEG_EXE,
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-c", "copy",
            "-bsf:a", "aac_adtstoasc",
            "-y",
            output_file
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0 and os.path.exists(output_file):
            dst = os.path.join(FINISH_DIR, os.path.basename(output_file))
            shutil.move(output_file, dst)
            return True
        else:
            return False
    finally:
        try:
            shutil.rmtree(temp_dir)
        except:
            pass

# ========================================================================
# Strategy 11 (HLS/TS Specialist) — original sequential implementation kept
# ========================================================================

def strategy_11_hls_ts_specialist(url):
    print("\n🔧 STRATEGY 11: HLS/TS Specialist - Chuyên gia M3U8...")
    from urllib.request import Request, urlopen
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urlopen(req, timeout=15)
        page_source = response.read().decode('utf-8', errors='ignore')
    except:
        print("❌ Strategy 11 thất bại (không tải được page source).")
        return 0

    hls_urls = extract_all_m3u8_ts_urls(page_source, base_url=url)
    m3u8_urls = hls_urls['m3u8']
    ts_urls = hls_urls['ts']

    if not m3u8_urls and not ts_urls:
        print("❌ Strategy 11 thất bại (không tìm thấy m3u8/ts URLs).")
        return 0

    print(f"✓ Tìm thấy {len(m3u8_urls)} m3u8 URLs và {len(ts_urls)} ts URLs")
    success_count = 0

    if m3u8_urls:
        print(f"\n📥 PHASE 1: Xử lý {len(m3u8_urls)} M3U8 playlists...")
        for i, m3u8_url in enumerate(m3u8_urls, 1):
            print(f"\n  → M3U8 {i}/{len(m3u8_urls)}: {m3u8_url[:80]}...")
            playlist_info = parse_m3u8_playlist(m3u8_url)
            if playlist_info and playlist_info['master']:
                print(f"     📋 Master playlist với {len(playlist_info['variants'])} variants")
                best_variant = find_best_m3u8_variant(playlist_info['variants'])
                if best_variant:
                    print(f"     🎯 Best variant: {best_variant[:60]}...")
                    m3u8_url = best_variant

            print("     🔧 Method 1: Thử với yt-dlp...")
            if download_m3u8_with_ytdlp(m3u8_url, DOWNLOAD_DIR, referer=url):
                print(f"     ✅ Tải thành công M3U8 {i} bằng yt-dlp!")
                success_count += 1
                continue

            print("     🔧 Method 2: Thử với ffmpeg direct...")
            if download_m3u8_with_ffmpeg_direct(m3u8_url, DOWNLOAD_DIR, referer=url):
                print(f"     ✅ Tải thành công M3U8 {i} bằng ffmpeg!")
                success_count += 1
                continue

            print(f"     ❌ M3U8 {i} thất bại cả 2 methods")

    if ts_urls and success_count == 0:
        print(f"\n📥 PHASE 2: Xử lý {len(ts_urls)} TS segments.")
        if len(ts_urls) > 50:
            if download_ts_segments_and_merge(ts_urls[:50], DOWNLOAD_DIR, referer=url):
                success_count += 1
        elif len(ts_urls) >= 5:
            if download_ts_segments_and_merge(ts_urls, DOWNLOAD_DIR, referer=url):
                success_count += 1
        else:
            pass

    if success_count > 0:
        print(f"\n✅ Strategy 11: Đã tải thành công {success_count} file(s)")
    else:
        print("\n❌ Strategy 11 thất bại (không tải được file nào).")

    return success_count


# ========================================================================
# Hàm download_universal_web_advanced (giữ cho backward-compatibility)
# ========================================================================

def download_universal_web_advanced(url):
    """Tải video từ bất kỳ trang web nào - NÂNG CẤP với nhiều strategies (phiên bản cũ)"""
    print("\n" + "=" * 60)
    print("🚀 BẮT ĐẦU MULTI-STRATEGY DOWNLOAD")
    print("=" * 60)
    print(f"\n🎯 Target: {url}\n")
    print("📌 CHẠY TẤT CẢ 11 STRATEGIES (không dừng khi có 1 cái thành công)\n")

    strategies = [
        ("HLS/TS SPECIALIST", strategy_11_hls_ts_specialist),
        ("DIRECT YT-DLP", strategy_1_direct_ytdlp),
        ("EXTRACT STREAMS", strategy_2_extract_streams),
        ("IFRAME DETECTION", strategy_3_iframe_detection),
        ("AGGRESSIVE SCAN", strategy_4_aggressive_extraction),
        ("WITH COOKIES", strategy_5_with_cookies),
        ("JSON EXTRACTION", strategy_6_json_extraction),
        ("META TAGS & SCHEMA", strategy_7_meta_tags),
        ("HTML5 VIDEO TAGS", strategy_8_video_tags),
        ("CDN DETECTION", strategy_9_cdn_detection),
        ("DECODE OBFUSCATED", strategy_10_decode_obfuscated),
    ]

    total_downloaded = 0
    results = []

    for strategy_name, strategy_func in strategies:
        try:
            count = strategy_func(url)
            results.append((strategy_name, count))
            total_downloaded += count

            if count > 0:
                print(f"\n✅ {strategy_name}: Đã tải {count} file(s)")
            else:
                print(f"\n❌ {strategy_name}: Không tải được file nào")

        except Exception as e:
            print(f"❌ {strategy_name} gặp lỗi: {str(e)}")
            results.append((strategy_name, 0))
            continue

    # Tổng kết
    print("\n" + "=" * 60)
    print("📊 KẾT QUẢ TỔNG QUÁT")
    print("=" * 60)
    for strategy_name, count in results:
        status = f"✅ {count} file(s)" if count > 0 else "❌ Thất bại"
        print(f"{strategy_name:20s}: {status}")

    print("\n" + "=" * 60)
    if total_downloaded > 0:
        print(f"🎉 TỔNG CỘNG ĐÃ TẢI: {total_downloaded} FILE(S)")
        print("=" * 60)
        return True
    else:
        print("❌ KHÔNG TẢI ĐƯỢC FILE NÀO")
        print("=" * 60)
        print("\n💡 Gợi ý:")
        print("   - Video có thể cần đăng nhập hoặc có DRM protection")
        print("   - Thử mở trang web trong browser và xem có video không")
        print("   - Một số trang yêu cầu JavaScript để load video")
        return False


# ========================================================================
# CHẾ ĐỘ 3 MENU (thay thế trước đây: mode_universal)
# ========================================================================

def mode_universal():
    """
    CHẾ ĐỘ 3: ĐA WEB - Mode3 (mới)
    Lưu ý: đã loại bỏ phần liệt kê '💪 TÍNH NĂNG NÂNG CAO' theo yêu cầu
    """
    print("\n" + "=" * 60)
    print("🌐 CHẾ ĐỘ: ĐA WEB - MODE 3 (MULTI-THREAD)")
    print("=" * 60)

    while True:
        url = input("\nDán URL trang web chứa media (q để quay lại):\n> ").strip()
        if url.lower() in ("q", "quit", "exit"):
            break
        if not url:
            print("⚠️  URL trống.")
            continue

        # Run the new mode3 downloader
        download_universal_web_mode3(url)


# ========================================================================
# ======================= MENU CHÍNH =====================================
# ========================================================================

def main():
    """Hàm chính - Menu chọn chế độ"""

    # Kiểm tra engine files
    success, error = check_engine_files()
    if not success:
        print(error)
        input("\n❌ Không thể tiếp tục. Nhấn Enter để thoát.")
        sys.exit(1)

    # Tạo thư mục finish
    os.makedirs(FINISH_DIR, exist_ok=True)

    # Menu chính
    while True:
        print("\n" + "=" * 60)
        print("           VIDEO DOWNLOADER - MULTI MODE")
        print("=" * 60)
        print("\nChọn chế độ tải:")
        print("1 - 📘 Facebook Video (cần cookies)")
        print("2 - 🎥 YouTube Video/Audio")
        print("3 - 🌐 Đa Web - Advanced (MODE 3 đa luồng)")
        
        # Show server status and option
        if is_server_running():
            print("e - 🔴 Tắt Server Local (đang chạy)")
        else:
            print("e - 🟢 Khởi động Server Local")
        
        print("q - Thoát")

        choice = input("\n> ").strip().lower()

        if choice == "1":
            mode_facebook()
        elif choice == "2":
            mode_youtube()
        elif choice == "3":
            mode_universal()
        elif choice == "e":
            toggle_server()
        elif choice == "q":
            # If server is running, ask if user wants to stop it before exit
            if is_server_running():
                print("\n⚠️  Server local đang chạy!")
                stop_choice = input("Bạn có muốn tắt server trước khi thoát không? (y/n): ").strip().lower()
                if stop_choice == 'y':
                    stop_server()
            print("\n👋 Kết thúc.")
            break
        else:
            print("⚠️  Lựa chọn không hợp lệ.")


if __name__ == "__main__":
    main()