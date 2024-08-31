from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import os
import uuid
import subprocess
import threading
import time

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def delayed_file_removal(file_path, delay=10):
    def remove_file():
        time.sleep(delay)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Removed file: {file_path}")
            else:
                print(f"File not found: {file_path}")
        except Exception as error:
            print(f"Error removing file {file_path}: {error}")

    thread = threading.Thread(target=remove_file)
    thread.start()

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/convert", methods=["POST"])
def convert_to_mp3():
    data = request.json
    print(f"Received data: {data}")  # Debugging line
    youtube_url = data["url"]
    file_id = str(uuid.uuid4())
    video_file = os.path.join(DOWNLOAD_FOLDER, f"{file_id}.mp4")
    mp3_file = os.path.join(DOWNLOAD_FOLDER, f"{file_id}.mp3")

    # Debugging lines
    print(f"Downloading video from: {youtube_url}")
    print(f"Temporary video file: {video_file}")
    print(f"MP3 output file: {mp3_file}")

    # Download video using yt-dlp
    result = subprocess.run(["yt-dlp", "-o", video_file, youtube_url], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"yt-dlp error: {result.stderr}")
        return jsonify({"success": False, "error": "Failed to download video"})

    # Convert video to MP3 using FFmpeg
    result = subprocess.run([r"C:\ffmpeg\ffmpeg-2024-08-28-git-b730defd52-full_build\bin\ffmpeg.exe", "-i", video_file, mp3_file], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FFmpeg error: {result.stderr}")
        return jsonify({"success": False, "error": "Failed to convert video to MP3"})

    # Remove the video file after conversion
    os.remove(video_file)

    # Serve the MP3 file for download
    return jsonify({"success": True, "link": f"/download/{file_id}.mp3"})

@app.route("/download/<filename>")
def download_file(filename):
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    # Schedule the file for removal after download
    delayed_file_removal(file_path)

    # Set the Content-Disposition header to force download
    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)