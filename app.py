from flask import Flask, render_template, request, jsonify
import dl  # Import your downloader script!

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

    # Call the appropriate function from dl.py
    try:
        if dl_type == '1':
            success, message = dl.file_downloader(url)
        elif dl_type == '2':
            success, message = dl.video_downloader(url, quality)
        elif dl_type == '3':
            success, message = dl.gallery_downloader(url)
        elif dl_type == '4':
            success, message = dl.webpage_image_scraper(url)
        else:
            return jsonify({'success': False, 'message': 'Invalid download type selected.'})
            
        return jsonify({'success': success, 'message': message})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Server Error: {str(e)}'})

if __name__ == '__main__':
    # host='0.0.0.0' makes it accessible from your phone on the same WiFi!
    app.run(debug=True, host='0.0.0.0', port=5000)
