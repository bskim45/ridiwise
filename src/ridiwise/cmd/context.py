import logging
from pathlib import Path
from typing import Optional, TypedDict


class AuthState(TypedDict, total=False):
    auth_method: str
    user_id: Optional[str]
    password: Optional[str]


class ContextState(TypedDict):
    logger: logging.Logger
    auth: AuthState
    config_dir: Path
    cache_dir: Path

    headless_mode: bool
