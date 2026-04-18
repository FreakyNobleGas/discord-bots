import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN: str = os.environ["DISCORD_TOKEN"]
DISCORD_GUILD_ID: int = int(os.environ["DISCORD_GUILD_ID"])
RAWG_API_KEY: str = os.environ["RAWG_API_KEY"]
ANTHROPIC_API_KEY: str = os.environ["ANTHROPIC_API_KEY"]

ROTATION_CHANNEL_ID: int = int(os.environ["ROTATION_CHANNEL_ID"])
REMINDER_CHANNEL_ID: int = int(os.environ["REMINDER_CHANNEL_ID"])

MIN_SESSIONS: int = int(os.getenv("MIN_SESSIONS", "3"))
EARLY_EXIT_VOTES: int = int(os.getenv("EARLY_EXIT_VOTES", "4"))
COOLDOWN_WEEKS: int = int(os.getenv("COOLDOWN_WEEKS", "4"))
REMINDER_TIME: str = os.getenv("REMINDER_TIME", "18:00")

DB_PATH: str = os.getenv("DB_PATH", "/app/data/rotation.db")
