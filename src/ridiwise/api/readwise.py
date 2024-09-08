import json
from typing import Literal, Optional, TypeAlias, TypedDict

import httpx

from ridiwise.api.base_client import BaseClient, HTTPTokenAuth

# https://readwise.io/api_deets
API_BASE_URL = 'https://readwise.io/api/v2'


BookCategory: TypeAlias = Literal['books', 'articles', 'tweets', 'podcasts']
HighlightLocationType: TypeAlias = Literal['page', 'order', 'time_offset']


class CreateHighlightRequestItem(TypedDict, total=False):
    text: str
    title: str
    author: Optional[str]
    category: Optional[BookCategory]
    location: Optional[int]
    location_type: Optional[HighlightLocationType]
    highlighted_at: Optional[str]
    source_url: Optional[str]
    source_type: Optional[str]
    image_url: Optional[str]
    note: Optional[str]
    highlight_url: Optional[str]


class CreateHighlightsRequest(TypedDict):
    highlights: list[CreateHighlightRequestItem]


class CreateHighlightResponseItem(TypedDict):
    id: int
    title: Optional[str]
    author: Optional[str]
    category: Optional[BookCategory]
    source: Optional[str]
    num_highlights: int
    last_highlight_at: Optional[str]
    updated: str
    cover_image_url: Optional[str]
    highlights_url: Optional[str]
    source_url: Optional[str]
    modified_highlights: list[int]


CreateHighlightsResponse: TypeAlias = list[CreateHighlightResponseItem]


class CreateHighlightTagRequest(TypedDict):
    name: str


class CreateHighlightTagResponse(TypedDict):
    id: int
    name: str


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
        highlights: list[CreateHighlightRequestItem],
    ) -> CreateHighlightsResponse:
        payload: CreateHighlightsRequest = {'highlights': highlights}

        self.logger.debug(json.dumps(payload, indent=2, ensure_ascii=False))

        response = self.client.post('/highlights/', auth=self.auth, json=payload)
        response.raise_for_status()
        return response.json()

    def create_highlight_tag(
        self,
        highlight_id: int,
        tag: str,
    ) -> CreateHighlightTagResponse:
        payload: CreateHighlightTagRequest = {'name': tag}

        response = self.client.post(
            f'/highlights/{highlight_id}/tags/',
            auth=self.auth,
            json=payload,
        )
        response.raise_for_status()
        return response.json()
