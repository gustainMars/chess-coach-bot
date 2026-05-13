import os

_VALID_SCREENS = {"study", "learn", "attack"}


def miniapp_url(screen: str) -> str | None:
    if screen not in _VALID_SCREENS:
        return None
    base = os.getenv("MINIAPP_URL", "").rstrip("/")
    if not base:
        return None
    public = os.getenv("WEBAPP_PUBLIC_URL", "").rstrip("/")
    url = f"{base}/{screen}/index.html"
    if public:
        url += f"?api={public}"
    return url
