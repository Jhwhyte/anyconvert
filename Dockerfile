FROM python:3.11-slim-buster

# Install FFmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Copy your application code
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Expose the port your Flask app will listen on
EXPOSE 5000

# Define the command to run your Flask app
CMD ["python", "app.py"]