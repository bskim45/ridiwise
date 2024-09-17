import datetime
import unittest
from zoneinfo import ZoneInfo

from ridiwise.api.longblack import LongblackClient


class TestLongblackClient(unittest.TestCase):
    def test_parse_scrap_url(self):
        test_cases = [
            {
                'url': 'https://www.longblack.co/note/12345#memoId=H172649477900012abc123',
                'expected': ('12345', 'H172649477900012abc123'),
            },
            {
                'url': 'https://www.longblack.co/note/invalid#memoId=invalid',
                'expected': None,
            },
            {'url': 'https://www.longblack.co/invalid/url', 'expected': None},
        ]

        for case in test_cases:
            with self.subTest(case=case):
                result = LongblackClient.parse_scrap_url(case['url'])
                self.assertEqual(result, case['expected'])

    def test_parse_scrap_date(self):
        test_cases = [
            (
                '2023.10.01 12:00',
                datetime.datetime(2023, 10, 1, 12, 0, tzinfo=ZoneInfo('Asia/Seoul')),
            ),
            (
                '2022.01.15 08:30',
                datetime.datetime(2022, 1, 15, 8, 30, tzinfo=ZoneInfo('Asia/Seoul')),
            ),
            (
                '2021.12.31 23:59',
                datetime.datetime(2021, 12, 31, 23, 59, tzinfo=ZoneInfo('Asia/Seoul')),
            ),
            (
                '2020.02.29 00:00',
                datetime.datetime(2020, 2, 29, 0, 0, tzinfo=ZoneInfo('Asia/Seoul')),
            ),
        ]

        for case in test_cases:
            with self.subTest(case=case):
                result = LongblackClient.parse_scrap_date(case[0])
                self.assertEqual(result, case[1])

    def test_parse_author_from_scrap_title(self):
        test_cases = [
            {'title': 'Author Name: Title', 'expected': 'Author Name'},
            {'title': 'Author Name: Title: Subtitle', 'expected': 'Author Name'},
            {'title': 'Author Name : Title', 'expected': 'Author Name'},
            {'title': 'Author Name:Title', 'expected': 'Author Name'},
            {'title': 'Author Name :Title', 'expected': 'Author Name'},
            {'title': 'Title', 'expected': None},
        ]

        for case in test_cases:
            with self.subTest(case=case):
                result = LongblackClient.get_author_from_scrap_title(case['title'])
                self.assertEqual(result, case['expected'])


if __name__ == '__main__':
    unittest.main()
