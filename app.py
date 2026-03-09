import io
from flask import Flask, render_template, request, jsonify, send_file
import dl

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
        if dl_type == '1':
            success, filename, result = dl.file_downloader(url)
        elif dl_type == '2':
            success, filename, result = dl.video_downloader(url, quality)
        elif dl_type == '3':
            success, filename, result = dl.gallery_downloader(url)
        elif dl_type == '4':
            success, filename, result = dl.webpage_image_scraper(url)
        else:
            return jsonify({'success': False, 'message': 'Invalid download type selected.'})

        if not success:
            # result is the error message string
            return jsonify({'success': False, 'message': result})

        # result is bytes — stream straight to the user's browser
        return send_file(
            io.BytesIO(result),
            download_name=filename,
            as_attachment=True
        )

    except Exception as e:
        return jsonify({'success': False, 'message': f'Server Error: {str(e)}'})


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
