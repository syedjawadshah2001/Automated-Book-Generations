from __future__ import annotations

import httpx
from openai import APIConnectionError, APIStatusError, OpenAI, RateLimitError

from app.config import Settings


class LLMService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.provider = settings.llm_provider.lower()
        self.openai_client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    def generate(self, prompt: str) -> str:
        try:
            if self.provider == "gemini":
                return self._generate_with_gemini(prompt)
            if self.provider == "openai":
                return self._generate_with_openai(prompt)
        except Exception:
            return self._fallback_response(prompt)

        return self._fallback_response(prompt)

    def _generate_with_openai(self, prompt: str) -> str:
        if not self.openai_client:
            return self._fallback_response(prompt)

        try:
            response = self.openai_client.responses.create(
                model=self.settings.openai_model,
                input=prompt,
            )
            return response.output_text.strip()
        except (RateLimitError, APIConnectionError, APIStatusError):
            return self._fallback_response(prompt)

    def _generate_with_gemini(self, prompt: str) -> str:
        if not self.settings.gemini_api_key:
            return self._fallback_response(prompt)

        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.settings.gemini_model}:generateContent"
        )
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt,
                        }
                    ]
                }
            ]
        }

        response = httpx.post(
            url,
            params={"key": self.settings.gemini_api_key},
            json=payload,
            timeout=45.0,
        )
        response.raise_for_status()
        data = response.json()
        candidates = data.get("candidates", [])
        if not candidates:
            return self._fallback_response(prompt)

        parts = candidates[0].get("content", {}).get("parts", [])
        text = "".join(part.get("text", "") for part in parts).strip()
        return text or self._fallback_response(prompt)

    @staticmethod
    def _fallback_response(prompt: str) -> str:
        lowered = prompt.lower()
        if "numbered chapter outline" in lowered:
            return (
                "Book positioning summary: A practical guide.\n\n"
                "1. Introduction to the topic - Defines the promise of the book.\n"
                "2. Core foundations - Explains the main concepts.\n"
                "3. Applied workflow - Shows how to use the concepts.\n"
                "4. Advanced patterns - Covers nuanced decisions.\n"
                "5. Final integration - Brings everything together."
            )
        if "summarize the following chapter" in lowered:
            return "This chapter advances the book with practical lessons and setup for the next section."
        return (
            "## Section 1\n"
            "This is a starter chapter draft generated in fallback mode.\n\n"
            "## Key Takeaway\n"
            "The chapter establishes a clear bridge to the next part of the book."
        )
