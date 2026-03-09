import os
import io
import base64
import requests
import yt_dlp
import gallery_dl
import gallery_dl.job
import gallery_dl.config
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import tempfile

# ─────────────────────────────────────────────
# 1. Direct File Downloader (Images, ZIPs, PDFs)
#    → Returns (True, filename, bytes) or (False, None, error)
# ─────────────────────────────────────────────
def file_downloader(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        filename = url.split("/")[-1].split("?")[0]
        if not filename or '.' not in filename:
            cd = response.headers.get('Content-Disposition', '')
            if 'filename=' in cd:
                filename = cd.split('filename=')[-1].strip('"\'')
            else:
                filename = "downloaded_file"

        # Capture the real Content-Type so phone knows what app to open it with
        content_type = response.headers.get('Content-Type', '').split(';')[0].strip()
        if not content_type or content_type == 'application/octet-stream':
            import mimetypes
            guessed, _ = mimetypes.guess_type(filename)
            if guessed:
                content_type = guessed

        return True, filename, response.content, content_type
    except Exception as e:
        return False, None, str(e), None


# ─────────────────────────────────────────────
# 2. Video / Audio Downloader
#    → Downloads to a temp file, reads bytes, returns them
# ─────────────────────────────────────────────
def video_downloader(url, quality="1"):
    tmp_dir = tempfile.mkdtemp()

    # Find cookies file — check multiple locations
    cookie_paths = [
        os.path.join(os.path.dirname(__file__), 'cookies.txt'),  # next to dl.py
        os.path.join(os.getcwd(), 'cookies.txt'),                # current working dir
        'cookies.txt',                                            # relative
    ]
    cookie_file = None
    for p in cookie_paths:
        if os.path.exists(p):
            cookie_file = p
            break

    ydl_opts = {
        'outtmpl': os.path.join(tmp_dir, '%(title)s.%(ext)s'),
        'quiet': True,
    }

    if quality == "2":
        ydl_opts['format'] = 'bestaudio/best'

    if cookie_file:
        ydl_opts['cookiefile'] = cookie_file

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        files = os.listdir(tmp_dir)
        if not files:
            return False, None, "Download failed: no file produced."

        filepath = os.path.join(tmp_dir, files[0])
        filename = files[0]

        with open(filepath, 'rb') as f:
            file_bytes = f.read()

        os.remove(filepath)
        os.rmdir(tmp_dir)

        return True, filename, file_bytes

    except Exception as e:
        # Include debug info so we know what went wrong
        debug = f"{str(e)} | cookies_found={cookie_file is not None} | cwd={os.getcwd()}"
        for f in os.listdir(tmp_dir):
            os.remove(os.path.join(tmp_dir, f))
        os.rmdir(tmp_dir)
        return False, None, debug


# ─────────────────────────────────────────────
# 3. Image Gallery Downloader
#    → Downloads to temp dir, returns each file as base64
#      so the browser saves each image DIRECTLY (no zip)
# ─────────────────────────────────────────────
def gallery_downloader(url):
    tmp_dir = tempfile.mkdtemp()
    try:
        gallery_dl.config.load([])
        gallery_dl.config.set(("extractor",), "directory", [tmp_dir])
        gallery_dl.config.set(("extractor",), "base-directory", tmp_dir)
        job = gallery_dl.job.DownloadJob(url)
        job.run()

        # Collect all downloaded files as base64 for JSON transport
        file_items = []
        for root, dirs, files in os.walk(tmp_dir):
            for file in sorted(files):
                filepath = os.path.join(root, file)
                with open(filepath, 'rb') as f:
                    file_items.append({
                        'name': file,
                        'data': base64.b64encode(f.read()).decode('utf-8')
                    })

        # Cleanup
        for root, dirs, files in os.walk(tmp_dir, topdown=False):
            for f in files:
                os.remove(os.path.join(root, f))
            for d in dirs:
                os.rmdir(os.path.join(root, d))
        os.rmdir(tmp_dir)

        if not file_items:
            return False, None, "No files were downloaded from this gallery."

        # Special marker — app.py returns JSON with base64 file list
        return True, '__GALLERY_LIST__', file_items

    except Exception as e:
        for root, dirs, files in os.walk(tmp_dir, topdown=False):
            for f in files:
                os.remove(os.path.join(root, f))
            for d in dirs:
                os.rmdir(os.path.join(root, d))
        try:
            os.rmdir(tmp_dir)
        except Exception:
            pass
        return False, None, str(e)


# ─────────────────────────────────────────────
# 4. Web Page Image Scraper
#    → Scrapes all images, zips them into ONE .zip file
# ─────────────────────────────────────────────
def webpage_image_scraper(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        img_tags = soup.find_all('img')

        img_urls = []
        seen = set()
        for img in img_tags:
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            if not src:
                continue
            if src.startswith('http'):
                abs_url = src
            elif src.startswith('//'):
                abs_url = 'https:' + src
            else:
                abs_url = urljoin(url, src)
            if abs_url not in seen:
                seen.add(abs_url)
                img_urls.append(abs_url)

        if not img_urls:
            return False, None, "No images found on this page."

        # Download each image as bytes and return as base64 list
        # → browser saves each file directly (no zip, opens on any device)
        file_items = []
        for i, img_url in enumerate(img_urls):
            try:
                img_data = requests.get(img_url, headers=headers, timeout=10)
                if not img_data.ok:
                    continue
                filename = img_url.split("/")[-1].split("?")[0]
                if not filename or '.' not in filename:
                    filename = f"image_{i}.jpg"
                file_items.append({
                    'name': filename,
                    'data': base64.b64encode(img_data.content).decode('utf-8')
                })
            except Exception:
                pass

        if not file_items:
            return False, None, "Could not download any images."

        return True, '__SCRAPER_LIST__', file_items

    except Exception as e:
        return False, None, str(e)
