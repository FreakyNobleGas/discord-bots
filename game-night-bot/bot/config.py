import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN: str = os.environ["DISCORD_TOKEN"]
DISCORD_GUILD_IDS: list[int] = [
    int(g.strip()) for g in os.environ["DISCORD_GUILD_IDS"].split(",")
]
RAWG_API_KEY: str = os.environ["RAWG_API_KEY"]

_channel_ids: list[int] = [
    int(c.strip()) for c in os.environ["GAME_NIGHT_CHANNEL_IDS"].split(",")
]
GUILD_CHANNEL_MAP: dict[int, int] = dict(zip(DISCORD_GUILD_IDS, _channel_ids))

REMINDER_TIME: str = os.getenv("REMINDER_TIME", "08:00")
DB_PATH: str = os.getenv("DB_PATH", "/app/data/rotation.db")
