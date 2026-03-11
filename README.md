# Universal Downloader

A Flask-based web application that acts as an all-in-one downloader for almost any type of media on the web. Whether you need to download direct files, YouTube videos, full image galleries, or scrape every image off a webpage, this tool handles it. It's built with a strong focus on mobile compatibility and robust error handling to bypass strict anti-bot protections.

## Features

- **Direct File Downloads**: Securely downloads direct links (Images, PDFs, ZIPs) while correctly assigning MIME types so mobile operating systems recognize how to open them.
- **Video & Audio Downloader**: Powered by `yt-dlp`. Downloads high-quality videos and audio from YouTube and hundreds of other sites. Uses advanced cookie injection to bypass datacenter IP bans and bot detection.
- **Image Gallery Downloader**: Uses `gallery-dl` to parse and download entire image galleries. Instead of zipping everything (which is hard to open on phones), it delivers images directly to your device.
- **Webpage Image Scraper**: Parses any URL with `BeautifulSoup`, extracts all `<img>` tags, and allows you to download the images natively.
- **Mobile Optimized**: Custom CSS ensures touch events work perfectly. Files are streamed directly to the browser with explicit Content-Types for seamless mobile usage.

## Tech Stack

- **Backend**: Python, Flask
- **Core Libraries**: `yt-dlp`, `gallery-dl`, `BeautifulSoup4`, `requests`
- **Deployment**: Gunicorn (Optimized for PaaS providers like Railway)

## How It Works (Overcoming Technical Challenges)

Building a dependable downloader that works on cloud servers involves bypassing several complex restrictions. Here is how this project solves them:

1. **Bypassing YouTube "Sign in to confirm you're not a bot"**: 
   Datacenter IPs are heavily restricted by YouTube. To fix this, personal browser cookies are exported and injected into the app via environment variables, giving the server legitimate session access.
2. **Beating the 32KB Environment Variable Limit**: 
   Cookie files are massive (often 40KB+), which breaks Railway's environment variable limits. This app uses a custom `zlib` compression + `base64` encoding pipeline to shrink the cookies down to ~8KB, decode them on server startup, and reconstruct the valid `cookies.txt` file.
3. **Preventing Cookie Deletion (yt-dlp Bug)**: 
   `yt-dlp` has a habit of overwriting the provided cookie file with a blank one after its first request. To prevent this from ruining subsequent downloads, the app clones the master cookie file into a temporary directory for every single request, letting `yt-dlp` destroy the temp file while keeping the original safe.
4. **Bypassing FFmpeg Merging Requirements**: 
   Server environments often struggle with FFmpeg installations. Instead of downloading separate video and audio streams and merging them (which requires FFmpeg and high CPU usage), the app requests `format: 'b'` to pull pre-merged MP4 files natively provided by the servers.
5. **Mobile File Handling**: 
   Phones do not handle `.zip` files well out of the box. Instead of packaging gallery/scraper downloads into an inaccessible ZIP, the backend encodes each image individually in base64. The frontend then processes these payloads, allowing the browser to natively save each file directly to the user's camera roll/downloads folder.

## Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/woott07/Web-Dl.git
   cd dl-vd-img
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Provide Cookies (Optional but recommended for YouTube):**
   - Export your YouTube/Google cookies using a browser extension.
   - Compress and Base64 encode them using a zlib encoder script if necessary to save space.
   - Set the resulting string as the `YT_COOKIES` environment variable.

4. **Run the app locally:**
   ```bash
   python app.py
   ```
   The app will start on `http://0.0.0.0:5000`

## Disclaimer
This project is for educational purposes. Ensure you comply with the Terms of Service of the websites you are downloading from.
