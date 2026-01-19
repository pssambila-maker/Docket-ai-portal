from typing import Optional, Tuple
import logging

from openai import OpenAI, AzureOpenAI

from app.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class LLMProvider:
    """Wrapper for LLM providers (OpenAI, Azure OpenAI)."""

    def __init__(self):
        self.provider = settings.llm_provider.lower()
        self.client = self._init_client()
        self.default_model = settings.openai_model

    def _init_client(self):
        """Initialize the appropriate client based on provider."""
        if self.provider == "azure_openai":
            return AzureOpenAI(
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
                azure_endpoint=settings.azure_openai_endpoint,
            )
        else:
            # Default to OpenAI
            return OpenAI(api_key=settings.openai_api_key)

    def chat(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> Tuple[str, int, int]:
        """
        Send a chat message to the LLM.

        Args:
            prompt: The user's message
            model: Model to use (defaults to configured model)
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature

        Returns:
            Tuple of (response_text, prompt_tokens, completion_tokens)
        """
        model = model or self.default_model

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            if self.provider == "azure_openai":
                # Azure uses deployment name instead of model
                response = self.client.chat.completions.create(
                    model=settings.azure_openai_deployment,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
            else:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )

            response_text = response.choices[0].message.content
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens

            logger.info(
                f"LLM call successful: model={model}, "
                f"prompt_tokens={prompt_tokens}, completion_tokens={completion_tokens}"
            )

            return response_text, prompt_tokens, completion_tokens

        except Exception as e:
            logger.error(f"LLM call failed: {str(e)}")
            raise


# Singleton instance
_llm_provider: Optional[LLMProvider] = None


def get_llm_provider() -> LLMProvider:
    """Get or create the LLM provider instance."""
    global _llm_provider
    if _llm_provider is None:
        _llm_provider = LLMProvider()
    return _llm_provider


def get_available_models() -> list[str]:
    """Get list of available models based on provider."""
    if settings.llm_provider.lower() == "azure_openai":
        return [settings.azure_openai_deployment]
    else:
        # Common OpenAI models
        return [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
        ]
