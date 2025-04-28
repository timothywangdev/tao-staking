from typing import List
from desearch_py import Desearch
from ..config import settings
import logging

logger = logging.getLogger(__name__)


class DesearchClient:
    def __init__(self):
        self.client = Desearch(api_key=settings.DATURA_API_KEY)

    def search_tweets(self, query: str, count: int = 10) -> List[str]:
        result = self.client.basic_twitter_search(query=query)
        return [tweet["text"] for tweet in result]
