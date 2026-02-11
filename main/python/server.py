#!/usr/bin/env python3
# server.py — Flask app để liệt kê file trong folder "finish", tải file gốc và convert sang .mov an toàn.

from flask import (
    Flask, render_template_string, send_from_directory, send_file,
    Response, abort, jsonify
)
import os
import socket
import qrcode
import subprocess
import tempfile
import time
import hashlib
from datetime import datetime
import sys
import logging
import shutil

app = Flask(__name__)

# ============================================================================
# CẤU HÌNH ĐƯỜNG DẪN
# ============================================================================
# File server.py nằm tại: download/main/python/server.py
# Nguồn chính (file gốc): download/finish
# Cache/working: download/main/getlink/

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FINISH_FOLDER = os.path.join(os.path.dirname(BASE_DIR), 'finish')  # download/finish
GETLINK_DIR = os.path.join(BASE_DIR, 'getlink')  # download/main/getlink
MOV_FOLDER = os.path.join(GETLINK_DIR, 'mov')
THUMBNAIL_CACHE = os.path.join(GETLINK_DIR, '.thumbnails')

# ============================================================================
# KHỞI TẠO FOLDER - XÓA CŨ, TẠO MỚI MỖI KHI MỞ SERVER
# ============================================================================

def init_folders():
    """Xóa folder cũ (nếu có) và tạo mới để tránh trùng lặp"""
    # Xóa mov folder nếu tồn tại
    if os.path.exists(MOV_FOLDER):
        shutil.rmtree(MOV_FOLDER)
    # Xóa thumbnails folder nếu tồn tại
    if os.path.exists(THUMBNAIL_CACHE):
        shutil.rmtree(THUMBNAIL_CACHE)
    
    # Tạo lại các folder mới
    for folder in [FINISH_FOLDER, GETLINK_DIR, MOV_FOLDER, THUMBNAIL_CACHE]:
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)

# Chạy ngay khi import module
init_folders()

# ============================================================================
# CẤU HÌNH SERVER - LINH HOẠT IP VÀ PORT
# ============================================================================

def get_local_ip():
    """Lấy địa chỉ IP local một cách đáng tin cậy"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(2)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            hostname = socket.gethostname()
            ip = socket.getaddrinfo(hostname, None, socket.AF_INET)[0][4][0]
            return ip
        except:
            return "127.0.0.1"

def find_free_port(start_port=5000, max_port=65535):
    """Tìm port trống từ start_port trở đi"""
    for port in range(start_port, min(start_port + 100, max_port)):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(('0.0.0.0', port))
                return port
        except OSError:
            continue
    import random
    while True:
        port = random.randint(10000, 60000)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(('0.0.0.0', port))
                return port
        except OSError:
            continue

LOCAL_IP = get_local_ip()
PORT = find_free_port(int(os.environ.get("PORT", "5000")))

# ============================================================================
# TEMPLATE HTML
# ============================================================================
HTML_TEMPLATE = """<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>File Finish - Download</title>
  <style>
    :root{
      --bg-dark: #0a0a14;
      --bg-gradient-start: #120a2a;
      --bg-gradient-end: #1a0f3a;
      --card-bg: linear-gradient(135deg, #1a0f3a 0%, #0f0720 100%);
      --card-border: #2d1b4e;
      --text: #e8e3f5;
      --text-muted: #9d8bc7;
      --primary: #8b5cf6;
      --primary-hover: #a78bfa;
      --secondary: #6366f1;
      --accent: #ec4899;
      --border-glow: rgba(139, 92, 246, 0.3);
      --shadow: rgba(139, 92, 246, 0.15);
    }
    
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    
    html, body {
      height: 100%;
      background: linear-gradient(180deg, var(--bg-gradient-start) 0%, var(--bg-gradient-end) 100%);
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, Arial, sans-serif;
      color: var(--text);
      overflow-x: hidden;
    }
    
    .container {
      max-width: 1200px;
      margin: 0 auto;
      padding: 32px 24px;
    }
    
    header {
      margin-bottom: 32px;
      text-align: center;
    }
    
    h1 {
      font-size: 32px;
      font-weight: 700;
      background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      margin-bottom: 12px;
      letter-spacing: -0.5px;
    }
    
    .folder-path {
      display: inline-block;
      padding: 8px 16px;
      background: rgba(139, 92, 246, 0.1);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      font-family: 'Courier New', monospace;
      font-size: 14px;
      color: var(--text-muted);
      margin-bottom: 8px;
    }
    
    .notice {
      color: var(--text-muted);
      font-size: 14px;
      margin-bottom: 24px;
    }
    
    .stats-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px 20px;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      margin-bottom: 24px;
      box-shadow: 0 4px 24px var(--shadow);
    }
    
    .stat-item {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    
    .stat-label {
      font-size: 13px;
      color: var(--text-muted);
    }
    
    .stat-value {
      font-size: 18px;
      font-weight: 600;
      color: var(--primary);
    }
    
    .live-indicator {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 6px 12px;
      background: rgba(16, 185, 129, 0.1);
      border: 1px solid rgba(16, 185, 129, 0.3);
      border-radius: 20px;
      font-size: 13px;
      color: #10b981;
    }
    
    .live-dot {
      width: 8px;
      height: 8px;
      background: #10b981;
      border-radius: 50%;
      animation: pulse 2s ease-in-out infinite;
    }
    
    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }
    
    .file-list {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    
    .file-card {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 16px;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      transition: all 0.3s ease;
      box-shadow: 0 4px 24px var(--shadow);
      position: relative;
      overflow: hidden;
    }
    
    .file-card::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 3px;
      background: linear-gradient(90deg, var(--primary) 0%, var(--accent) 100%);
      opacity: 0;
      transition: opacity 0.3s ease;
    }
    
    .file-card:hover {
      border-color: var(--border-glow);
      box-shadow: 0 8px 32px var(--shadow);
      transform: translateY(-2px);
    }
    
    .file-card:hover::before {
      opacity: 1;
    }
    
    .file-info {
      flex: 1;
      min-width: 0;
      display: flex;
      align-items: center;
      gap: 16px;
    }
    
    .file-thumbnail {
      width: 120px;
      height: 68px;
      border-radius: 8px;
      overflow: hidden;
      flex-shrink: 0;
      background: linear-gradient(135deg, #1a0f3a 0%, #0f0720 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    }
    
    .file-thumbnail img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    
    .file-thumbnail.loading {
      animation: shimmer 2s infinite;
    }
    
    .thumbnail-placeholder {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 100%;
      height: 100%;
    }
    
    .thumbnail-icon {
      width: 32px;
      height: 32px;
      stroke: var(--text-muted);
      opacity: 0.5;
    }
    
    .file-details {
      flex: 1;
      min-width: 0;
    }
    
    .file-name {
      font-size: 16px;
      font-weight: 600;
      color: var(--text);
      margin-bottom: 6px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 100%;
    }
    
    .file-meta {
      display: flex;
      align-items: center;
      gap: 16px;
      font-size: 13px;
      color: var(--text-muted);
    }
    
    .file-size {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 10px;
      background: rgba(139, 92, 246, 0.1);
      border-radius: 6px;
      font-weight: 500;
    }
    
    .file-time {
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    
    .file-actions {
      display: flex;
      gap: 12px;
      flex-shrink: 0;
    }
    
    .btn {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 10px 20px;
      border-radius: 10px;
      border: none;
      font-size: 14px;
      font-weight: 500;
      cursor: pointer;
      text-decoration: none;
      transition: all 0.2s ease;
      position: relative;
      overflow: hidden;
    }
    
    .btn::before {
      content: '';
      position: absolute;
      top: 50%;
      left: 50%;
      width: 0;
      height: 0;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.1);
      transform: translate(-50%, -50%);
      transition: width 0.6s, height 0.6s;
    }
    
    .btn:hover::before {
      width: 300px;
      height: 300px;
    }
    
    .btn-primary {
      background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
      color: white;
      box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
    }
    
    .btn-primary:hover {
      box-shadow: 0 6px 20px rgba(139, 92, 246, 0.6);
      transform: translateY(-2px);
    }
    
    .btn-secondary {
      background: linear-gradient(135deg, var(--accent) 0%, #f472b6 100%);
      color: white;
      box-shadow: 0 4px 12px rgba(236, 72, 153, 0.4);
    }
    
    .btn-secondary:hover {
      box-shadow: 0 6px 20px rgba(236, 72, 153, 0.6);
      transform: translateY(-2px);
    }
    
    .btn-icon {
      width: 18px;
      height: 18px;
      flex-shrink: 0;
      position: relative;
      z-index: 1;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    
    .btn-icon svg {
      width: 100%;
      height: 100%;
      display: block;
    }
    
    .btn-text {
      position: relative;
      z-index: 1;
      line-height: 1;
    }
    
    .meta-icon {
      width: 14px;
      height: 14px;
      flex-shrink: 0;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    
    .meta-icon svg {
      width: 100%;
      height: 100%;
      display: block;
    }
    
    .empty-state {
      text-align: center;
      padding: 60px 20px;
      color: var(--text-muted);
    }
    
    .empty-state svg {
      width: 80px;
      height: 80px;
      margin-bottom: 20px;
      opacity: 0.3;
      stroke: var(--text-muted);
    }
    
    .empty-state h3 {
      font-size: 20px;
      margin-bottom: 8px;
      color: var(--text);
    }
    
    footer {
      margin-top: 40px;
      padding-top: 24px;
      border-top: 1px solid var(--card-border);
      text-align: center;
      color: var(--text-muted);
      font-size: 13px;
    }
    
    .footer-content {
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 24px;
      flex-wrap: wrap;
    }
    
    .footer-item {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    
    .footer-icon {
      width: 16px;
      height: 16px;
      flex-shrink: 0;
    }
    
    @keyframes shimmer {
      0% { background-position: -1000px 0; }
      100% { background-position: 1000px 0; }
    }
    
    .loading {
      animation: shimmer 2s infinite;
      background: linear-gradient(90deg, 
        rgba(139, 92, 246, 0.05), 
        rgba(139, 92, 246, 0.15), 
        rgba(139, 92, 246, 0.05)
      );
      background-size: 1000px 100%;
    }
    
    @media (max-width: 768px) {
      .container {
        padding: 20px 16px;
      }
      
      h1 {
        font-size: 24px;
      }
      
      .file-card {
        flex-direction: column;
        align-items: flex-start;
        padding: 16px;
      }
      
      .file-info {
        width: 100%;
        margin-bottom: 12px;
      }
      
      .file-actions {
        width: 100%;
      }
      
      .btn {
        flex: 1;
        justify-content: center;
      }
      
      .stats-bar {
        flex-direction: column;
        gap: 12px;
        align-items: flex-start;
      }
      
      .file-thumbnail {
        width: 100px;
        height: 56px;
      }
    }
  </style>
</head>
<body>
<div class="container">
  <header>
    <h1>📁 File Manager</h1>
    <div class="folder-path">{{ finish_folder }}</div>
    <p class="notice">Tải xuống file gốc hoặc convert sang định dạng .mov</p>
  </header>
  
  <div class="stats-bar">
    <div class="stat-item">
      <span class="stat-label">Tổng số file:</span>
      <span class="stat-value" id="file-count">0</span>
    </div>
    <div class="live-indicator">
      <span class="live-dot"></span>
      <span>Cập nhật real-time</span>
    </div>
    <div class="stat-item">
      <span class="stat-label">Cập nhật lúc:</span>
      <span class="stat-value" id="last-update" style="font-size: 14px;">--:--:--</span>
    </div>
  </div>

  <div id="file-list" class="file-list">
    <!-- Files will be loaded here via JavaScript -->
  </div>

  <footer>
    <div class="footer-content">
      <div class="footer-item">
        <div class="footer-icon">
          <svg fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 6v6l4 2"/>
          </svg>
        </div>
        <span id="footer-time">{{ now }}</span>
      </div>
      <div class="footer-item">
        <div class="footer-icon">
          <svg fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">
            <rect x="3" y="4" width="18" height="18" rx="2"/>
            <line x1="16" y1="2" x2="16" y2="6"/>
            <line x1="8" y1="2" x2="8" y2="6"/>
            <line x1="3" y1="10" x2="21" y2="10"/>
          </svg>
        </div>
        <span>{{ server_url }}</span>
      </div>
    </div>
  </footer>
</div>

<script>
  let previousFiles = [];
  
  function createFileCard(file) {
    const thumbnailUrl = `/thumbnail/${encodeURIComponent(file.encoded)}`;
    
    return `
      <div class="file-card" data-filename="${file.name}">
        <div class="file-info">
          <div class="file-thumbnail loading" data-src="${thumbnailUrl}">
            <div class="thumbnail-placeholder">
              <svg class="thumbnail-icon" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">
                <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/>
                <polyline points="13 2 13 9 20 9"/>
              </svg>
            </div>
          </div>
          <div class="file-details">
            <div class="file-name" title="${file.name}">${file.name}</div>
            <div class="file-meta">
              <span class="file-size">
                <div class="meta-icon">
                  <svg fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                    <polyline points="7 10 12 15 17 10"/>
                    <line x1="12" y1="15" x2="12" y2="3"/>
                  </svg>
                </div>
                ${file.size}
              </span>
              <span class="file-time">
                <div class="meta-icon">
                  <svg fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">
                    <circle cx="12" cy="12" r="10"/>
                    <path d="M12 6v6l4 2"/>
                  </svg>
                </div>
                ${file.mtime}
              </span>
            </div>
          </div>
        </div>
        <div class="file-actions">
          <a class="btn btn-primary" href="/download-original/${file.encoded}" title="Tải file gốc">
            <div class="btn-icon">
              <svg fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="7 10 12 15 17 10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
            </div>
            <span class="btn-text">Tải Gốc</span>
          </a>
          <a class="btn btn-secondary" href="/download-mov/${file.encoded}" title="Convert và tải .mov">
            <div class="btn-icon">
              <svg fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">
                <rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18"/>
                <line x1="7" y1="2" x2="7" y2="22"/>
                <line x1="17" y1="2" x2="17" y2="22"/>
                <line x1="2" y1="12" x2="22" y2="12"/>
                <line x1="2" y1="7" x2="7" y2="7"/>
                <line x1="2" y1="17" x2="7" y2="17"/>
                <line x1="17" y1="17" x2="22" y2="17"/>
                <line x1="17" y1="7" x2="22" y2="7"/>
              </svg>
            </div>
            <span class="btn-text">Tải MOV</span>
          </a>
        </div>
      </div>
    `;
  }
  
  function createEmptyState() {
    return `
      <div class="empty-state">
        <svg fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24">
          <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/>
          <polyline points="13 2 13 9 20 9"/>
        </svg>
        <h3>Không có file nào</h3>
        <p>Thư mục hiện đang trống</p>
      </div>
    `;
  }
  
  function loadThumbnails() {
    const thumbnails = document.querySelectorAll('.file-thumbnail[data-src]:not(.loaded)');
    
    thumbnails.forEach(thumb => {
      const img = new Image();
      const src = thumb.dataset.src;
      
      img.onload = function() {
        thumb.innerHTML = '';
        thumb.appendChild(img);
        thumb.classList.remove('loading');
        thumb.classList.add('loaded');
      };
      
      img.onerror = function() {
        thumb.classList.remove('loading');
      };
      
      img.src = src;
    });
  }
  
  function updateFileList(files) {
    const fileList = document.getElementById('file-list');
    const fileCount = document.getElementById('file-count');
    const lastUpdate = document.getElementById('last-update');
    
    fileCount.textContent = files.length;
    
    const now = new Date();
    lastUpdate.textContent = now.toLocaleTimeString('vi-VN');
    
    const filesChanged = JSON.stringify(files) !== JSON.stringify(previousFiles);
    
    if (filesChanged) {
      previousFiles = [...files];
      
      if (files.length === 0) {
        fileList.innerHTML = createEmptyState();
      } else {
        fileList.innerHTML = files.map(createFileCard).join('');
        
        setTimeout(() => {
          document.querySelectorAll('.file-card').forEach((card, index) => {
            card.style.animation = `fadeIn 0.5s ease ${index * 0.05}s both`;
          });
          
          loadThumbnails();
        }, 10);
      }
    }
  }
  
  async function fetchFiles() {
    try {
      const response = await fetch('/api/files');
      if (response.ok) {
        const files = await response.json();
        updateFileList(files);
      }
    } catch (error) {
      console.error('Error fetching files:', error);
    }
  }
  
  function updateFooterTime() {
    const footerTime = document.getElementById('footer-time');
    const now = new Date();
    footerTime.textContent = now.toLocaleString('vi-VN');
  }
  
  const style = document.createElement('style');
  style.textContent = `
    @keyframes fadeIn {
      from {
        opacity: 0;
        transform: translateY(20px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
  `;
  document.head.appendChild(style);
  
  fetchFiles();
  setInterval(fetchFiles, 1000);
  setInterval(updateFooterTime, 1000);
</script>
</body>
</html>"""

# ============================================================================
# CÁC HÀM TIỆN ÍCH
# ============================================================================

def sizeof_fmt(num, suffix='B'):
    """Convert file size to human readable format"""
    for unit in ['','K','M','G','T','P']:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}P{suffix}"

def list_finish_files():
    """List all files in the finish folder (nguồn chính)"""
    files = []
    try:
        for fname in os.listdir(FINISH_FOLDER):
            full = os.path.join(FINISH_FOLDER, fname)
            if os.path.isfile(full):
                stat = os.stat(full)
                files.append({
                    "name": fname,
                    "encoded": fname.replace("\\", "/"),
                    "size": sizeof_fmt(stat.st_size),
                    "mtime": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                })
    except Exception as e:
        print(f"Error listing files: {e}")
    
    files.sort(key=lambda x: x["mtime"], reverse=True)
    return files

def get_server_url():
    """Get the server URL with current IP and Port"""
    return f"http://{LOCAL_IP}:{PORT}"

def generate_thumbnail(video_path, output_path, width=320):
    """Generate thumbnail from video at 1 second mark"""
    try:
        cmd = [
            'ffmpeg', '-y',
            '-ss', '1',
            '-i', video_path,
            '-vframes', '1',
            '-vf', f'scale={width}:-1',
            '-q:v', '2',
            output_path
        ]
        
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10
        )
        
        return proc.returncode == 0
    except Exception as e:
        print(f"Thumbnail generation error: {e}")
        return False

def ffprobe_has_audio(path):
    """Check if video file has audio stream"""
    try:
        p = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'a', '-show_entries', 'stream=index',
             '-of', 'csv=p=0', path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False
        )
        return bool(p.stdout.strip())
    except FileNotFoundError:
        return False
    except Exception as e:
        print(f"ffprobe error: {e}")
        return False

def get_video_info(path):
    """Get video stream information"""
    try:
        p = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'v:0', 
             '-show_entries', 'stream=codec_name,codec_tag_string,width,height,pix_fmt', 
             '-of', 'default=noprint_wrappers=1', path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False
        )
        
        info = {}
        for line in p.stdout.strip().split('\n'):
            if '=' in line:
                key, value = line.split('=', 1)
                info[key.strip()] = value.strip()
        
        return info
    except Exception as e:
        print(f"get_video_info error: {e}")
        return {}

def is_codec_mov_compatible(codec_name, codec_tag=None):
    """Check if codec is compatible with MOV container"""
    if not codec_name:
        return False
    
    codec_name = codec_name.lower()
    
    compatible_codecs = [
        'h264', 'hevc', 'h265', 'x265',
        'prores',
        'mpeg4', 'mp4v',
        'mjpeg', 'jpeg',
        'png',
        'tiff',
        'rawvideo',
        'v210', 'v410',
        'rle',
    ]
    
    if codec_tag and codec_tag.lower() in ['avc1', 'hev1', 'hvc1']:
        return True
    
    return codec_name in compatible_codecs

# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    """Main page with file listing"""
    files = list_finish_files()
    return render_template_string(
        HTML_TEMPLATE,
        files=files,
        finish_folder=FINISH_FOLDER,
        server_url=get_server_url(),
        now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

@app.route('/thumbnail/<path:filename>')
def get_thumbnail(filename):
    """Generate thumbnail from video in FINISH_FOLDER, save to THUMBNAIL_CACHE"""
    video_path = os.path.join(FINISH_FOLDER, filename)
    
    if not os.path.exists(video_path):
        return abort(404, "File không tồn tại")
    
    file_hash = hashlib.md5(filename.encode()).hexdigest()
    thumbnail_path = os.path.join(THUMBNAIL_CACHE, f"{file_hash}.jpg")
    
    if os.path.exists(thumbnail_path):
        video_mtime = os.path.getmtime(video_path)
        thumb_mtime = os.path.getmtime(thumbnail_path)
        
        if thumb_mtime >= video_mtime:
            return send_file(thumbnail_path, mimetype='image/jpeg')
    
    if generate_thumbnail(video_path, thumbnail_path):
        return send_file(thumbnail_path, mimetype='image/jpeg')
    else:
        return abort(404, "Không thể tạo thumbnail")

@app.route('/download-original/<path:filename>')
def download_original(filename):
    """Download original file từ FINISH_FOLDER"""
    safe_path = os.path.join(FINISH_FOLDER, filename)
    if not os.path.exists(safe_path):
        return abort(404, "File không tồn tại")
    return send_from_directory(FINISH_FOLDER, filename, as_attachment=True)

@app.route('/download-mov/<path:filename>')
def download_mov(filename):
    """Convert file từ FINISH_FOLDER sang MOV, lưu vào MOV_FOLDER, và tải về"""
    input_p = os.path.join(FINISH_FOLDER, filename)
    if not os.path.exists(input_p):
        return abort(404, "File không tồn tại")

    base = os.path.splitext(os.path.basename(filename))[0]
    mov_path = os.path.join(MOV_FOLDER, base + ".mov")
    
    if os.path.exists(mov_path):
        input_mtime = os.path.getmtime(input_p)
        mov_mtime = os.path.getmtime(mov_path)
        if mov_mtime >= input_mtime:
            return send_file(mov_path, mimetype='video/quicktime', as_attachment=True, download_name=base + ".mov")

    has_audio = ffprobe_has_audio(input_p)
    
    video_info = get_video_info(input_p)
    video_codec = video_info.get('codec_name', '').lower()
    codec_tag = video_info.get('codec_tag_string', '')
    
    print(f"Converting: {filename}")
    print(f"  Video codec: {video_codec}, tag: {codec_tag}")
    print(f"  Has audio: {has_audio}")

    should_copy = is_codec_mov_compatible(video_codec, codec_tag)
    
    if should_copy:
        print(f"  Strategy: COPY codec (preserve quality)")
    else:
        print(f"  Strategy: RE-ENCODE to H.264 (codec {video_codec} not MOV compatible)")

    cmd = ['ffmpeg', '-y', '-i', input_p]
    
    if should_copy:
        cmd += ['-c:v', 'copy']
    else:
        cmd += ['-c:v', 'libx264', '-preset', 'fast', '-crf', '18']
    
    if has_audio:
        cmd += ['-c:a', 'aac', '-b:a', '256k']
    else:
        cmd += ['-an']
    
    cmd += ['-movflags', '+faststart']
    
    if not should_copy:
        cmd += ['-pix_fmt', 'yuv420p']
    
    cmd += [mov_path]

    try:
        proc = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True,
            timeout=600
        )
    except subprocess.TimeoutExpired:
        print(f"  ERROR: ffmpeg timeout")
        try:
            if os.path.exists(mov_path):
                os.remove(mov_path)
        except Exception:
            pass
        return abort(500, "Quá thời gian xử lý video (timeout).")
    except FileNotFoundError:
        try:
            if os.path.exists(mov_path):
                os.remove(mov_path)
        except Exception:
            pass
        return abort(500, "ffmpeg không được cài đặt trên server.")
    except Exception as e:
        try:
            if os.path.exists(mov_path):
                os.remove(mov_path)
        except Exception:
            pass
        print(f"  ERROR: ffmpeg exception: {e}")
        return abort(500, "Lỗi khi gọi ffmpeg.")

    if proc.returncode != 0:
        print("=" * 60)
        print("ffmpeg FAILED!")
        print(f"Command: {' '.join(cmd)}")
        print(f"Return code: {proc.returncode}")
        print(f"STDERR: {proc.stderr}")
        print("=" * 60)
        try:
            if os.path.exists(mov_path):
                os.remove(mov_path)
        except Exception:
            pass
        return abort(500, f"Lỗi convert: {proc.stderr[:200]}")

    try:
        size = os.path.getsize(mov_path)
        print(f"  Output size: {sizeof_fmt(size)}")
        
        if size == 0:
            os.remove(mov_path)
            return abort(500, "File kết quả 0B.")
            
        if size < 1024:
            print(f"  WARNING: File very small ({size} bytes), possible error")
            
    except Exception as e:
        print(f"  ERROR: Cannot check file: {e}")
        try:
            if os.path.exists(mov_path):
                os.remove(mov_path)
        except Exception:
            pass
        return abort(500, "Không thể kiểm tra file kết quả.")

    print(f"  SUCCESS: {base}.mov")
    
    return send_file(mov_path, mimetype='video/quicktime', as_attachment=True, download_name=base + ".mov")

@app.route('/api/files')
def api_files():
    """API endpoint for file listing"""
    return jsonify(list_finish_files())

# ============================================================================
# QR CODE DISPLAY FUNCTIONS - COMPACT VERSION
# ============================================================================

def create_compact_qr(url):
    """Create compact QR code using Unicode half-blocks (1/4 size)"""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=1,
            border=1
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        matrix = qr.get_matrix()
        size = len(matrix)
        
        if size % 2 == 1:
            for row in matrix:
                row.append(False)
            matrix.append([False] * (size + 1))
            size += 1
        
        chars = {
            (False, False): ' ',
            (False, True):  '▄',
            (True, False):  '▀',
            (True, True):   '█',
        }
        
        lines = []
        for i in range(0, size, 2):
            row1 = matrix[i]
            row2 = matrix[i + 1]
            line = ''
            for j in range(0, size, 2):
                top_left = row1[j]
                top_right = row1[j + 1] if j + 1 < len(row1) else False
                bot_left = row2[j]
                bot_right = row2[j + 1] if j + 1 < len(row2) else False
                
                line += chars[(top_left, bot_left)]
                line += chars[(top_right, bot_right)]
            
            lines.append(line)
        
        return '\n'.join(lines)
        
    except Exception as e:
        return None

def display_server_info(url):
    """Display clickable URL and compact QR code"""
    print(f"\033]8;;{url}\033\\{url}\033]8;;\033\\")
    
    qr_code = create_compact_qr(url)
    if qr_code:
        print(qr_code)

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    SERVER_URL = get_server_url()
    
    display_server_info(SERVER_URL)
    
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    log.disabled = True
    
    app.logger.disabled = True
    logging.getLogger('socketio').setLevel(logging.ERROR)
    logging.getLogger('engineio').setLevel(logging.ERROR)
    
    cli = sys.modules['flask.cli']
    cli.show_server_banner = lambda *x: None
    
    try:
        import click
        click.echo = lambda *args, **kwargs: None
        click.secho = lambda *args, **kwargs: None
    except:
        pass
    
    try:
        from werkzeug.serving import WSGIRequestHandler
        WSGIRequestHandler.protocol_version = "HTTP/1.1"
        
        app.run(
            host='0.0.0.0',
            port=PORT,
            debug=False,
            threaded=True,
            use_reloader=False
        )
    except KeyboardInterrupt:
        pass
    except Exception as e:
        pass