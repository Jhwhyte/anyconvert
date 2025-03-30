from flask import Flask, send_file, request, jsonify, after_this_request, render_template
from flask_cors import CORS
from pytubefix import YouTube
from pytubefix.cli import on_progress
import os
import time
import threading
import uuid
import subprocess

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

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
        yt = YouTube(url, 'MWEB', on_progress_callback=on_progress)
        print(f"Attempting to download: {yt.title}")
        
        # Get audio stream
        ys = yt.streams.get_audio_only()
        
        # Clean filename (remove characters that might cause issues)
        safe_title = ''.join(c for c in yt.title if c.isalnum() or c in ' -_').strip()
        
        # Set the file name without extension
        mp4_filename = f'{safe_title}_{unique_id}.mp4'
        mp3_filename = f'{safe_title}_{unique_id}.mp3'
        
        # Download the audio stream as MP4
        ys.download(output_path='.', filename=mp4_filename)
        print(f"Downloaded: {mp4_filename}")
        
        # Convert the downloaded MP4 file to proper MP3 using ffmpeg
        if os.path.exists(mp4_filename):
            ffmpeg_command = f'ffmpeg -i "{mp4_filename}" -vn -acodec libmp3lame "{mp3_filename}"'
            subprocess.run(ffmpeg_command, shell=True)
            print(f"Converted to MP3: {mp3_filename}")
            
            # Remove the original MP4 file after conversion
            os.remove(mp4_filename)
        
        if not os.path.exists(mp3_filename):
            return jsonify({'error': 'Converted MP3 file not found'}), 500
        
        @after_this_request
        def cleanup(response):
            def remove_files():
                time.sleep(1)
                try:
                    os.remove(mp3_filename)
                    print(f'Removed file: {mp3_filename}')
                except Exception as e:
                    print(f'Error removing file: {e}')
            
            threading.Thread(target=remove_files).start()
            return response
        
        # Send the converted MP3 file
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
    # For production, you might want to use a production WSGI server instead
    # Configure host and port based on your hosting environment
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
