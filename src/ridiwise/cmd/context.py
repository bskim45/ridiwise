import enum
import logging
from pathlib import Path
from typing import Optional, TypedDict


@enum.unique
class AuthMethod(enum.StrEnum):
    # BROWSER_COOKIE = 'browser_cookie'
    HEADLESS_BROWSER = 'headless_browser'


class AuthState(TypedDict, total=False):
    auth_method: str
    user_id: Optional[str]
    password: Optional[str]


class ContextState(TypedDict):
    logger: logging.Logger
    auths: dict[str, AuthState]
    config_dir: Path
    cache_dir: Path

    # headless browser options
    headless_mode: bool
    browser_timeout_seconds: int
