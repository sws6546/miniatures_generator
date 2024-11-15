FROM python:3.12.7-alpine
WORKDIR /app
COPY . .
RUN apk add ffmpeg
RUN pip install -r requirements.txt
CMD [ "python", "src/main.py" ]