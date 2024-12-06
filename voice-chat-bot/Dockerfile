#
# docker build -t freakynoblegas/voice-chat-bot:1.0 .
#
FROM python:3.12-slim

WORKDIR /app

COPY . .

ARG DISCORD_TOKEN

ENV DISCORD_TOKEN=$DISCORD_TOKEN

RUN pip3 install -r requirements.txt

CMD ["python", "voice-chat-bot.py"]