from flask import Flask, send_file, request, jsonify, after_this_request, render_template
from flask_cors import CORS
from pytubefix import YouTube
from pytubefix.cli import on_progress
from moviepy.editor import VideoFileClip
import os
import time
import threading
import uuid
import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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
    
    unique_id = str(uuid.uuid4())
    
    yt = YouTube(url, on_progress_callback=on_progress)
    print(yt.title)
    
    ys = yt.streams.get_highest_resolution()
    
    mp4_path = f'{yt.title}_{unique_id}.mp4'
    mp3_path = f'{yt.title}_{unique_id}.mp3'

    ys.download(filename=mp4_path)

    with VideoFileClip(mp4_path) as video:
        video.audio.write_audiofile(mp3_path)
    
    @after_this_request
    def cleanup(response):
        def remove_files():
            time.sleep(1)
            try:
                os.remove(mp4_path)
                os.remove(mp3_path)
            except Exception as e:
                print(f'Error removing files: {e}')
        
        threading.Thread(target=remove_files).start()
        return response
    
    if 'X-Forwarded-For' in request.headers:
        user_ip = request.headers['X-Forwarded-For'].split(',')[0].strip()
    else:
        user_ip = request.remote_addr
    
    video_title = yt.title

    DATABASE_URL = os.getenv('DATABASE_URL')
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO conversions (user_ip, video_url, video_title)
        VALUES (%s, %s, %s)
    ''', (user_ip, url, video_title))
    conn.commit()
    cursor.close()
    conn.close()
    
    return send_file(
        mp3_path,
        as_attachment=True,
        download_name=f'{yt.title}_{unique_id}.mp3'
    )

if __name__ == '__main__':
    app.run(debug=True)
