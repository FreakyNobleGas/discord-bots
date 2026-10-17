import discord

from bot import config
from bot.locale import t


def site_view(path: str = "/") -> discord.ui.View | None:
    """A link button to the game night website, or None when SITE_URL isn't set.

    Paths must exist on the site (see ../game-night-website and CLAUDE.md).
    """
    if not config.SITE_URL:
        return None
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label=t("site_link_label"), url=f"{config.SITE_URL}{path}"))
    return view


def with_site_link(path: str = "/", **kwargs) -> dict:
    """Message kwargs plus the site link view, if there is one.

    discord.py rejects view=None on followup sends, so only add the key when set.
    """
    view = site_view(path)
    if view is not None:
        kwargs["view"] = view
    return kwargs
