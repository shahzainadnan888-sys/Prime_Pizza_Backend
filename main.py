"""Process entrypoint for local development and process managers."""

from __future__ import annotations

import uvicorn
from app.config.settings import get_settings


def main() -> None:
    """Run the ASGI server with settings-driven host/port."""
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
