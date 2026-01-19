from typing import Optional, Tuple
import logging

from openai import OpenAI, AzureOpenAI
import anthropic
import google.generativeai as genai

from app.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Model to provider mapping
MODEL_PROVIDERS = {
    # OpenAI models
    "gpt-4o": "openai",
    "gpt-4o-mini": "openai",
    "gpt-4-turbo": "openai",
    "gpt-4": "openai",
    "gpt-3.5-turbo": "openai",
    "o1-preview": "openai",
    "o1-mini": "openai",
    # Anthropic models (current as of 2026)
    "claude-sonnet-4-5-20250929": "anthropic",
    "claude-opus-4-1-20250805": "anthropic",
    "claude-haiku-3-5-20241022": "anthropic",
    # Google models (Gemini 2.0+)
    "gemini-2.0-flash": "google",
    "gemini-2.0-flash-lite": "google",
    "gemini-2.5-flash-lite": "google",
}


class MultiLLMProvider:
    """Wrapper for multiple LLM providers (OpenAI, Anthropic, Google)."""

    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        self.google_configured = False
        self.default_model = settings.openai_model
        self._init_clients()

    def _init_clients(self):
        """Initialize all available clients based on API keys."""
        # OpenAI
        if settings.openai_api_key:
            self.openai_client = OpenAI(api_key=settings.openai_api_key)
            logger.info("OpenAI client initialized")

        # Anthropic
        if settings.anthropic_api_key:
            self.anthropic_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            logger.info("Anthropic client initialized")

        # Google
        if settings.google_api_key:
            genai.configure(api_key=settings.google_api_key)
            self.google_configured = True
            logger.info("Google AI client initialized")

    def _get_provider_for_model(self, model: str) -> str:
        """Determine which provider to use for a given model."""
        return MODEL_PROVIDERS.get(model, "openai")

    def chat(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> Tuple[str, int, int]:
        """
        Send a chat message to the appropriate LLM based on model.

        Args:
            prompt: The user's message
            model: Model to use (determines provider automatically)
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature

        Returns:
            Tuple of (response_text, prompt_tokens, completion_tokens)
        """
        model = model or settings.openai_model
        provider = self._get_provider_for_model(model)

        logger.info(f"Using provider '{provider}' for model '{model}'")

        try:
            if provider == "anthropic":
                return self._chat_anthropic(prompt, model, system_prompt, max_tokens, temperature)
            elif provider == "google":
                return self._chat_google(prompt, model, system_prompt, max_tokens, temperature)
            else:
                return self._chat_openai(prompt, model, system_prompt, max_tokens, temperature)
        except Exception as e:
            logger.error(f"LLM call failed for {provider}/{model}: {str(e)}")
            raise

    def _chat_openai(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
    ) -> Tuple[str, int, int]:
        """Chat using OpenAI API."""
        if not self.openai_client:
            raise ValueError("OpenAI API key not configured")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.openai_client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        response_text = response.choices[0].message.content
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens

        logger.info(f"OpenAI call successful: model={model}, tokens={prompt_tokens}+{completion_tokens}")
        return response_text, prompt_tokens, completion_tokens

    def _chat_anthropic(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
    ) -> Tuple[str, int, int]:
        """Chat using Anthropic API."""
        if not self.anthropic_client:
            raise ValueError("Anthropic API key not configured")

        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        # Anthropic doesn't support temperature for all models
        if temperature != 0.7:
            kwargs["temperature"] = temperature

        response = self.anthropic_client.messages.create(**kwargs)

        response_text = response.content[0].text
        prompt_tokens = response.usage.input_tokens
        completion_tokens = response.usage.output_tokens

        logger.info(f"Anthropic call successful: model={model}, tokens={prompt_tokens}+{completion_tokens}")
        return response_text, prompt_tokens, completion_tokens

    def _chat_google(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
    ) -> Tuple[str, int, int]:
        """Chat using Google AI API."""
        if not self.google_configured:
            raise ValueError("Google API key not configured")

        # Create the model
        generation_config = {
            "max_output_tokens": max_tokens,
            "temperature": temperature,
        }

        gemini_model = genai.GenerativeModel(
            model_name=model,
            generation_config=generation_config,
            system_instruction=system_prompt if system_prompt else None,
        )

        response = gemini_model.generate_content(prompt)

        response_text = response.text

        # Google doesn't always return token counts, estimate if not available
        prompt_tokens = getattr(response.usage_metadata, 'prompt_token_count', len(prompt.split()) * 2)
        completion_tokens = getattr(response.usage_metadata, 'candidates_token_count', len(response_text.split()) * 2)

        logger.info(f"Google call successful: model={model}, tokens={prompt_tokens}+{completion_tokens}")
        return response_text, prompt_tokens, completion_tokens


# Singleton instance
_llm_provider: Optional[MultiLLMProvider] = None


def get_llm_provider() -> MultiLLMProvider:
    """Get or create the LLM provider instance."""
    global _llm_provider
    if _llm_provider is None:
        _llm_provider = MultiLLMProvider()
    return _llm_provider


def get_available_models() -> list[str]:
    """Get list of available models based on configured API keys."""
    models = []

    # OpenAI models
    if settings.openai_api_key:
        models.extend([
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
        ])

    # Anthropic models (current as of 2026)
    if settings.anthropic_api_key:
        models.extend([
            "claude-sonnet-4-5-20250929",
            "claude-opus-4-1-20250805",
            "claude-haiku-3-5-20241022",
        ])

    # Google models (Gemini 2.0+)
    if settings.google_api_key:
        models.extend([
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-2.5-flash-lite",
        ])

    return models if models else ["gpt-4o-mini"]  # Fallback
