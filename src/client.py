from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

class HevyClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.hevyapp.com/v1",
        timeout_seconds: int = 30,
    ) -> None:
        self.api_key = api_key or os.getenv("HEVY_API_KEY")
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

        if not self.api_key:
            raise ValueError(
                "HEVY_API_KEY não encontrada. Defina no .env (recomendado) ou no ambiente."
            )

        self.headers = {"api-key": self.api_key, "Accept": "application/json"}
    
    def get_recent_workouts(self, page: int = 1, page_size: int = 10) -> List[Dict[str, Any]]:
        """
        Busca treinos no endpoint /workouts.

        Observação: a API retorna um envelope com a chave 'workouts'.
        """
        url = f"{self.base_url}/workouts"
        params = {"page": page, "pageSize": page_size}
        response = requests.get(
            url, headers=self.headers, params=params, timeout=self.timeout_seconds
        )
        response.raise_for_status()
        payload = response.json() or {}
        workouts = payload.get("workouts", [])
        return workouts if isinstance(workouts, list) else []
    
    def get_exercise_template(self, exercise_template_id: str) -> Dict[str, Any]:
        """
        Busca informações do template de exercício através do exercise_template_id.
        Retorna o primary_muscle_group e outras informações do exercício.
        """
        url = f"{self.base_url}/exercise_templates/{exercise_template_id}"
        response = requests.get(
            url, headers=self.headers, timeout=self.timeout_seconds
        )
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, dict) else {}

    def get_all_workouts(self, max_pages: int = 100) -> List[Dict[str, Any]]:
        """
        Busca todos os treinos disponíveis, paginando automaticamente.
        
        Args:
            max_pages: Número máximo de páginas a buscar (evita loops infinitos).
        
        Returns:
            Lista completa de treinos de todas as páginas.
        """
        all_workouts: List[Dict[str, Any]] = []
        page = 1
        page_size = 50  # Maior tamanho para reduzir número de requisições
        
        while page <= max_pages:
            workouts = self.get_recent_workouts(page=page, page_size=page_size)
            if not workouts:
                break
            all_workouts.extend(workouts)
            if len(workouts) < page_size:
                # Última página, não há mais treinos
                break
            page += 1
        
        return all_workouts

    def get_routines(self, page: int = 1, page_size: int = 10) -> List[Dict[str, Any]]:
        """
        Busca rotinas de treino salvas no endpoint /routines.
        
        Returns:
            Lista de rotinas de treino.
        """
        url = f"{self.base_url}/routines"
        params = {"page": page, "pageSize": page_size}
        response = requests.get(
            url, headers=self.headers, params=params, timeout=self.timeout_seconds
        )
        response.raise_for_status()
        payload = response.json() or {}
        routines = payload.get("routines", [])
        return routines if isinstance(routines, list) else []