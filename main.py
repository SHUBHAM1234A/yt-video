import os
import sys
import shutil
import json
import re
from datetime import datetime
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError
from concurrent.futures import ThreadPoolExecutor, as_completed

def safe_filename(name): return re.sub(r'[\\/*?:"<>|]', "_", name)

def check_ffmpeg():
    if not shutil.which("ffmpeg"):
        print("❌ ffmpeg not found. Please install it and make sure it's in your 'PATH'.\n")
        print("💡 To install ffmpeg, run \"winget install --id=Gyan.FFmpeg -e\" in terminal.")
        sys.exit(1)

print("🎬 Welcome to YouTube Video Downloader!\n")

check_ffmpeg()

if not os.path.exists("youtube_cookies.txt"):
    print("❌ Cookie file 'youtube_cookies.txt' not found. Please export it from your browser.\n")
    print("➡️  Instuctions to get the cookie file:\n\n1. Install \"Get cookies.txt LOCALLY\" Extension in your browser.\n2. Go to youtube.com while logged in and click the extension and save the cookies file.\n3. Save it as \"youtube_cookies.txt\" in the same folder as this script.")
    print("\n⚠️  By using your account with yt-dlp, you run the risk of it being banned (temporarily or permanently). Be mindful with the request rate and amount of downloads you make with an account. Use it only when necessary, or consider using a throwaway account.")
    sys.exit(1)

history_file = "download_history.json"

if not os.path.exists(history_file):
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump([], f, indent=2)

if os.path.exists(history_file):
    with open(history_file, "r", encoding="utf-8") as f:
        try:
            download_history = json.load(f)
        except json.JSONDecodeError:
            print("⚠️ History file is corrupted or missing. Starting fresh.")
            download_history = []
else:
    download_history = []

try:
    state = int(input("Choose a number:\n1. Download a Playlist\n2. Download separate video(s)\n3. Clear Download history\nChoice: "))
    if state not in [1, 2, 3]:
        raise ValueError
except Exception:
    print("❌ Invalid input. Please enter 1, 2 or 3.")
    sys.exit(1)

video_urls = []

if state == 1:
    playlist_url = input("🎵 Playlist URL: ").strip()
    with YoutubeDL({'extract_flat': True, 'skip_download': True, 'quiet': True, 'cookiefile': 'youtube_cookies.txt'}) as ydl:
        info_dict = ydl.extract_info(playlist_url, download=False)
        print(f"✅ Playlist: {info_dict['title']} ({len(info_dict['entries'])} videos)")
        video_urls = [f"https://www.youtube.com/watch?v={entry['id']}" for entry in info_dict['entries']]
elif state == 2:
    print('🔗 Enter video URLs one by one (type "done" to finish):')
    while True:
        number = len(video_urls) + 1
        suffix = "th" if 10 <= number % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
        sep_url = input(f"{number}{suffix} URL: ").strip().split("&")[0]
        if sep_url.lower() == "done":
            break
        with YoutubeDL({'extract_flat': True, 'skip_download': True, 'quiet': True, 'cookiefile': 'youtube_cookies.txt'}) as ydl:
            info = ydl.extract_info(sep_url, download=False)
            print(f"Title: {info['title']}")
        video_urls.append(sep_url)
elif state == 3:
    with open(history_file, "w") as f:
        json.dump([], f, indent=2)
    print("✅  All History Cleared.")
    sys.exit(0)
else: sys.exit(0)

download_dir = input("📁 Folder name to save videos: ").strip()
os.makedirs(download_dir, exist_ok=True)

audio_only = input("🎧 Do you want to download audio (MP3) instead of video? (y/n): ").strip().lower() == "y"

use_parallel = False

if len(video_urls) > 1:
    use_parallel = input("⚡ Do you want to enable parallel downloads? (y/n): ").strip().lower() == "y"
max_workers = 1

if use_parallel:
    suggested_workers = min(os.cpu_count(), 6)
    print(f"🧠 Based on your system, {suggested_workers} parallel downloads are recommended.")
    try:
        user_input = input(f"🚦 How many parallel downloads? [Default: {suggested_workers}]: ").strip()
        max_workers = int(user_input) if user_input else suggested_workers
        if max_workers < 1:
            print("Setting workers to 1 (sequential)")
            max_workers = 1
    except ValueError:
        print("Invalid input. Using recommended value.")
        max_workers = suggested_workers

skip_downloaded = input("🧠 Skip videos already downloaded in the past? (y/n): ").strip().lower() == "y"
downloaded_urls = {entry['url'] for entry in download_history if entry['status'] == 'success'}

if skip_downloaded:
    before = len(video_urls)
    video_urls = [url for url in video_urls if url not in downloaded_urls]
    skipped = before - len(video_urls)
    if skipped:
        print(f"⏩ Skipping {skipped} previously downloaded video(s).")

def progress_hook(d):
    if d['status'] == 'downloading':
        print(f"\r⬇️  {d['_percent_str'].strip()} at {d['_speed_str'].strip()} ETA {d['_eta_str'].strip()}", end='')
    elif d['status'] == 'finished':
        print(f"\n✅ Done: {d['filename']}")

class Logger:
    def debug(self, msg):
        pass
    def warning(self, msg):
        pass
    def error(self, msg):
        print(f"❌ {msg}")

base_opts = {
    'format': 'bestvideo+bestaudio/best',
    'outtmpl': os.path.join(download_dir, '%(id)s.%(ext)s'),
    'progress_hooks': [progress_hook],
    'quiet': True,
    'progress_with_newline': False,
    'logger': Logger(),
    'merge_output_format': 'mp4',
    'noplaylist': True,
    'cookiefile': 'youtube_cookies.txt',
    'postprocessors': [],
}

if audio_only:
    base_opts['postprocessors'].append({
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    })

def download_url(url):
    print(f"\n🚀 Downloading: {url}")

    result = {
        "url": url,
        "status": "failed",
        "title": None,
        "filename": None,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    try:
        with YoutubeDL(base_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            title = info_dict.get("title", "video")
            safe_title = safe_filename(title)
            ext = info_dict.get("ext", "mp4")
            filename = os.path.join(download_dir, f"{safe_title}.{ext}")

            result["title"] = title
            result["filename"] = filename

            actual_file = ydl.prepare_filename(info_dict)
            if os.path.exists(actual_file) and actual_file != filename:
                os.rename(actual_file, filename)
            result["status"] = "success"
    except DownloadError as e:
        print(f"❌ Download error for {url}: {e}")
    except Exception as e:
        print(f"⚠️ Unexpected error for {url}: {e}")
    download_history.append(result)

start = datetime.now()

if use_parallel and max_workers > 1:
    print(f"\n🚦 Parallel download mode enabled with {max_workers} workers.")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(download_url, url): url for url in video_urls}
        for future in as_completed(futures):
            pass  
else:
    for url in video_urls:
        download_url(url)        

end = datetime.now()

print(f"\n✅ All downloads completed in {int((end - start).total_seconds())} seconds.")

with open(history_file, "w") as f:
    json.dump(download_history, f, indent=2)
print(f"🗃️  History saved to {history_file}")