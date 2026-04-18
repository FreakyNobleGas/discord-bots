import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN: str = os.environ["DISCORD_TOKEN"]
DISCORD_GUILD_IDS: list[int] = [
    int(g.strip()) for g in os.environ["DISCORD_GUILD_IDS"].split(",")
]
RAWG_API_KEY: str = os.environ["RAWG_API_KEY"]
ANTHROPIC_API_KEY: str = os.environ["ANTHROPIC_API_KEY"]

_channel_ids: list[int] = [
    int(c.strip()) for c in os.environ["GAME_NIGHT_CHANNEL_IDS"].split(",")
]
GUILD_CHANNEL_MAP: dict[int, int] = dict(zip(DISCORD_GUILD_IDS, _channel_ids))

MIN_SESSIONS: int = int(os.getenv("MIN_SESSIONS", "3"))
EARLY_EXIT_VOTES: int = int(os.getenv("EARLY_EXIT_VOTES", "4"))
COOLDOWN_WEEKS: int = int(os.getenv("COOLDOWN_WEEKS", "4"))
REMINDER_TIME: str = os.getenv("REMINDER_TIME", "08:00")
VOTE_WINDOW_HOURS: int = int(os.getenv("VOTE_WINDOW_HOURS", "12"))

DB_PATH: str = os.getenv("DB_PATH", "/app/data/rotation.db")
