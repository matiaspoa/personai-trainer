from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Optional, Protocol

import requests


@dataclass(frozen=True)
class LlmConfig:
    """
    Configuração mínima para chamar um modelo de linguagem.

    Pensada para ser simples de entender e fácil de trocar de provedor.
    Provedores suportados:
    - openai  (compatível com /chat/completions)
      - LLM_PROVIDER=openai
      - LLM_API_KEY=...
      - LLM_MODEL=gpt-4.1-mini (ou similar)
      - LLM_BASE_URL=https://api.openai.com/v1

    - gemini (Google Gemini API via generateContent)
      - LLM_PROVIDER=gemini
      - LLM_API_KEY=...  (sua GEMINI_API_KEY)
      - LLM_MODEL=gemini-2.5-flash (ou similar)
      - LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta
    """

    provider: str
    api_key: str
    model: str
    base_url: str

    @classmethod
    def from_env(cls) -> "LlmConfig":
        provider = os.getenv("LLM_PROVIDER", "openai").strip()
        api_key = os.getenv("LLM_API_KEY", "").strip()
        model = os.getenv("LLM_MODEL", "").strip()
        default_base_url = (
            "https://generativelanguage.googleapis.com/v1beta"
            if provider.lower() == "gemini"
            else "https://api.openai.com/v1"
        )
        base_url = os.getenv("LLM_BASE_URL", default_base_url).rstrip("/")

        missing = [name for name, value in [("LLM_API_KEY", api_key), ("LLM_MODEL", model)] if not value]
        if missing:
            missing_str = ", ".join(missing)
            raise ValueError(
                f"Variáveis de ambiente de LLM ausentes: {missing_str}. "
                "Defina-as no .env para habilitar geração automática de texto."
            )

        return cls(provider=provider, api_key=api_key, model=model, base_url=base_url)


class LlmClient(Protocol):
    """Contrato mínimo para um cliente de LLM."""

    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:  # pragma: no cover - interface
        ...


class OpenAiLikeClient:
    """
    Cliente HTTP para LLMs via REST.

    Suporta:
    - openai (chat/completions)
    - gemini (models:generateContent)

    NÃO expõe a chave de API em mensagens de erro.
    """

    def __init__(self, config: LlmConfig) -> None:
        self._config = config

    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        provider = self._config.provider.lower()

        if provider == "gemini":
            return self._generate_text_gemini(prompt=prompt, system_prompt=system_prompt)
        if provider == "openai":
            return self._generate_text_openai(prompt=prompt, system_prompt=system_prompt)

        raise NotImplementedError(
            f"Provider '{self._config.provider}' ainda não suportado. "
            "Use LLM_PROVIDER=openai|gemini ou adapte esta classe."
        )

    def _generate_text_openai(self, prompt: str, system_prompt: Optional[str]) -> str:
        url = f"{self._config.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._config.api_key}",
            "Content-Type": "application/json",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self._config.model,
            "messages": messages,
            "temperature": 0.4,
        }

        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise RuntimeError(f"Erro HTTP ao chamar o modelo de linguagem: {exc}") from exc
        except requests.RequestException as exc:
            raise RuntimeError(f"Erro de rede ao chamar o modelo de linguagem: {exc}") from exc

        data = response.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:  # pragma: no cover - defende contra respostas estranhas
            raise RuntimeError("Resposta inesperada do modelo de linguagem.") from exc

    def _generate_text_gemini(self, prompt: str, system_prompt: Optional[str]) -> str:
        """
        Implementação Gemini API (Google AI for Developers).

        Endpoint:
        POST {base_url}/models/{model}:generateContent
        Header: x-goog-api-key
        """
        url = f"{self._config.base_url}/models/{self._config.model}:generateContent"
        headers = {
            "x-goog-api-key": self._config.api_key,
            "Content-Type": "application/json",
        }

        payload: dict = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.4},
        }
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise RuntimeError(f"Erro HTTP ao chamar o Gemini: {exc}") from exc
        except requests.RequestException as exc:
            raise RuntimeError(f"Erro de rede ao chamar o Gemini: {exc}") from exc

        data = response.json()
        try:
            # candidates[0].content.parts[0].text
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:  # pragma: no cover
            raise RuntimeError("Resposta inesperada do Gemini.") from exc

