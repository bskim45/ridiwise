import datetime
import re
import urllib.parse
from typing import Optional, TypedDict
from zoneinfo import ZoneInfo

from playwright.sync_api import (
    Locator,
)
from playwright.sync_api import (
    TimeoutError as PlaywrightTimeoutError,
)

from ridiwise.api.browser_base_client import BrowserBaseClient

DOMAIN = 'www.longblack.co'
COOKIE_DOMAIN = f'https://{DOMAIN}'

SELECTOR_LOGIN_USER_ID = 'form.login-form input[name="email"]'
SELECTOR_LOGIN_PASSWORD = 'form.login-form input[name="password"]'
SELECTOR_LOGIN_BUTTON = 'form.login-form button[type="submit"]'


class Note(TypedDict):
    """
    Article
    """

    note_id: str
    note_url: str
    title: str
    author: Optional[str]
    cover_image_url: Optional[str]


class Scrap(TypedDict):
    """
    Highlight
    """

    scrap_id: str
    scrap_url: str
    highlighted_text: str
    memo: Optional[str]
    created_datetime: datetime.datetime
    note: Note


class LongblackClient(BrowserBaseClient):
    base_url = f'https://{DOMAIN}'
    provider = 'longblack'
    storage_state_filename = f'browser_state_{provider}.json'

    def __init__(
        self,
        user_id: str,
        password: str,
        *args,
        **kwargs,
    ):
        self.user_id = user_id
        self.password = password

        super().__init__(*args, **kwargs)

    @staticmethod
    def parse_scrap_url(url) -> Optional[tuple[str, str]]:
        """
        Extracts the book_id from a given URI.
        """
        pattern = re.compile(r'/note/(\d+).*#memoId=([A-Za-z0-9]+)')
        match = pattern.search(url)
        if match:
            note_id, scrap_id = match.groups()
            return note_id, scrap_id
        return None

    @staticmethod
    def parse_scrap_date(datetime_string) -> Optional[datetime.datetime]:
        """
        Parses a date string in the format 'YYYY.MM.DD HH:MM'
        """
        datetime_format = '%Y.%m.%d %H:%M'
        dt = datetime.datetime.strptime(datetime_string, datetime_format)
        dt = dt.replace(tzinfo=ZoneInfo('Asia/Seoul'))
        return dt

    @staticmethod
    def get_author_from_scrap_title(title: str) -> Optional[str]:
        """
        Extracts the author from the scrap title.
        """
        if ':' not in title:
            return None

        parts = title.split(':', 1)
        author = parts[0].strip()
        title = parts[1].strip()

        if not author or not title:
            return None

        return author

    def login(self):
        self.logger.info(f'Login: `{DOMAIN}`')

        with self.browser_context.new_page() as page:
            page.goto(f'{self.base_url}/login?return_url=/membership')
            page.wait_for_selector(SELECTOR_LOGIN_USER_ID)

            page.locator(SELECTOR_LOGIN_USER_ID).fill(self.user_id)
            page.locator(SELECTOR_LOGIN_PASSWORD).fill(self.password)

            page.click(SELECTOR_LOGIN_BUTTON)

            try:
                page.wait_for_url('**/membership')
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                self.browser_context.storage_state(
                    path=self.cache_dir / self.storage_state_filename
                )
            except PlaywrightTimeoutError as e:
                self.logger.error('Login timeout')
                raise e

    def is_authenticated(self) -> bool:
        with self.browser_context.new_page() as page:
            res = page.request.get(f'{self.base_url}/membership', max_redirects=0)
            return res.ok

    def get_scraps(self) -> list[Scrap]:
        if not self.is_authenticated():
            self.logger.info('Login required')
            self.login()

        scraps = []

        # get recent 20 pages only to avoid spamming the server
        for page_num in range(1, 21):
            query_params = urllib.parse.urlencode(
                {
                    'page': page_num,
                    'view': 'note',
                    'sort': 'latest',
                    'search': '',
                }
            )

            with self.browser_context.new_page() as page:
                page.goto(f'{self.base_url}/scrap?{query_params}')
                items = page.locator('.swiper-slide:has(div.scrap)').all()

                if not items:
                    break

                scraps.extend([self._parse_dom(item) for item in items])

        return scraps

    def _parse_dom(self, elem: Locator) -> Scrap:
        highlighted_text = elem.locator('.scrap-content').inner_text().strip()
        date_str = elem.locator('.date').text_content().strip()
        scrap_date = self.parse_scrap_date(date_str)

        note_info = elem.locator('a.note-info')

        scrap_url = note_info.get_attribute('href')
        note_id, scrap_id = self.parse_scrap_url(scrap_url)
        note_title = note_info.locator('span').text_content().strip()
        note_cover_image_url = note_info.locator('img').get_attribute('src')

        memo = self._get_memo(elem)

        return {
            'scrap_id': scrap_id,
            'scrap_url': scrap_url,
            'highlighted_text': highlighted_text,
            'memo': memo,
            'created_datetime': scrap_date,
            'note': {
                'title': note_title,
                'note_url': f'{self.base_url}/note/{note_id}',
                'note_id': note_id,
                'author': self.get_author_from_scrap_title(note_title),
                'cover_image_url': note_cover_image_url,
            },
        }

    @staticmethod
    def _get_memo(elem: Locator) -> Optional[str]:
        memo_button = elem.locator('.actions').locator('button.show-memo')
        indicator = memo_button.locator('.memo-icon.dot')

        if not indicator.is_visible():
            return None

        memo_button.click()
        memo_modals = elem.page.locator('.memo-modal')
        memo_modal = memo_modals.locator('visible=true')

        if not memo_modal.is_visible():
            try:
                memo_modal = memo_modals.last
                memo_modal.wait_for(state='visible')
            except PlaywrightTimeoutError:
                return None

        memo = memo_modal.get_by_role('textbox').input_value()
        memo_modal.locator('.actions').locator('button.negative').click()

        return memo
