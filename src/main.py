import os
from flask import Flask, request
import boto3
from dotenv import load_dotenv
from src.functions import *

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
@app.route("/create_thumbnails/<s3_name>/<s3_url_to_save>", methods=["GET"])
def create_thumbnails(s3_name, s3_url_to_save):
    if 'Content-Type' not in request.headers and request.headers['Content-Type'] != 'video/mp4':
        return {"error": "Content-Type header not set to video/mp4"}, 400
    video_data = request.data
    if video_data == b'':
        return {"error": "No video data"}, 400

    tempFolder = generateRandomString(20)
    create_temp_folder(tempFolder)

    save_video(video_data, tempFolder)

    width, height, duration = getVideoData(tempFolder)
    
    interval = int(os.getenv("INTERVAL"))

    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    createStoryboard(os.path.join(current_dir, tempFolder), width, height, interval)

    createThumbnails(os.path.join(current_dir, tempFolder), width, height, duration, interval)

    # uploading to s3
    saved = save_files_in_s3(s3, tempFolder, s3_name, s3_url_to_save)
    if not saved:
        return {"error": "Failed to upload to S3"}, 500

    return {"message": "Successfully created files in S3"}, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)