import os
import random
import string
from flask import Flask, request, redirect, url_for
from werkzeug.utils import secure_filename
from moviepy.editor import VideoFileClip
import math
import boto3
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv
import shutil

ALLOWED_EXTENSIONS = {'mp4'}

load_dotenv()
app = Flask(__name__)

s3 = boto3.client('s3',
    region_name=f"{os.getenv("REGION_NAME")}",
    aws_access_key_id=f"{os.getenv("AWS_ACCESS_KEY_ID")}",
    aws_secret_access_key=f"{os.getenv("AWS_SECRET_ACCES_KEY")}",
    endpoint_url=f"{os.getenv("ENDPOINT_URL")}"
)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generateRandomString(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

def createStoryboard(tempFolder, width, height, interval):
    width = math.floor(width/10)
    height = math.floor(height/10)
    os.system(f"{tempFolder}/../generator.py {tempFolder}/video.mp4 {interval} {width} {height} 10 {tempFolder}/storyboard.jpg")

def getVideoData(tempFolder):
    video = VideoFileClip(tempFolder + "/video.mp4")
    width, height = video.size
    duration = video.duration
    return width, height, duration
    
def createThumbnails(tempFolder, width, height, duration, interval):
    width = math.floor(width/10)
    height = math.floor(height/10)
    os.system(f"touch {tempFolder}/thumbnails.vtt")
    with open(f"{tempFolder}/thumbnails.vtt", "a") as f:
        f.write("WEBVTT\n")
        f.write("\n")
        hour = 0
        minutes = 0
        seconds = 0
        x = 0
        y = 0
        for i in range(1, math.ceil(duration/interval)):
            print(i)
            f.write(f"{hour:02d}:{minutes:02d}:{seconds:02d}.000 --> ")
            seconds += interval
            while(seconds >= 60):
                minutes += 1
                seconds = seconds - 60
            while(minutes >= 60):
                hour += 1
                minutes = minutes - 60
            f.write(f"{hour:02d}:{minutes:02d}:{seconds:02d}.000\n")
            f.write(f"storyboard.jpg#xywh={x},{y},{width},{height}\n")
            x += width
            if(x >= width*10):
                x = 0
                y += height
            f.write("\n")

        if(int(duration) % int(interval) != 0):
            f.write(f"{hour:02d}:{minutes:02d}:{seconds:02d}.000 --> ")
            seconds += duration % interval
            while(seconds >= 60):
                minutes += 1
                seconds = seconds - 60
            while(minutes >= 60):
                hour += 1
                minutes = minutes - 60
            f.write(f"{int(hour):02d}:{int(minutes):02d}:{int(seconds):02d}.000\n")
            f.write(f"storyboard.jpg#xywh={x},{y},{width},{height}\n")
            f.write("\n")

def upload_to_s3(file_name, bucket, object_name=None):
    if object_name is None:
        object_name = file_name  # If no custom object name is provided, use file_name

    try:
        # Upload the file to S3
        s3.upload_file(file_name, bucket, object_name)
        print(f"File '{file_name}' uploaded to S3 bucket '{bucket}' successfully.")
    except FileNotFoundError:
        print(f"The file '{file_name}' was not found.")
    except NoCredentialsError:
        print("Credentials not available.")

@app.route("/create_thumbnails/<s3_name>/<s3_url_to_save>", methods=["GET"])
def create_thumbnails(s3_name, s3_url_to_save):
    if 'Content-Type' not in request.headers and request.headers['Content-Type'] != 'video/mp4':
        return {"error": "Content-Type header not set to video/mp4"}, 400
    video_data = request.data
    if video_data == b'':
        return {"error": "No video data"}, 400

    # creating temp folder
    tempFolder = generateRandomString(20)
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    while os.path.exists(os.path.join(current_dir, tempFolder)):
        tempFolder = generateRandomString(20)
    os.mkdir(os.path.join(current_dir, tempFolder))

    # saving video
    with open(os.path.join(current_dir, tempFolder, "video.mp4"), "wb") as f:
        f.write(video_data)

    # getting video data
    width, height, duration = getVideoData(tempFolder)
    
    interval = 113
    # creating storyboard
    createStoryboard(os.path.join(current_dir, tempFolder), width, height, interval)

    # creating thumbnails
    createThumbnails(os.path.join(current_dir, tempFolder), width, height, duration, interval)

    # uploading to s3
    try:
        upload_to_s3(os.path.join(current_dir, tempFolder, "thumbnails.vtt"), f"{s3_name}", f"{s3_url_to_save}/thumbnails.vtt")
        upload_to_s3(os.path.join(current_dir, tempFolder, "storyboard.jpg"), f"{s3_name}", f"{s3_url_to_save}/storyboard.jpg")

        shutil.rmtree(os.path.join(current_dir, tempFolder))
    except:
        shutil.rmtree(os.path.join(current_dir, tempFolder))
        return {"error": "Failed to upload to S3"}, 500

    return {"s3_url_to_save" : s3_url_to_save}, 200

if __name__ == "__main__":
    app.run(debug=True, port=os.getenv("PORT", 5000))