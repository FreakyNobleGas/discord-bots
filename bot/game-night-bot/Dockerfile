FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.11.3 /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never

WORKDIR /app

COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev

# Copy only what the bot needs, so a local .venv never overwrites the image's.
COPY bot/ bot/
COPY scripts/ scripts/
COPY schema.sql locale*.json ./

CMD ["uv", "run", "--frozen", "--no-sync", "python", "-m", "bot.main"]
