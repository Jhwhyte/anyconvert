from flask import Flask, send_file, request, jsonify, after_this_request, render_template
from flask_cors import CORS
import yt_dlp
import os
import time
import threading
import uuid

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download_file():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    
    try:
        unique_id = str(uuid.uuid4())
        download_folder = '.'
        
        # Configure yt-dlp download options
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(download_folder, f'%(title)s_{unique_id}.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'noplaylist': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'audio')
        
        safe_title = ''.join(c for c in title if c.isalnum() or c in ' -_').strip()
        mp3_filename = f"{safe_title}_{unique_id}.mp3"

        if not os.path.exists(mp3_filename):
            return jsonify({'error': 'Converted MP3 file not found'}), 500

        @after_this_request
        def cleanup(response):
            def remove_file():
                time.sleep(1)
                try:
                    os.remove(mp3_filename)
                    print(f'Removed file: {mp3_filename}')
                except Exception as e:
                    print(f'Error removing file: {e}')
            threading.Thread(target=remove_file).start()
            return response

        return send_file(
            mp3_filename,
            as_attachment=True,
            download_name=f"{safe_title}.mp3",
            mimetype="audio/mpeg"
        )
    
    except Exception as e:
        print(f'Error during download: {e}')
        return jsonify({'error': f'Error converting video: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
