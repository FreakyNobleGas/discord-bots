import json
from pathlib import Path

_ROOT = Path(__file__).parent.parent
_LOCALE_FILE = _ROOT / "locale.json"
_EXAMPLE_FILE = _ROOT / "locale.example.json"


def _load() -> dict:
    # The example file provides defaults, so keys added later still work with an older locale.json.
    with open(_EXAMPLE_FILE, encoding="utf-8") as f:
        strings = json.load(f)
    if _LOCALE_FILE.exists():
        with open(_LOCALE_FILE, encoding="utf-8") as f:
            strings.update(json.load(f))
    return strings


_strings: dict = _load()


def t(key: str, **kwargs) -> str:
    template = _strings.get(key, key)
    return template.format(**kwargs) if kwargs else template
