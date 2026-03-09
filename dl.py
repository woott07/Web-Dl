import os
import wget
import requests
import yt_dlp
import gallery_dl
from tqdm import tqdm
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# --- Always save to the user's real Windows Downloads folder ---
DOWNLOADS = os.path.join(os.path.expanduser("~"), "Downloads")
os.makedirs(DOWNLOADS, exist_ok=True)


# ─────────────────────────────────────────────
# 1. Direct File Downloader (Images, ZIPs, PDFs)
#    → Saves straight into Downloads/ (no extra folder)
# ─────────────────────────────────────────────
def file_downloader(url):
    try:
        saved = wget.download(url, out=DOWNLOADS)
        return True, f"File saved to: {saved}"
    except Exception as e:
        return False, f"Error: {e}"


# ─────────────────────────────────────────────
# 2. Video / Audio Downloader
#    → Saves straight into Downloads/ (no extra folder)
# ─────────────────────────────────────────────
def video_downloader(url, quality="1"):
    if quality == "2":
        ydl_opts = {
            'outtmpl': os.path.join(DOWNLOADS, '%(title)s.%(ext)s'),
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }],
        }
        label = "Audio (MP3)"
    else:
        ydl_opts = {
            'outtmpl': os.path.join(DOWNLOADS, '%(title)s.%(ext)s'),
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        }
        label = "Video (MP4)"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True, f"{label} downloaded to your Downloads folder!"
    except Exception as e:
        return False, f"Error: {e}"


# ─────────────────────────────────────────────
# 3. Image Gallery Downloader
#    → Saves straight into Downloads/ (no extra folder)
# ─────────────────────────────────────────────
def gallery_downloader(url):
    try:
        gallery_dl.config.load()
        gallery_dl.config.set(("extractor",), "directory", [DOWNLOADS])
        job = gallery_dl.job.DownloadJob(url)
        job.run()
        return True, "Gallery downloaded to your Downloads folder!"
    except Exception as e:
        return False, f"Error: {e}"


# ─────────────────────────────────────────────
# 4. Web Page Image Scraper
#    → Creates a folder named after the website
#      inside Downloads/ (e.g. Downloads/example.com/)
# ─────────────────────────────────────────────
def webpage_image_scraper(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Name the folder after the website domain
        domain = urlparse(url).netloc.replace("www.", "")
        save_folder = os.path.join(DOWNLOADS, domain)
        os.makedirs(save_folder, exist_ok=True)

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
            return False, "No images found on this page."

        count = 0
        for img_url in tqdm(img_urls, desc="Scraping"):
            try:
                filename = img_url.split("/")[-1].split("?")[0]
                if not filename or '.' not in filename:
                    filename = f"image_{count}.jpg"
                img_data = requests.get(img_url, headers=headers, timeout=10)
                with open(os.path.join(save_folder, filename), 'wb') as f:
                    f.write(img_data.content)
                count += 1
            except Exception:
                pass

        return True, f"Scraped {count} images → saved to Downloads/{domain}/"

    except Exception as e:
        return False, f"Error: {e}"


# ─────────────────────────────────────────────
# CLI (still works from terminal!)
# ─────────────────────────────────────────────
def main():
    while True:
        print("\n" + "="*45)
        print("      🌐 Universal Downloader")
        print("="*45)
        print("  1. Direct File     (image, zip, pdf)")
        print("  2. Video / Audio   (YouTube, IG, Twitter)")
        print("  3. Image Gallery   (Reddit, Imgur, etc)")
        print("  4. Page Scraper    (all images on a page)")
        print("  5. Exit")
        print("="*45)

        choice = input("  Choice (1-5): ").strip()

        if choice == "1":
            url = input("  URL: ").strip()
            ok, msg = file_downloader(url)
        elif choice == "2":
            url = input("  URL: ").strip()
            print("  1=Best Video  2=Audio Only")
            q = input("  Quality (1/2): ").strip()
            ok, msg = video_downloader(url, q)
        elif choice == "3":
            url = input("  URL: ").strip()
            ok, msg = gallery_downloader(url)
        elif choice == "4":
            url = input("  URL: ").strip()
            ok, msg = webpage_image_scraper(url)
        elif choice == "5":
            print("\n  Goodbye! 👋\n")
            break
        else:
            continue

        print(f"\n  [{'+' if ok else '-'}] {msg}")


if __name__ == "__main__":
    main()