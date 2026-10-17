#
# docker build -t xwolfinbarger/music-bot:1.0 .
#
FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip3 install -r requirements.txt

CMD ["python", "music-bot.py"]
