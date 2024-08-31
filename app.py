from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import os
import uuid
import threading
import time
from yt_dlp import YoutubeDL

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
    video_file = os.path.join(DOWNLOAD_FOLDER, f"{file_id}.mp4.webm")  # Adjust the file extension
    mp3_file = os.path.join(DOWNLOAD_FOLDER, f"{file_id}.mp3")

    # Debugging lines
    print(f"Downloading video from: {youtube_url}")
    print(f"Temporary video file: {video_file}")
    print(f"MP3 output file: {mp3_file}")

    # Download and convert video to MP3 using yt-dlp Python package
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': mp3_file,  # Directly output the MP3 file
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
    except Exception as e:
        print(f"yt-dlp error: {e}")
        return jsonify({"success": False, "error": "Failed to download video or convert to MP3"})

    # Schedule the MP3 file for removal after a delay
    delayed_file_removal(mp3_file, delay=60)  # Remove the MP3 file after a longer delay

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
