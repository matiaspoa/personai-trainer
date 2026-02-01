"""
Router de modelos LLM com fallback automático.

Este módulo implementa um sistema de roteamento inteligente entre diferentes
provedores de LLM (Gemini, Groq, OpenAI) usando litellm. Quando um provedor
atinge rate limit, automaticamente tenta o próximo disponível.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass
class ModelConfig:
    """Configuração de um modelo LLM."""
    
    name: str  # Nome do modelo no formato litellm (ex: "gemini/gemma-3-4b-it")
    api_key_env: str  # Nome da variável de ambiente com a chave
    priority: int = 0  # Menor = maior prioridade
    max_tokens: int = 1024
    temperature: float = 0.4
    
    @property
    def api_key(self) -> Optional[str]:
        """Obtém a chave da API do ambiente."""
        return os.getenv(self.api_key_env)
    
    @property
    def is_available(self) -> bool:
        """Verifica se o modelo está configurado (tem chave)."""
        return bool(self.api_key)


# Configurações padrão de modelos (ordenados por prioridade)
DEFAULT_MODELS: List[ModelConfig] = [
    # Gemma 3 4B - melhor custo-benefício no tier gratuito Google
    ModelConfig(
        name="gemini/gemma-3-4b-it",
        api_key_env="GEMINI_API_KEY",
        priority=1,
    ),
    # Gemini 2.0 Flash Lite - fallback Google
    ModelConfig(
        name="gemini/gemini-2.0-flash-lite",
        api_key_env="GEMINI_API_KEY",
        priority=2,
    ),
    # Groq Llama 3.1 8B - muito rápido, tier gratuito generoso
    ModelConfig(
        name="groq/llama-3.1-8b-instant",
        api_key_env="GROQ_API_KEY",
        priority=3,
    ),
    # Groq Llama 3.3 70B - mais capaz, mais lento
    ModelConfig(
        name="groq/llama-3.3-70b-versatile",
        api_key_env="GROQ_API_KEY",
        priority=4,
    ),
    # OpenAI GPT-4o mini - fallback pago
    ModelConfig(
        name="gpt-4o-mini",
        api_key_env="OPENAI_API_KEY",
        priority=5,
    ),
]


@dataclass
class ModelRouter:
    """
    Router inteligente para LLMs com fallback automático.
    
    Usa litellm para interface unificada e tenta múltiplos provedores
    em sequência quando ocorrem erros de rate limit.
    
    Exemplo de uso:
        router = ModelRouter()
        response = router.generate("Olá, como vai?", system_prompt="Seja breve.")
    """
    
    models: List[ModelConfig] = field(default_factory=lambda: DEFAULT_MODELS.copy())
    _last_successful_model: Optional[str] = field(default=None, init=False)
    
    def __post_init__(self) -> None:
        """Configura as variáveis de ambiente para litellm."""
        # Mapeia as chaves para o formato esperado pelo litellm
        gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("LLM_API_KEY")
        if gemini_key:
            os.environ["GEMINI_API_KEY"] = gemini_key
        
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            os.environ["GROQ_API_KEY"] = groq_key
        
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            os.environ["OPENAI_API_KEY"] = openai_key
        
        # Ordena modelos por prioridade
        self.models.sort(key=lambda m: m.priority)
    
    def get_available_models(self) -> List[ModelConfig]:
        """Retorna lista de modelos disponíveis (com chave configurada)."""
        return [m for m in self.models if m.is_available]
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Gera texto usando o primeiro modelo disponível.
        
        Faz fallback automático para o próximo modelo se ocorrer erro.
        
        Args:
            prompt: Texto do usuário.
            system_prompt: Instruções de sistema (opcional).
            max_tokens: Limite de tokens na resposta.
            temperature: Criatividade (0-1).
        
        Returns:
            Texto gerado pelo modelo.
        
        Raises:
            RuntimeError: Se todos os modelos falharem.
        """
        import litellm
        
        # Desabilita logs verbosos do litellm
        litellm.set_verbose = False
        
        available = self.get_available_models()
        if not available:
            raise RuntimeError(
                "Nenhum modelo LLM configurado. Configure pelo menos uma das chaves: "
                "GEMINI_API_KEY, GROQ_API_KEY ou OPENAI_API_KEY no arquivo .env"
            )
        
        # Se já temos um modelo que funcionou, tenta ele primeiro
        if self._last_successful_model:
            available = sorted(
                available,
                key=lambda m: (m.name != self._last_successful_model, m.priority)
            )
        
        errors = []
        
        for model_config in available:
            try:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                
                response = litellm.completion(
                    model=model_config.name,
                    messages=messages,
                    max_tokens=max_tokens or model_config.max_tokens,
                    temperature=temperature or model_config.temperature,
                )
                
                # Sucesso! Memoriza o modelo
                self._last_successful_model = model_config.name
                
                return response.choices[0].message.content
                
            except litellm.RateLimitError as e:
                errors.append(f"{model_config.name}: Rate limit - {e}")
                continue
            except litellm.APIConnectionError as e:
                errors.append(f"{model_config.name}: Conexão - {e}")
                continue
            except litellm.APIError as e:
                errors.append(f"{model_config.name}: API Error - {e}")
                continue
            except Exception as e:
                errors.append(f"{model_config.name}: {type(e).__name__} - {e}")
                continue
        
        # Todos falharam
        error_details = "\n".join(errors)
        raise RuntimeError(
            f"Todos os modelos falharam:\n{error_details}"
        )
    
    def generate_with_fallback(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Gera texto e retorna informações adicionais sobre qual modelo foi usado.
        
        Returns:
            Dict com 'text', 'model' e 'success'.
        """
        try:
            text = self.generate(prompt, system_prompt, **kwargs)
            return {
                "text": text,
                "model": self._last_successful_model,
                "success": True,
            }
        except RuntimeError as e:
            return {
                "text": str(e),
                "model": None,
                "success": False,
            }


class LiteLLMClient:
    """
    Cliente compatível com a interface LlmClient existente.
    
    Drop-in replacement para OpenAiLikeClient com fallback automático.
    """
    
    def __init__(self, router: Optional[ModelRouter] = None) -> None:
        self._router = router or ModelRouter()
    
    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Gera texto usando o router com fallback."""
        return self._router.generate(prompt, system_prompt)
    
    @property
    def available_models(self) -> List[str]:
        """Lista modelos disponíveis."""
        return [m.name for m in self._router.get_available_models()]
    
    @property
    def last_model_used(self) -> Optional[str]:
        """Retorna o último modelo que funcionou."""
        return self._router._last_successful_model
