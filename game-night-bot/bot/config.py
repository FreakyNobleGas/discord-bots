import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN: str = os.environ["DISCORD_TOKEN"]
DISCORD_GUILD_IDS: list[int] = [
    int(g.strip()) for g in os.environ["DISCORD_GUILD_IDS"].split(",")
]
RAWG_API_KEY: str = os.environ["RAWG_API_KEY"]

DB_PATH: str = os.getenv("DB_PATH", "/app/data/rotation.db")
