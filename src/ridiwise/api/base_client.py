import abc
import logging
import typing

from httpx import Auth, Client, Request, Response


class HTTPTokenAuth(Auth):
    """Attaches HTTP Token Authentication to a given Request object."""

    def __init__(self, keyword='Bearer', token=None):
        self.keyword = keyword
        self.token = token

    def auth_flow(self, request: Request) -> typing.Generator[Request, Response, None]:
        request.headers['Authorization'] = f'{self.keyword} {self.token}'
        yield request


class BaseClient(metaclass=abc.ABCMeta):
    provider: str
    base_url: str

    def __init__(self, *args, **kwargs):
        self.client = Client(base_url=self.base_url, *args, **kwargs)
        self.logger = logging.getLogger(name=self.provider)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.client.close()

    # pylint: disable=unnecessary-dunder-call
    def start(self):
        self.__enter__()

    def close(self):
        self.__exit__()
