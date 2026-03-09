import io
import os
import mimetypes
from flask import Flask, render_template, request, jsonify, send_file
import dl

# If YouTube cookies are provided via Railway variables, write them to file at startup
# Supports both raw text and base64-encoded cookies (base64 preserves newlines)
import base64 as _b64
import zlib as _zlib
yt_cookies = os.environ.get('YT_COOKIES')
if yt_cookies:
    yt_cookies = yt_cookies.strip()
    # Check if it was compressed using our new script
    if yt_cookies.startswith('ZLIB_'):
        try:
            compressed = _b64.b64decode(yt_cookies[5:])
            yt_cookies = _zlib.decompress(compressed).decode('utf-8')
        except Exception as e:
            yt_cookies = f"# FAILED_TO_DECODE_ZLIB: {str(e)}"
    # Legacy fallback: pure base64
    elif '\t' not in yt_cookies:
        try:
            yt_cookies = _b64.b64decode(yt_cookies).decode('utf-8')
        except Exception as e:
            yt_cookies = f"# FAILED_TO_DECODE_B64: {str(e)}"
            
    with open('cookies.txt', 'w', encoding='utf-8') as f:
        f.write(yt_cookies)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    dl_type = data.get('type')
    quality = data.get('quality', '1')

    if not url:
        return jsonify({'success': False, 'message': 'URL is required!'})

    try:
        mime_type = None

        if dl_type == '1':
            success, filename, result, mime_type = dl.file_downloader(url)
        elif dl_type == '2':
            success, filename, result = dl.video_downloader(url, quality)
        elif dl_type == '3':
            success, filename, result = dl.gallery_downloader(url)
        elif dl_type == '4':
            success, filename, result = dl.webpage_image_scraper(url)
        else:
            return jsonify({'success': False, 'message': 'Invalid download type selected.'})

        if not success:
            return jsonify({'success': False, 'message': result})

        # Gallery: each image as base64 for direct browser saves (no zip)
        if filename == '__GALLERY_LIST__':
            return jsonify({'success': True, 'type': 'gallery_list', 'files': result})

        # Web Scraper: same direct-save approach, each image individually
        if filename == '__SCRAPER_LIST__':
            return jsonify({'success': True, 'type': 'gallery_list', 'files': result})

        # Fallback: guess mime type from filename if not already set
        if not mime_type:
            guessed, _ = mimetypes.guess_type(filename)
            mime_type = guessed or 'application/octet-stream'

        # Stream file to browser with correct Content-Type so phone can open it
        return send_file(
            io.BytesIO(result),
            download_name=filename,
            mimetype=mime_type,
            as_attachment=True
        )

    except Exception as e:
        return jsonify({'success': False, 'message': f'Server Error: {str(e)}'})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
