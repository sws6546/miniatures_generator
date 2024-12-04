import string
import random
import math
import os
from moviepy.editor import VideoFileClip
from botocore.exceptions import NoCredentialsError
import shutil

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

def upload_to_s3(s3, file_name, bucket, object_name=None):
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


def create_temp_folder(tempFolder):
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    while os.path.exists(os.path.join(current_dir, tempFolder)):
        tempFolder = generateRandomString(20)
    os.mkdir(os.path.join(current_dir, tempFolder))

def save_video(video_data, tempFolder):
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(current_dir, tempFolder, "video.mp4"), "wb") as f:
        f.write(video_data)

def save_files_in_s3(s3, tempFolder, s3_name, s3_url_to_save):
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    try:
        upload_to_s3(s3, os.path.join(current_dir, tempFolder, "thumbnails.vtt"), f"{s3_name}", f"{s3_url_to_save}/thumbnails.vtt")
        upload_to_s3(s3, os.path.join(current_dir, tempFolder, "storyboard.jpg"), f"{s3_name}", f"{s3_url_to_save}/storyboard.jpg")

        shutil.rmtree(os.path.join(current_dir, tempFolder))
        return True
    except:
        shutil.rmtree(os.path.join(current_dir, tempFolder))
        return False
