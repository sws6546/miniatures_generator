FROM python:3.12.7-alpine
WORKDIR /app
COPY . .
RUN apk add ffmpeg
RUN pip install -r requirements.txt
CMD [ "gunicorn", "--bind", "0.0.0.0:5000", "src.main:app", "-w", "4" ]