from flask import Flask, send_file, request, jsonify, after_this_request, render_template
from flask_cors import CORS
from pytubefix import YouTube
from pytubefix.cli import on_progress
from moviepy.editor import VideoFileClip
import os
import time
import threading
import uuid

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
    
    # Generate a unique identifier
    unique_id = str(uuid.uuid4())
    
    yt = YouTube(url, on_progress_callback=on_progress)
    print(yt.title)
    
    ys = yt.streams.get_highest_resolution()
    
    # Use unique ID to avoid conflicts
    mp4_path = f'{yt.title}_{unique_id}.mp4'
    mp3_path = f'{yt.title}_{unique_id}.mp3'

    ys.download(filename=mp4_path)

    # Load the mp4 file
    with VideoFileClip(mp4_path) as video:
        # Extract audio from video
        video.audio.write_audiofile(mp3_path)
    
    @after_this_request
    def cleanup(response):
        def remove_files():
            time.sleep(1)  # Delay to ensure file is released
            try:
                os.remove(mp4_path)
                os.remove(mp3_path)
            except Exception as e:
                print(f'Error removing files: {e}')
        
        # Start a new thread to remove the files
        threading.Thread(target=remove_files).start()
        return response
    
    return send_file(
        mp3_path,
        as_attachment=True,
        download_name=f'{yt.title}_{unique_id}.mp3'
    )

if __name__ == '__main__':
    app.run(debug=True)
