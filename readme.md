Welcome to Discord Bots!
---
This repository contains the source code for various bots that I've created for my own Discord servers to help with various tasks.

Layout
------
- `bot/`: one folder per Discord bot
- `website/`: websites that go with the bots
- `scripts/move-ignored-files.sh`: run it once in an older clone after pulling the `bot/` + `website/` move. It carries `.env`, `locale.json` and `data/` along, because git doesn't move ignored files.

Voice Chat Bot
--------------
This bot notifies the General channel in the Discord server when a user joins a previously empty voice channel. There is a short timeout for the voice channel when it becomes empty to prevent spamming.

Twitch Bot
----------
This bot notifies the General channel in the Discord server when a Twitch streamer defined in the configuration file goes live on Twitch.

Music Bot
----------
This bot joins a voice channel upon request from a user to play a song that they have entered. It proceeds then to play that song and allows users to queue more songs.

Game Night Bot
--------------
This bot tracks a group's game rotation for game night. It integrates with the RAWG API to enrich game data and lets members add/remove games, log sessions, and view the rotation ranked by last played date. All bot dialogue is customizable via a locale file. Runs in Docker.

Game Night Website
------------------
Not a bot. It's the companion site for the Game Night Bot, deployed to Vercel from `website/game-night-website/`. It charts which genres and games the group plays, has an API for Grok Bot to post patch notes and game suggestions, and has a password-protected admin page. It shares a Postgres database with the bot.

Requirements
------------
Python 3

Commands to Execute Scripts
---------------------------
python3 bot/voice-chat-bot/voice-chat-bot.py\
python3 bot/twitch-bot/twitch-bot.py
