import json
from pathlib import Path

_ROOT = Path(__file__).parent.parent
_LOCALE_FILE = _ROOT / "locale.json"
_EXAMPLE_FILE = _ROOT / "locale.example.json"


def _load() -> dict:
    source = _LOCALE_FILE if _LOCALE_FILE.exists() else _EXAMPLE_FILE
    with open(source, encoding="utf-8") as f:
        return json.load(f)


_strings: dict = _load()


def t(key: str, **kwargs) -> str:
    template = _strings.get(key, key)
    return template.format(**kwargs) if kwargs else template
