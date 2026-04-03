package main

import (
	"bufio"
	"context"
	"crypto/md5"
	"embed"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"sync"
	"time"
)

//go:embed main/engine/*
var engineFiles embed.FS

var (
	baseDir        string
	mainDir        string
	engineDir      string
	ytdlpExe       string
	ffmpegExe      string
	cookiesFile    string
	sourceFile     string
	getLinkDir     string
	linkFile       string
	finishDir      string
	mode3Dir       string
	movFolder      string
	thumbnailCache string

	localIP string
	port    int
	srv     *http.Server
)

func initPaths() {
	cwd, _ := os.Getwd()
	baseDir = cwd
	mainDir = filepath.Join(baseDir, "main")

	engineDir = filepath.Join(mainDir, "engine")
	ytdlpExe = filepath.Join(engineDir, "yt-dlp.exe")
	ffmpegExe = filepath.Join(engineDir, "ffmpeg.exe")

	cookiesFile = filepath.Join(mainDir, "cookies.txt")
	sourceFile = filepath.Join(mainDir, "source.txt")
	getLinkDir = filepath.Join(mainDir, "getlink")
	linkFile = filepath.Join(getLinkDir, "link.txt")

	finishDir = filepath.Join(mainDir, "finish")
	mode3Dir = filepath.Join(finishDir, "mode3")
	movFolder = filepath.Join(getLinkDir, "mov")
	thumbnailCache = filepath.Join(getLinkDir, ".thumbnails")

	os.MkdirAll(engineDir, 0755)
	os.MkdirAll(getLinkDir, 0755)
	os.MkdirAll(finishDir, 0755)
	os.MkdirAll(mode3Dir, 0755)
	os.MkdirAll(movFolder, 0755)
	os.MkdirAll(thumbnailCache, 0755)

	createIfNotExist(cookiesFile)
	createIfNotExist(sourceFile)
	createIfNotExist(linkFile)

	extractEngine(ytdlpExe, "main/engine/yt-dlp.exe")
	extractEngine(ffmpegExe, "main/engine/ffmpeg.exe")
}

func createIfNotExist(path string) {
	if _, err := os.Stat(path); os.IsNotExist(err) {
		os.WriteFile(path, []byte(""), 0644)
	}
}

func extractEngine(dest string, internalPath string) {
	if _, err := os.Stat(dest); os.IsNotExist(err) {
		fmt.Printf("Đang trích xuất %s từ bộ nhớ đệm...\n", filepath.Base(dest))
		data, err := engineFiles.ReadFile(internalPath)
		if err == nil {
			os.WriteFile(dest, data, 0755)
		}
	}
}

func checkEngineFiles() bool {
	if _, err := os.Stat(ytdlpExe); os.IsNotExist(err) {
		return false
	}
	if _, err := os.Stat(ffmpegExe); os.IsNotExist(err) {
		return false
	}
	return true
}

func runYtdlpWithCookieFallback(baseArgs []string, printOutput bool) error {
	hasCookies := false
	if _, err := os.Stat(cookiesFile); err == nil {
		hasCookies = true
	}

	runCommand := func(useCookies bool) error {
		var args []string
		args = append(args, baseArgs...)
		if useCookies {
			args = append(args, "--cookies", cookiesFile)
		}
		cmd := exec.Command(ytdlpExe, args...)
		if printOutput {
			cmd.Stdout = os.Stdout
			cmd.Stderr = os.Stderr
		}
		return cmd.Run()
	}

	if hasCookies {
		if printOutput {
			fmt.Println("🍪 Đang áp dụng Session Cookies...")
		}
		err := runCommand(true)
		if err == nil {
			return nil
		}
		if printOutput {
			fmt.Println("⚠️  Cookies lỗi/hết hạn. Tự động chuyển qua Naked Fallback...")
		}
	}
	return runCommand(false)
}

func extractFacebookLinks() bool {
	content, err := os.ReadFile(sourceFile)
	if err != nil {
		return false
	}
	html := strings.ReplaceAll(string(content), "\\/", "/")
	fbPattern := `https?://(?:www\.|m\.)?(?:facebook\.com/(?:watch\?v=\d+|reel/\d+|[^/]+/videos/\d+|groups/[^/]+/(?:posts|permalink)/\d+)|fb\.watch/[a-zA-Z0-9_-]+)`
	re := regexp.MustCompile(fbPattern)
	matches := re.FindAllString(html, -1)
	unique := make(map[string]bool)
	var links []string
	for _, m := range matches {
		if !unique[m] {
			unique[m] = true
			links = append(links, m)
		}
	}
	sort.Strings(links)
	f, _ := os.Create(linkFile)
	defer f.Close()
	for _, l := range links {
		f.WriteString(l + "\n")
	}
	return true
}

func facebookWorker(id int, url string, wg *sync.WaitGroup, successChan chan bool) {
	defer wg.Done()
	timestamp := time.Now().Unix()
	outputTemplate := filepath.Join(finishDir, fmt.Sprintf("%%(title)s_%d_%d.%%(ext)s", timestamp, id))
	baseArgs := []string{"--ffmpeg-location", engineDir, "--no-playlist", "-f", "bv*+ba/b", "--merge-output-format", "mp4", "-o", outputTemplate, url}
	err := runYtdlpWithCookieFallback(baseArgs, false)
	if err != nil {
		fmt.Printf("Worker %d Failed: %s\n", id, url)
		successChan <- false
		return
	}
	fmt.Printf("Worker %d Success: %s\n", id, url)
	successChan <- true
}

func modeFacebook() {
	fmt.Println("============ CHẾ ĐỘ: FACEBOOK ============")
	extractFacebookLinks()
	fmt.Print("\n1 - Nhập link trực tiếp\n2 - Đọc link từ main/link.txt (đa luồng)\n> ")
	scanner := bufio.NewScanner(os.Stdin)
	scanner.Scan()
	choice := strings.TrimSpace(scanner.Text())

	var links []string
	if choice == "1" {
		fmt.Print("Dán URL: ")
		scanner.Scan()
		links = append(links, strings.TrimSpace(scanner.Text()))
	} else if choice == "2" {
		content, _ := os.ReadFile(linkFile)
		lines := strings.Split(string(content), "\n")
		for _, l := range lines {
			if strings.TrimSpace(l) != "" {
				links = append(links, strings.TrimSpace(l))
			}
		}
	}

	if len(links) == 0 {
		return
	}
	var wg sync.WaitGroup
	successChan := make(chan bool, len(links))
	for i, url := range links {
		wg.Add(1)
		go facebookWorker(i+1, url, &wg, successChan)
	}
	wg.Wait()
	close(successChan)
	fmt.Println("\n✅ Hoàn tất tải Facebook.")
}

func modeYoutube() {
	fmt.Println("============ CHẾ ĐỘ: YOUTUBE ============")
	fmt.Print("Dán URL YouTube: ")
	scanner := bufio.NewScanner(os.Stdin)
	scanner.Scan()
	url := strings.TrimSpace(scanner.Text())
	if url == "" {
		return
	}

	fmt.Print("1 - MP3 (Audio - Kèm Thumbnail)\n2 - Siêu Nét (4K/Tự động Best)\n3 - Nén Cao (Chỉ 1080p)\n4 - Dành cho Điện Thoại (Chỉ 720p)\n> ")
	scanner.Scan()
	format := strings.TrimSpace(scanner.Text())

	outputTemplate := filepath.Join(finishDir, "%(title)s.%(ext)s")
	var baseArgs []string

	if format == "1" {
		baseArgs = []string{"--ffmpeg-location", engineDir, "--extract-audio", "--audio-format", "mp3", "--audio-quality", "0", "--embed-thumbnail", "--embed-metadata", "--no-playlist", "-o", outputTemplate, url}
	} else if format == "3" {
		baseArgs = []string{"--ffmpeg-location", engineDir, "-f", "bestvideo[height<=1080]+bestaudio/best", "--merge-output-format", "mp4", "--embed-metadata", "--no-playlist", "-o", outputTemplate, url}
	} else if format == "4" {
		baseArgs = []string{"--ffmpeg-location", engineDir, "-f", "bestvideo[height<=720]+bestaudio/best", "--merge-output-format", "mp4", "--embed-metadata", "--no-playlist", "-o", outputTemplate, url}
	} else {
		baseArgs = []string{"--ffmpeg-location", engineDir, "-f", "bestvideo+bestaudio/best", "--merge-output-format", "mp4", "--embed-metadata", "--no-playlist", "-o", outputTemplate, url}
	}
	runYtdlpWithCookieFallback(baseArgs, true)
}

func extractStreamUrls(html string, baseUrl string) []string {
	var urls []string
	unique := make(map[string]bool)
	parsedBase, _ := url.Parse(baseUrl)

	addUrl := func(u string) {
		clean := strings.ReplaceAll(u, "&amp;", "&")
		clean = strings.ReplaceAll(clean, "\\/", "/")
		clean = strings.ReplaceAll(clean, "\\\"", "")
		if !strings.HasPrefix(clean, "http") && parsedBase != nil {
			if uParsed, err := url.Parse(clean); err == nil {
				clean = parsedBase.ResolveReference(uParsed).String()
			}
		}
		if !unique[clean] && strings.HasPrefix(clean, "http") {
			unique[clean] = true
			urls = append(urls, clean)
		}
	}

	reMedia := regexp.MustCompile(`https?://[^\s"\'<>]+\.(m3u8|mpd|mp4|mp3|webm|m4a|ogg)(?:\?[^\s"\'<>]*)?`)
	for _, m := range reMedia.FindAllString(html, -1) {
		addUrl(m)
	}

	reIframe := regexp.MustCompile(`(?i)<iframe[^>]+src=["']([^"']+)["']`)
	for _, m := range reIframe.FindAllStringSubmatch(html, -1) {
		if len(m) > 1 {
			addUrl(m[1])
		}
	}

	reHtml5 := regexp.MustCompile(`(?i)<(?:video|source)[^>]+src=["']([^"']+)["']`)
	for _, m := range reHtml5.FindAllStringSubmatch(html, -1) {
		if len(m) > 1 {
			addUrl(m[1])
		}
	}

	reJson := regexp.MustCompile(`(?i)(?:file|url|src)["']?\s*:\s*["']([^"']+)["']`)
	for _, m := range reJson.FindAllStringSubmatch(html, -1) {
		if len(m) > 1 {
			if strings.Contains(m[1], ".mp4") || strings.Contains(m[1], ".m3u8") || strings.Contains(m[1], "youtube") {
				addUrl(m[1])
			}
		}
	}

	reB64 := regexp.MustCompile(`(?i)data-[a-z-]+=["'](aHR0c[a-zA-Z0-9+/=]+)["']`)
	for _, m := range reB64.FindAllStringSubmatch(html, -1) {
		if len(m) > 1 {
			decoded, err := base64.StdEncoding.DecodeString(m[1])
			if err == nil {
				addUrl(string(decoded))
			}
		}
	}
	return urls
}

func modeUniversalWorker(id int, TargetUrl string, wg *sync.WaitGroup, successChan chan bool) {
	defer wg.Done()
	timestamp := time.Now().Unix()
	outputTemplate := filepath.Join(mode3Dir, fmt.Sprintf("%%(title)s_%d_%d.%%(ext)s", timestamp, id))
	baseArgs := []string{"--ffmpeg-location", engineDir, "--no-playlist", "--no-warnings", "-f", "bv*+ba/b", "-o", outputTemplate, TargetUrl}
	if err := runYtdlpWithCookieFallback(baseArgs, false); err == nil {
		fmt.Printf("[Luồng %d] ✅ Tìm thấy: %s\n", id, TargetUrl)
		successChan <- true
	} else {
		successChan <- false
	}
}

func modeUniversal() {
	fmt.Println("============ CHẾ ĐỘ 3: ĐA WEB ============")
	fmt.Print("Dán URL trang web: ")
	scanner := bufio.NewScanner(os.Stdin)
	scanner.Scan()
	TargetUrl := strings.TrimSpace(scanner.Text())
	if TargetUrl == "" {
		return
	}

	fmt.Println("[1/3] Thử phân tích URL gốc bằng Core Engine...")
	outputTemplate := filepath.Join(mode3Dir, "%(title)s_%(id)s.%(ext)s")
	baseArgs := []string{"--ffmpeg-location", engineDir, "--no-playlist", "-f", "bv*+ba/b", "-o", outputTemplate, TargetUrl}
	if err := runYtdlpWithCookieFallback(baseArgs, false); err == nil {
		fmt.Println("✅ Hoàn tất Universal Mode (Native Extraction).")
		return
	}

	fmt.Println("⚠️  Native Extraction thất bại. Khởi động Deep HTML X-Ray Scanner...")
	client := &http.Client{Timeout: 30 * time.Second}
	req, _ := http.NewRequest("GET", TargetUrl, nil)
	req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0")
	req.Header.Set("Accept-Language", "en-US,en;q=0.9,vi;q=0.8")
	resp, err := client.Do(req)
	if err != nil {
		fmt.Println("Lỗi kết nối:", err)
		return
	}
	defer resp.Body.Close()
	bodyBytes, _ := io.ReadAll(resp.Body)
	urls := extractStreamUrls(string(bodyBytes), TargetUrl)

	if len(urls) == 0 {
		fmt.Println("❌ Scanner không thể tìm thấy media trong mã nguồn!")
		return
	}

	fmt.Printf("[2/3] X-Ray phát hiện %d liên kết.\n", len(urls))
	var wg sync.WaitGroup
	successChan := make(chan bool, len(urls))
	for i, u := range urls {
		wg.Add(1)
		go modeUniversalWorker(i+1, u, &wg, successChan)
	}
	wg.Wait()
	close(successChan)
	succ := 0
	for res := range successChan {
		if res {
			succ++
		}
	}
	if succ > 0 {
		fmt.Printf("\n✅ Bóc tách thành công %d video.\n", succ)
	} else {
		fmt.Println("\n❌ Mọi liên kết không phản hồi media khả dụng.")
	}
}

// =============== SERVER =================
func getLocalIP() string {
	conn, err := net.Dial("udp", "8.8.8.8:80")
	if err != nil {
		return "127.0.0.1"
	}
	defer conn.Close()
	return conn.LocalAddr().(*net.UDPAddr).IP.String()
}

func findFreePort(startPort int) int {
	for p := startPort; p < startPort+100; p++ {
		addr := fmt.Sprintf("0.0.0.0:%d", p)
		l, err := net.Listen("tcp", addr)
		if err == nil {
			l.Close()
			return p
		}
	}
	return startPort
}

type FileInfo struct {
	Name    string    `json:"name"`
	Encoded string    `json:"encoded"`
	Size    string    `json:"size"`
	MTime   string    `json:"mtime"`
	RawTime time.Time `json:"-"`
}

func listFinishFiles() []FileInfo {
	var files []FileInfo
	entries, err := os.ReadDir(finishDir)
	if err != nil {
		return files
	}
	for _, e := range entries {
		if !e.IsDir() {
			info, err := e.Info()
			if err != nil {
				continue
			}
			files = append(files, FileInfo{
				Name:    e.Name(),
				Encoded: strings.ReplaceAll(e.Name(), "\\", "/"),
				Size:    fmt.Sprintf("%v B", info.Size()),
				MTime:   info.ModTime().Format("2006-01-02 15:04"),
				RawTime: info.ModTime(),
			})
		}
	}
	sort.Slice(files, func(i, j int) bool { return files[i].RawTime.After(files[j].RawTime) })
	return files
}

func handlerApiFiles(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(listFinishFiles())
}

func handlerThumbnail(w http.ResponseWriter, r *http.Request) {
	filename := strings.TrimPrefix(r.URL.Path, "/thumbnail/")
	videoPath := filepath.Join(finishDir, filename)
	hash := hex.EncodeToString(md5.New().Sum([]byte(filename)))
	thumbnailPath := filepath.Join(thumbnailCache, hash+".jpg")

	if _, err := os.Stat(thumbnailPath); err != nil {
		exec.Command(ffmpegExe, "-y", "-ss", "1", "-i", videoPath, "-vframes", "1", "-vf", "scale=320:-1", "-q:v", "2", thumbnailPath).Run()
	}
	http.ServeFile(w, r, thumbnailPath)
}

func handlerDownloadOrig(w http.ResponseWriter, r *http.Request) {
	filename := strings.TrimPrefix(r.URL.Path, "/download-original/")
	http.ServeFile(w, r, filepath.Join(finishDir, filename))
}

func handlerIndex(w http.ResponseWriter, r *http.Request) {
	tmpl := `<!doctype html><html><head><title>File Finish System</title></head>
	<body style="background:#111; color:#eee; font-family:sans-serif; text-align:center;">
		<h1>📁 Video Downloader Vault</h1>
		<ul style="list-style:none; padding:0;">
			<script>
				fetch('/api/files').then(r=>r.json()).then(f => {
					document.write(f.map(x => "<li><a style='color:#0f0' href='/download-original/" + x.name + "'> Tải: " + x.name + "</a> (" + x.size + ")</li>").join(''))
				})
			</script>
		</ul>
	</body></html>`
	w.Write([]byte(tmpl))
}

func runLocalServer() {
	localIP = getLocalIP()
	port = findFreePort(8000)
	mux := http.NewServeMux()
	mux.HandleFunc("/", handlerIndex)
	mux.HandleFunc("/api/files", handlerApiFiles)
	mux.HandleFunc("/thumbnail/", handlerThumbnail)
	mux.HandleFunc("/download-original/", handlerDownloadOrig)

	srv = &http.Server{
		Addr:    fmt.Sprintf("0.0.0.0:%d", port),
		Handler: mux,
	}

	fmt.Printf("\n🚀 Server đang chạy tại: http://%s:%d\n", localIP, port)
	srv.ListenAndServe()
}

func toggleServerStatus() {
	if srv != nil {
		fmt.Println("🛑 Đang tắt server...")
		srv.Shutdown(context.Background())
		srv = nil
		fmt.Println("✅ Server Local TẮT")
	} else {
		go runLocalServer()
	}
}

func main() {
	initPaths()
	if !checkEngineFiles() {
		return
	}

	scanner := bufio.NewScanner(os.Stdin)
	for {
		fmt.Println("\n==============================================")
		fmt.Println("   📹 VIDEO DOWNLOADER (SINGLE BINARY VERSION)")
		fmt.Println("==============================================")
		fmt.Println("1 - Facebook Downloader")
		fmt.Println("2 - YouTube Downloader")
		fmt.Println("3 - Đa Web (Universal)")
		status := "🔴 Tắt"
		if srv != nil {
			status = "🟢 Bật"
		}
		fmt.Printf("e - Bật/Tắt Local Server (%s)\n", status)
		fmt.Println("q - Thoát")
		fmt.Print("\nChọn phím: ")

		if !scanner.Scan() {
			break
		}
		switch strings.TrimSpace(scanner.Text()) {
		case "1":
			modeFacebook()
		case "2":
			modeYoutube()
		case "3":
			modeUniversal()
		case "e":
			toggleServerStatus()
		case "q":
			return
		}
	}
}
