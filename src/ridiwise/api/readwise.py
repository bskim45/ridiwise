import json
from typing import Optional, TypedDict

import httpx

from ridiwise.api.base_client import BaseClient, HTTPTokenAuth

API_BASE_URL = 'https://readwise.io/api/v2'


class CreateHighlight(TypedDict, total=False):
    text: str
    title: str
    author: Optional[str]
    category: Optional[str]
    location: Optional[str]
    location_type: Optional[str]
    highlighted_at: Optional[str]
    source_url: Optional[str]
    source_type: Optional[str]
    image_url: Optional[str]
    note: Optional[str]
    highlight_url: Optional[str]


class ReadwiseClient(BaseClient):
    base_url = API_BASE_URL
    provider = 'readwise'

    def __init__(self, token, *args, **kwargs):
        if not token:
            raise ValueError(f'{self.provider}: `token` must be provided')

        self.auth = HTTPTokenAuth(keyword='Token', token=token)
        super().__init__(*args, **kwargs)

    def validate_token(self):
        try:
            response = self.client.get('/auth/', auth=self.auth)
            response.raise_for_status()
            return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                self.logger.error('Invalid Readwise token.')
                return False

            raise e

    def create_highlights(
        self,
        highlights: list[CreateHighlight],
    ):
        payload = {'highlights': highlights}

        self.logger.debug(json.dumps(payload, indent=2, ensure_ascii=False))

        response = self.client.post('/highlights/', auth=self.auth, json=payload)
        response.raise_for_status()
        return response.json()
