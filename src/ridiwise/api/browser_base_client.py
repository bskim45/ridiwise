from pathlib import Path

from playwright.sync_api import sync_playwright

from ridiwise.api.base_client import BaseClient


class BrowserBaseClient(BaseClient):
    storage_state_filename = 'browser_state.json'

    # pylint: disable=keyword-arg-before-vararg,fixme
    # TODO: fix lint error
    def __init__(
        self,
        cache_dir: Path,
        headless: bool = True,
        browser_timeout_seconds: int = 10,
        *args,
        **kwargs,
    ):
        self.cache_dir = cache_dir
        self.headless = headless
        self.browser_timeout_seconds = browser_timeout_seconds

        self.playwright = None
        self.browser = None
        self.browser_context = None

        super().__init__(*args, **kwargs)

    def __enter__(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)

        try:
            self.browser_context = self.browser.new_context(
                storage_state=self.cache_dir / self.storage_state_filename
            )
        except FileNotFoundError:
            self.browser_context = self.browser.new_context()

        self.browser_context.set_default_timeout(self.browser_timeout_seconds * 1000)

        super().__enter__()
        return self

    def __exit__(self, *args):
        self.browser_context.close()
        self.browser.close()
        self.playwright.stop()

        super().__exit__(*args)
