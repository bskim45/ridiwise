import datetime
import http.cookiejar
import re
from typing import Optional, TypedDict
from zoneinfo import ZoneInfo

from playwright.sync_api import (
    ElementHandle,
)
from playwright.sync_api import (
    TimeoutError as PlaywrightTimeoutError,
)

from ridiwise.api.browser_base_client import BrowserBaseClient

DOMAIN = 'ridibooks.com'
COOKIE_DOMAIN = f'https://{DOMAIN}'

SELECTOR_LOGIN_USER_ID = 'input[placeholder="아이디"]'
SELECTOR_LOGIN_PASSWORD = 'input[placeholder="비밀번호"]'

BOOK_COVER_IMAGE_URL_FORMAT = 'https://img.ridicdn.net/cover/{book_id}/xxlarge#1'


# pylint: disable=import-outside-toplevel
def get_cookie_jar(browser: str) -> http.cookiejar.CookieJar:
    import browser_cookie3

    try:
        cookie_jar_function = getattr(browser_cookie3, browser)
        cookie_jar = cookie_jar_function(domain_name=DOMAIN)
        return cookie_jar
    except AttributeError as e:
        raise RuntimeError(f'Browser "{browser}" is not supported.') from e
    except Exception as e:
        raise RuntimeError('Unable to import cookies from browser.') from e


class Note(TypedDict):
    id: str
    highlighted_text: str
    memo: Optional[str]
    created_date: Optional[datetime.datetime]


class Book(TypedDict):
    book_title: str
    book_url: str
    book_notes_url: str
    book_id: str
    notes: list[Note]
    authors: list[str]
    book_cover_image_url: str


class RidiClient(BrowserBaseClient):
    base_url = f'https://{DOMAIN}'
    provider = 'ridibooks'
    storage_state_filename = 'browser_state_ridibooks.json'

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
    def extract_book_id(uri) -> Optional[str]:
        """
        Extracts the book_id from a given URI.
        """
        pattern = re.compile(r'/reading-note/detail/(\d+)')
        match = pattern.search(uri)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def parse_note_date(date_string) -> Optional[datetime.datetime]:
        """
        Parses a date string in the format 'YYYY.MM.DD.'
        """
        pattern = re.compile(r'(\d{4})\.(\d{2})\.(\d{2})\.')

        # Use regex to find the date components
        match = pattern.match(date_string)
        if match:
            year, month, day = map(int, match.groups())
            return datetime.datetime(year, month, day, tzinfo=ZoneInfo('Asia/Seoul'))

        return None

    def login(self):
        self.logger.info('Login: `ridibooks.com`')

        with self.browser_context.new_page() as page:
            page.goto(
                f'{self.base_url}/account/login?return_url=https%3A%2F%2Fridibooks.com%2Faccount%2Fmyridi'  # pylint: disable=line-too-long  # noqa: E501
            )

            page.wait_for_selector(SELECTOR_LOGIN_USER_ID)

            page.locator(SELECTOR_LOGIN_USER_ID).fill(self.user_id)
            page.locator(SELECTOR_LOGIN_PASSWORD).fill(self.password)

            page.click('button[type="submit"]')

            try:
                page.wait_for_url('**/myridi', timeout=3000)
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                self.browser_context.storage_state(
                    path=self.cache_dir / self.storage_state_filename
                )
            except PlaywrightTimeoutError as e:
                self.logger.error('Login timeout')
                raise e

    def is_authenticated(self) -> bool:
        with self.browser_context.new_page() as page:
            res = page.request.get(f'{self.base_url}/account/myridi', max_redirects=0)
            return res.ok

    def is_cookie_authenticated(self):
        return all(
            next(
                (
                    cookie['value']
                    for cookie in self.browser_context.cookies(COOKIE_DOMAIN)
                    if cookie['name'] == auth_key
                ),
                None,
            )
            for auth_key in ['ridi-at', 'ridi-rt']
        )

    def get_books_from_shelf(self) -> list[Book]:
        if not self.is_authenticated():
            self.logger.info('Login required')
            self.login()

        with self.browser_context.new_page() as page:
            page.goto(f'{self.base_url}/reading-note/shelf')
            items = page.query_selector_all('article li')

            books = [self._get_book_info_from_dom(item) for item in items]

            for book in books:
                book['notes'] = self.get_notes_by_book(book['book_id'])

            return books

    def _get_book_info_from_dom(self, elem: ElementHandle) -> Book:
        book_title = elem.query_selector('h3').inner_text()
        book_ids = [
            self.extract_book_id(link.get_attribute('href'))
            for link in elem.query_selector_all('a')
            if link.get_attribute('href').startswith('/reading-note/detail/')
        ]

        # pylint: disable=consider-using-set-comprehension
        book_id_set = set([book_id for book_id in book_ids if book_id is not None])

        if len(book_id_set) != 1:
            raise ValueError('Failed to get book id')

        book_id = book_id_set.pop()

        authors = [
            link.inner_text()
            for link in elem.query_selector_all('a')
            if link.get_attribute('href').startswith('/author/')
        ]

        return {
            'book_title': book_title,
            'book_url': f'{self.base_url}/books/{book_id}',
            'book_notes_url': f'{self.base_url}/reading-note/detail/{book_id}',
            'book_id': book_id,
            'notes': [],
            'authors': authors,
            'book_cover_image_url': BOOK_COVER_IMAGE_URL_FORMAT.format(book_id=book_id),
        }

    def get_notes_by_book(self, book_id):
        if not self.is_cookie_authenticated():
            self.login()

        with self.browser_context.new_page() as page:
            page.goto(f'{self.base_url}/reading-note/detail/{book_id}')

            # pylint: disable=fixme
            # TODO: Implement handling when the number of notes is very large
            for _ in range(5):
                try:
                    more_button = page.locator('article button:has-text("더보기")')
                    if not more_button.is_visible(timeout=500):
                        break
                    more_button.click()
                except PlaywrightTimeoutError:
                    break

            note_items = page.query_selector_all('article li[id^="annotation_"]')

            notes = [self._get_note_from_dom(item) for item in note_items]
            return notes

    def _get_note_from_dom(self, elem: ElementHandle) -> Optional[Note]:
        annotation_id = elem.get_attribute('id').removeprefix('annotation_')
        items = elem.query_selector_all('p')

        if not items:
            return None

        highlighted_text = items[0].inner_text().strip()

        if len(items) == 3:
            memo = items[1].inner_text().strip()
            created_date = items[2].inner_text().strip()
        else:
            memo = None
            created_date = items[1].inner_text().strip()

        return {
            'id': annotation_id,
            'highlighted_text': highlighted_text,
            'memo': memo,
            'created_date': self.parse_note_date(created_date),
        }
