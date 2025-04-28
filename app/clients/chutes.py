from typing import List, Optional
import httpx
from app.config import settings

CHUTES_API_URL = "https://llm.chutes.ai/v1/chat/completions"


class ChutesClient:
    """
    Synchronous client for interacting with the Chutes LLM API.
    """

    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize the ChutesClient.
        Args:
            api_token: Optional API key for Chutes LLM. If not provided, uses settings.CHUTES_API_KEY.
        Raises:
            ValueError: If no API key is provided or found in config.
        """
        self.api_token = api_token or settings.CHUTES_API_KEY
        if not self.api_token:
            raise ValueError(
                "Chutes API key must be provided or set in CHUTES_API_KEY env var/.env."
            )
        self.client = httpx.Client()

    def close(self):
        """
        Close the underlying HTTP client.
        """
        self.client.close()

    def _get_headers(self) -> dict:
        """
        Build HTTP headers for Chutes API requests, including authorization.
        Returns:
            dict: Headers with Bearer token and content type.
        """
        return {"Authorization": f"Bearer {self.api_token}", "Content-Type": "application/json"}

    def _chat_completions(
        self,
        prompt: str,
        model: str = "unsloth/Llama-3.2-3B-Instruct",
        max_tokens: int = 1024,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> str:
        """
        Internal helper to call the Chutes LLM chat completions API.
        Args:
            prompt: The prompt string to send to the LLM.
            model: The model name to use (default: unsloth/Llama-3.2-3B-Instruct).
            max_tokens: Maximum tokens to generate in the response.
            temperature: Sampling temperature for the LLM.
            stream: Whether to use streaming responses (default: False).
        Returns:
            str: The LLM's response content (usually a string or number, depending on prompt).
        Raises:
            httpx.HTTPStatusError: If the HTTP request fails.
        """
        headers = self._get_headers()
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": stream,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        response = self.client.post(CHUTES_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    def get_sentiment_score(self, tweets: List[str]) -> int:
        """
        Analyze the sentiment of a list of tweets using the Chutes LLM API.
        Args:
            tweets: List of tweet strings to analyze.
        Returns:
            int: Sentiment score between -100 (extremely negative) and +100 (extremely positive).
        Raises:
            ValueError: If the LLM response is not an integer or is out of range.
        """
        tweets_text = "\n".join(tweets)
        prompt = (
            "You are a sentiment analysis expert. Given the following tweets about a blockchain subnet, "
            "analyze the overall sentiment and respond with a single integer between -100 (extremely negative) "
            "and +100 (extremely positive). Do not explain your answer. Only output the integer.\n\n"
            f"Tweets:\n{tweets_text}\n\nSentiment score:"
        )
        content = self._chat_completions(prompt)
        try:
            score = int(content)
        except ValueError:
            raise ValueError(f"Unexpected response from Chutes LLM: {content}")
        if not -100 <= score <= 100:
            raise ValueError(f"Score out of range: {score}")
        return score
