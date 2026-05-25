class LLMError(Exception):
    """Base LLM service error."""


class LLMUnavailableError(LLMError):
    """Provider disabled or misconfigured."""


class LLMResponseError(LLMError):
    """Invalid or empty response from provider."""
