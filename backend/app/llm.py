from typing import Optional, Tuple
import logging
import httpx

from openai import OpenAI
import anthropic
import google.generativeai as genai

from app.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Model to provider mapping
MODEL_PROVIDERS = {
    # OpenAI models (GPT-5.x series - Jan 2026)
    "gpt-5.2": "openai",
    "gpt-5.2-pro": "openai",
    "gpt-5-mini": "openai",
    "gpt-4o": "openai",
    "gpt-4o-mini": "openai",
    # Anthropic models (Jan 2026)
    "claude-opus-4-5-20251101": "anthropic",
    "claude-sonnet-4-5-20250929": "anthropic",
    "claude-haiku-3-5-20241022": "anthropic",
    # Google models (Jan 2026)
    "gemini-2.5-flash": "google",
    "gemini-2.5-pro": "google",
    "gemini-2.0-flash": "google",
    # Groq models (free tier)
    "llama-3.3-70b-versatile": "groq",
    "llama-3.1-8b-instant": "groq",
    "mixtral-8x7b-32768": "groq",
    "gemma2-9b-it": "groq",
    # OpenRouter models
    "openrouter/auto": "openrouter",
    "openrouter/mistralai/mistral-7b-instruct:free": "openrouter",
    "openrouter/google/gemma-2-9b-it:free": "openrouter",
    "openrouter/meta-llama/llama-3.2-3b-instruct:free": "openrouter",
    # Ollama models (local)
    "ollama/llama3.2": "ollama",
    "ollama/mistral": "ollama",
    "ollama/codellama": "ollama",
    "ollama/phi3": "ollama",
}


class MultiLLMProvider:
    """Wrapper for multiple LLM providers."""

    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        self.google_configured = False
        self.groq_client = None
        self.openrouter_client = None
        self.ollama_base_url = None
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

        # Groq (uses OpenAI-compatible API)
        if settings.groq_api_key:
            self.groq_client = OpenAI(
                api_key=settings.groq_api_key,
                base_url="https://api.groq.com/openai/v1"
            )
            logger.info("Groq client initialized")

        # OpenRouter (uses OpenAI-compatible API)
        if settings.openrouter_api_key:
            self.openrouter_client = OpenAI(
                api_key=settings.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1"
            )
            logger.info("OpenRouter client initialized")

        # Ollama (local, no API key needed)
        if settings.ollama_base_url:
            self.ollama_base_url = settings.ollama_base_url
            logger.info(f"Ollama configured at {self.ollama_base_url}")

    def _get_provider_for_model(self, model: str) -> str:
        """Determine which provider to use for a given model."""
        if model.startswith("ollama/"):
            return "ollama"
        if model.startswith("openrouter/"):
            return "openrouter"
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
            elif provider == "groq":
                return self._chat_groq(prompt, model, system_prompt, max_tokens, temperature)
            elif provider == "openrouter":
                return self._chat_openrouter(prompt, model, system_prompt, max_tokens, temperature)
            elif provider == "ollama":
                return self._chat_ollama(prompt, model, system_prompt, max_tokens, temperature)
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

        # GPT-5.x models use max_completion_tokens instead of max_tokens
        if model.startswith("gpt-5"):
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                max_completion_tokens=max_tokens,
                temperature=temperature,
            )
        else:
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

        prompt_tokens = getattr(response.usage_metadata, 'prompt_token_count', len(prompt.split()) * 2)
        completion_tokens = getattr(response.usage_metadata, 'candidates_token_count', len(response_text.split()) * 2)

        logger.info(f"Google call successful: model={model}, tokens={prompt_tokens}+{completion_tokens}")
        return response_text, prompt_tokens, completion_tokens

    def _chat_groq(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
    ) -> Tuple[str, int, int]:
        """Chat using Groq API (OpenAI-compatible)."""
        if not self.groq_client:
            raise ValueError("Groq API key not configured")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.groq_client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        response_text = response.choices[0].message.content
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens

        logger.info(f"Groq call successful: model={model}, tokens={prompt_tokens}+{completion_tokens}")
        return response_text, prompt_tokens, completion_tokens

    def _chat_openrouter(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
    ) -> Tuple[str, int, int]:
        """Chat using OpenRouter API (OpenAI-compatible)."""
        if not self.openrouter_client:
            raise ValueError("OpenRouter API key not configured")

        # Remove 'openrouter/' prefix for the actual API call
        actual_model = model.replace("openrouter/", "")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.openrouter_client.chat.completions.create(
            model=actual_model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        response_text = response.choices[0].message.content
        prompt_tokens = response.usage.prompt_tokens if response.usage else len(prompt.split()) * 2
        completion_tokens = response.usage.completion_tokens if response.usage else len(response_text.split()) * 2

        logger.info(f"OpenRouter call successful: model={model}, tokens={prompt_tokens}+{completion_tokens}")
        return response_text, prompt_tokens, completion_tokens

    def _chat_ollama(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
    ) -> Tuple[str, int, int]:
        """Chat using Ollama API (local)."""
        if not self.ollama_base_url:
            raise ValueError("Ollama base URL not configured")

        # Remove 'ollama/' prefix for the actual API call
        actual_model = model.replace("ollama/", "")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Ollama uses OpenAI-compatible chat API
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                f"{self.ollama_base_url}/api/chat",
                json={
                    "model": actual_model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": temperature,
                    }
                }
            )
            response.raise_for_status()
            data = response.json()

        response_text = data["message"]["content"]
        # Ollama provides token counts in some versions
        prompt_tokens = data.get("prompt_eval_count", len(prompt.split()) * 2)
        completion_tokens = data.get("eval_count", len(response_text.split()) * 2)

        logger.info(f"Ollama call successful: model={model}, tokens={prompt_tokens}+{completion_tokens}")
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

    # OpenAI models (GPT-5.x series - Jan 2026)
    if settings.openai_api_key:
        models.extend([
            "gpt-5.2",
            "gpt-5.2-pro",
            "gpt-5-mini",
            "gpt-4o",
            "gpt-4o-mini",
        ])

    # Anthropic models (Jan 2026)
    if settings.anthropic_api_key:
        models.extend([
            "claude-opus-4-5-20251101",
            "claude-sonnet-4-5-20250929",
            "claude-haiku-3-5-20241022",
        ])

    # Google models (Jan 2026)
    if settings.google_api_key:
        models.extend([
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-2.0-flash",
        ])

    # Groq models (free tier)
    if settings.groq_api_key:
        models.extend([
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
        ])

    # OpenRouter models (includes free tier)
    if settings.openrouter_api_key:
        models.extend([
            "openrouter/auto",
            "openrouter/mistralai/mistral-7b-instruct:free",
            "openrouter/google/gemma-2-9b-it:free",
            "openrouter/meta-llama/llama-3.2-3b-instruct:free",
        ])

    # Ollama models (local)
    if settings.ollama_base_url:
        models.extend([
            "ollama/llama3.2",
            "ollama/mistral",
            "ollama/codellama",
            "ollama/phi3",
        ])

    return models if models else ["gpt-4o-mini"]  # Fallback
