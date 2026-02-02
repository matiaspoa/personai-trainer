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

    def get_all_exercise_templates(self, max_pages: int = 100) -> Dict[str, Dict[str, Any]]:
        """
        Busca todos os templates de exercícios e retorna um dicionário indexado por ID.
        
        Isso é muito mais eficiente do que buscar um template por vez, pois a API
        retorna até 10 templates por página.
        
        Returns:
            Dicionário com exercise_template_id como chave e o template como valor.
        """
        templates_by_id: Dict[str, Dict[str, Any]] = {}
        page = 1
        page_size = 10  # Limite da API Hevy
        
        while page <= max_pages:
            url = f"{self.base_url}/exercise_templates"
            params = {"page": page, "pageSize": page_size}
            response = requests.get(
                url, headers=self.headers, params=params, timeout=self.timeout_seconds
            )
            response.raise_for_status()
            payload = response.json() or {}
            templates = payload.get("exercise_templates", [])
            
            if not templates:
                break
            
            for template in templates:
                template_id = template.get("id")
                if template_id:
                    templates_by_id[template_id] = template
            
            if len(templates) < page_size:
                # Última página
                break
            page += 1
        
        return templates_by_id

    def get_workouts_count(self) -> int:
        """
        Retorna o número total de treinos na conta.
        """
        url = f"{self.base_url}/workouts/count"
        response = requests.get(
            url, headers=self.headers, timeout=self.timeout_seconds
        )
        response.raise_for_status()
        payload = response.json() or {}
        return payload.get("workout_count", 0)

    # ==================== MÉTODOS POST (Criação) ====================

    def get_routine_folders(self, page: int = 1, page_size: int = 10) -> List[Dict[str, Any]]:
        """
        Busca pastas de rotinas no endpoint /routine_folders.
        
        Returns:
            Lista de pastas de rotinas.
        """
        url = f"{self.base_url}/routine_folders"
        params = {"page": page, "pageSize": page_size}
        response = requests.get(
            url, headers=self.headers, params=params, timeout=self.timeout_seconds
        )
        response.raise_for_status()
        payload = response.json() or {}
        folders = payload.get("routine_folders", [])
        return folders if isinstance(folders, list) else []

    def get_all_routine_folders(self, max_pages: int = 10) -> List[Dict[str, Any]]:
        """
        Busca todas as pastas de rotinas disponíveis.
        
        Returns:
            Lista completa de pastas de rotinas.
        """
        all_folders: List[Dict[str, Any]] = []
        page = 1
        page_size = 10
        
        while page <= max_pages:
            folders = self.get_routine_folders(page=page, page_size=page_size)
            if not folders:
                break
            all_folders.extend(folders)
            if len(folders) < page_size:
                break
            page += 1
        
        return all_folders

    def create_routine_folder(self, title: str) -> Dict[str, Any]:
        """
        Cria uma nova pasta de rotinas.
        
        Args:
            title: Nome da pasta.
        
        Returns:
            Dados da pasta criada (incluindo ID).
        """
        url = f"{self.base_url}/routine_folders"
        headers = {**self.headers, "Content-Type": "application/json"}
        payload = {"routine_folder": {"title": title}}
        
        response = requests.post(
            url, headers=headers, json=payload, timeout=self.timeout_seconds
        )
        response.raise_for_status()
        return response.json()

    def create_routine(
        self,
        title: str,
        exercises: List[Dict[str, Any]],
        folder_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Cria uma nova rotina de treino.
        
        Args:
            title: Nome da rotina (ex: "Treino A - Peito e Tríceps").
            exercises: Lista de exercícios no formato:
                [
                    {
                        "exercise_template_id": "ABC123",  # ID do exercício no Hevy
                        "rest_seconds": 90,  # Descanso entre séries
                        "notes": "Manter forma",  # Notas opcionais
                        "superset_id": None,  # ID do superset (opcional)
                        "sets": [
                            {
                                "type": "normal",  # ou "warmup", "dropset", "failure"
                                "weight_kg": 80,
                                "reps": 10,
                                "rep_range": {"start": 8, "end": 12}  # Faixa de reps
                            }
                        ]
                    }
                ]
            folder_id: ID da pasta onde salvar (opcional).
            notes: Notas gerais da rotina.
        
        Returns:
            Dados da rotina criada (incluindo ID).
        """
        url = f"{self.base_url}/routines"
        headers = {**self.headers, "Content-Type": "application/json"}
        
        # Formata os exercícios para o formato da API
        formatted_exercises = []
        for ex in exercises:
            formatted_sets = []
            for s in ex.get("sets", []):
                set_data = {
                    "type": s.get("type", "normal"),
                    "weight_kg": s.get("weight_kg"),
                    "reps": s.get("reps"),
                    "distance_meters": s.get("distance_meters"),
                    "duration_seconds": s.get("duration_seconds"),
                    "custom_metric": s.get("custom_metric"),
                }
                # Adiciona rep_range se especificado
                if "rep_range" in s:
                    set_data["rep_range"] = s["rep_range"]
                elif s.get("reps"):
                    # Cria range padrão baseado nas reps
                    reps = s["reps"]
                    set_data["rep_range"] = {"start": max(1, reps - 2), "end": reps + 2}
                
                formatted_sets.append(set_data)
            
            formatted_exercises.append({
                "exercise_template_id": ex["exercise_template_id"],
                "superset_id": ex.get("superset_id"),
                "rest_seconds": ex.get("rest_seconds", 60),
                "notes": ex.get("notes"),
                "sets": formatted_sets,
            })
        
        payload = {
            "routine": {
                "title": title,
                "folder_id": folder_id,
                "notes": notes,
                "exercises": formatted_exercises,
            }
        }
        
        response = requests.post(
            url, headers=headers, json=payload, timeout=self.timeout_seconds
        )
        response.raise_for_status()
        return response.json()

    def search_exercise_template(
        self, 
        name: str, 
        templates: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Busca um template de exercício pelo nome (busca parcial case-insensitive).
        
        Args:
            name: Nome do exercício a buscar.
            templates: Dicionário de templates pré-carregado (opcional).
        
        Returns:
            Template encontrado ou None.
        """
        if templates is None:
            templates = self.get_all_exercise_templates()
        
        name_lower = name.lower().strip()
        
        # Busca exata primeiro
        for template_id, template in templates.items():
            template_name = template.get("title", "").lower()
            if template_name == name_lower:
                return template
        
        # Busca parcial
        for template_id, template in templates.items():
            template_name = template.get("title", "").lower()
            if name_lower in template_name or template_name in name_lower:
                return template
        
        return None

    def get_routine(self, routine_id: str) -> Dict[str, Any]:
        """
        Busca uma rotina pelo ID.
        
        Args:
            routine_id: ID da rotina.
        
        Returns:
            Dados da rotina.
        """
        url = f"{self.base_url}/routines/{routine_id}"
        response = requests.get(
            url, headers=self.headers, timeout=self.timeout_seconds
        )
        response.raise_for_status()
        return response.json()

    def update_routine(
        self,
        routine_id: str,
        title: Optional[str] = None,
        exercises: Optional[List[Dict[str, Any]]] = None,
        folder_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Atualiza uma rotina existente.
        
        Args:
            routine_id: ID da rotina a atualizar.
            title: Novo nome (opcional).
            exercises: Nova lista de exercícios (opcional).
            folder_id: Nova pasta (opcional).
            notes: Novas notas (opcional).
        
        Returns:
            Dados da rotina atualizada.
        """
        url = f"{self.base_url}/routines/{routine_id}"
        headers = {**self.headers, "Content-Type": "application/json"}
        
        # Busca rotina atual para mesclar dados
        current = self.get_routine(routine_id).get("routine", {})
        
        # Prepara payload com dados atualizados
        routine_data = {
            "title": title if title is not None else current.get("title"),
            "folder_id": folder_id if folder_id is not None else current.get("folder_id"),
            "notes": notes if notes is not None else current.get("notes"),
        }
        
        if exercises is not None:
            # Formata exercícios igual ao create_routine
            formatted_exercises = []
            for ex in exercises:
                formatted_sets = []
                for s in ex.get("sets", []):
                    set_data = {
                        "type": s.get("type", "normal"),
                        "weight_kg": s.get("weight_kg"),
                        "reps": s.get("reps"),
                        "distance_meters": s.get("distance_meters"),
                        "duration_seconds": s.get("duration_seconds"),
                        "custom_metric": s.get("custom_metric"),
                    }
                    if "rep_range" in s:
                        set_data["rep_range"] = s["rep_range"]
                    elif s.get("reps"):
                        reps = s["reps"]
                        set_data["rep_range"] = {"start": max(1, reps - 2), "end": reps + 2}
                    formatted_sets.append(set_data)
                
                formatted_exercises.append({
                    "exercise_template_id": ex["exercise_template_id"],
                    "superset_id": ex.get("superset_id"),
                    "rest_seconds": ex.get("rest_seconds", 60),
                    "notes": ex.get("notes"),
                    "sets": formatted_sets,
                })
            routine_data["exercises"] = formatted_exercises
        else:
            routine_data["exercises"] = current.get("exercises", [])
        
        payload = {"routine": routine_data}
        
        response = requests.put(
            url, headers=headers, json=payload, timeout=self.timeout_seconds
        )
        response.raise_for_status()
        return response.json()