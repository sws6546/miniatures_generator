Po wysłaniu zapytania http na `/create_thumbnails/<s3_name>/<s3_url_to_save>` i wysłaniu pliku .mp4 zapisuje się storyboard.jpg i thumbnails.vtt na s3

Aby działało należy dodać plik `.env`:
```
REGION_NAME=<eg. us-east-1>
AWS_ACCES_KEY_ID=<id key>
AWS_SECRET_ACCES_KEY=<secret key>
ENDPOINT_URL=<endpoint url>
INTERVAL=<co ile sekund ma się pojawiać nowy obrazek>
```

Plik `generator.py` jest z projektu: `https://github.com/flavioribeiro/video-thumbnail-generator`

Można także zmienić w `Dockerfile` liczbę workerów:
```
CMD [ "gunicorn", "--bind", "0.0.0.0:5000", "src.main:app", "-w", "<liczba>" ]
```
https://docs.gunicorn.org/en/latest/run.html
https://flask.palletsprojects.com/en/stable/deploying/gunicorn/