FROM python:3.11-slim-buster

# Install FFmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy your application code
COPY . .

# Define the command to run your Flask app
CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0"]
