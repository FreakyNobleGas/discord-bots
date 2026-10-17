import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN: str = os.environ["DISCORD_TOKEN"]
DISCORD_GUILD_IDS: list[int] = [
    int(g.strip()) for g in os.environ["DISCORD_GUILD_IDS"].split(",")
]
RAWG_API_KEY: str = os.environ["RAWG_API_KEY"]

# Neon Postgres, shared with the game night website. Use the direct (non-pooler) URL.
DATABASE_URL: str = os.environ["DATABASE_URL"]

# Public URL of the game night website, e.g. https://game-night.vercel.app (optional).
SITE_URL: str = os.getenv("SITE_URL", "").rstrip("/")
