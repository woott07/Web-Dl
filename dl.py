import os
import io
import requests
import yt_dlp
import gallery_dl
import gallery_dl.job
import gallery_dl.config
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import zipfile
import tempfile

# ─────────────────────────────────────────────
# 1. Direct File Downloader (Images, ZIPs, PDFs)
#    → Returns (True, filename, bytes) or (False, None, None)
# ─────────────────────────────────────────────
def file_downloader(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        # Try to get a good filename from the URL
        filename = url.split("/")[-1].split("?")[0]
        if not filename or '.' not in filename:
            # Try Content-Disposition header
            cd = response.headers.get('Content-Disposition', '')
            if 'filename=' in cd:
                filename = cd.split('filename=')[-1].strip('"\'')
            else:
                filename = "downloaded_file"

        return True, filename, response.content
    except Exception as e:
        return False, None, str(e)


# ─────────────────────────────────────────────
# 2. Video / Audio Downloader
#    → Downloads to a temp file, reads bytes, returns them
# ─────────────────────────────────────────────
def video_downloader(url, quality="1"):
    tmp_dir = tempfile.mkdtemp()

    if quality == "2":
        ydl_opts = {
            'outtmpl': os.path.join(tmp_dir, '%(title)s.%(ext)s'),
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }],
            'quiet': True,
        }
        label = "Audio (MP3)"
    else:
        ydl_opts = {
            'outtmpl': os.path.join(tmp_dir, '%(title)s.%(ext)s'),
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'quiet': True,
        }
        label = "Video (MP4)"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Find the downloaded file
        files = os.listdir(tmp_dir)
        if not files:
            return False, None, "Download failed: no file produced."

        filepath = os.path.join(tmp_dir, files[0])
        filename = files[0]

        with open(filepath, 'rb') as f:
            file_bytes = f.read()

        # Cleanup temp dir
        os.remove(filepath)
        os.rmdir(tmp_dir)

        return True, filename, file_bytes

    except Exception as e:
        # Cleanup on error
        for f in os.listdir(tmp_dir):
            os.remove(os.path.join(tmp_dir, f))
        os.rmdir(tmp_dir)
        return False, None, str(e)


# ─────────────────────────────────────────────
# 3. Image Gallery Downloader
#    → Downloads to temp dir, zips everything, returns zip bytes
# ─────────────────────────────────────────────
def gallery_downloader(url):
    tmp_dir = tempfile.mkdtemp()
    try:
        gallery_dl.config.load([])
        gallery_dl.config.set(("extractor",), "directory", [tmp_dir])
        gallery_dl.config.set(("extractor",), "base-directory", tmp_dir)
        job = gallery_dl.job.DownloadJob(url)
        job.run()

        # Zip all downloaded files
        zip_buffer = io.BytesIO()
        file_count = 0
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(tmp_dir):
                for file in files:
                    filepath = os.path.join(root, file)
                    arcname = os.path.relpath(filepath, tmp_dir)
                    zf.write(filepath, arcname)
                    file_count += 1

        zip_buffer.seek(0)

        # Cleanup
        for root, dirs, files in os.walk(tmp_dir, topdown=False):
            for f in files:
                os.remove(os.path.join(root, f))
            for d in dirs:
                os.rmdir(os.path.join(root, d))
        os.rmdir(tmp_dir)

        if file_count == 0:
            return False, None, "No files were downloaded from this gallery."

        return True, "gallery.zip", zip_buffer.read()

    except Exception as e:
        # Cleanup on error
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
#    → Scrapes all images, zips them, returns zip bytes
# ─────────────────────────────────────────────
def webpage_image_scraper(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        domain = urlparse(url).netloc.replace("www.", "")
        soup = BeautifulSoup(response.text, 'html.parser')
        img_tags = soup.find_all('img')

        img_urls = []
        for img in img_tags:
            src = img.get('src') or img.get('data-src')
            if src:
                if src.startswith('http'):
                    img_urls.append(src)
                elif src.startswith('//'):
                    img_urls.append('https:' + src)
                else:
                    img_urls.append(urljoin(url, src))

        if not img_urls:
            return False, None, "No images found on this page."

        zip_buffer = io.BytesIO()
        count = 0
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for i, img_url in enumerate(img_urls):
                try:
                    filename = img_url.split("/")[-1].split("?")[0]
                    if not filename or '.' not in filename:
                        filename = f"image_{i}.jpg"
                    img_data = requests.get(img_url, headers=headers, timeout=10)
                    zf.writestr(filename, img_data.content)
                    count += 1
                except Exception:
                    pass

        zip_buffer.seek(0)

        if count == 0:
            return False, None, "Could not download any images."

        return True, f"{domain}_images.zip", zip_buffer.read()

    except Exception as e:
        return False, None, str(e)