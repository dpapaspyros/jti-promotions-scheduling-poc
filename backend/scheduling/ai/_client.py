"""OpenAI-compatible client factory."""

from django.conf import settings
from openai import OpenAI


def make_client() -> OpenAI:
    kwargs: dict = {"api_key": settings.OPENAI_API_KEY}
    if base_url := getattr(settings, "OPENAI_BASE_URL", None):
        kwargs["base_url"] = base_url
    return OpenAI(**kwargs)
