"""
Parser de treinos para extrair rotinas estruturadas de texto ou JSON.

Este módulo converte sugestões de treino da IA ou links externos em
formato compatível com a API do Hevy.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class SetConfig:
    """Configuração de uma série."""
    
    type: str = "normal"  # normal, warmup, dropset, failure
    weight_kg: Optional[float] = None
    reps: Optional[int] = None
    rep_range_start: Optional[int] = None
    rep_range_end: Optional[int] = None
    rest_seconds: Optional[int] = None
    distance_meters: Optional[float] = None
    duration_seconds: Optional[int] = None
    
    def to_api_format(self) -> Dict[str, Any]:
        """Converte para formato da API do Hevy."""
        data = {
            "type": self.type,
            "weight_kg": self.weight_kg,
            "reps": self.reps,
            "distance_meters": self.distance_meters,
            "duration_seconds": self.duration_seconds,
            "custom_metric": None,
        }
        
        if self.rep_range_start and self.rep_range_end:
            data["rep_range"] = {
                "start": self.rep_range_start,
                "end": self.rep_range_end
            }
        elif self.reps:
            # Gera range padrão
            data["rep_range"] = {
                "start": max(1, self.reps - 2),
                "end": self.reps + 2
            }
        
        return data


@dataclass
class ExerciseConfig:
    """Configuração de um exercício na rotina."""
    
    name: str
    exercise_template_id: Optional[str] = None
    sets: List[SetConfig] = field(default_factory=list)
    rest_seconds: int = 60
    notes: Optional[str] = None
    superset_id: Optional[int] = None
    
    def to_api_format(self) -> Dict[str, Any]:
        """Converte para formato da API do Hevy."""
        return {
            "exercise_template_id": self.exercise_template_id,
            "superset_id": self.superset_id,
            "rest_seconds": self.rest_seconds,
            "notes": self.notes,
            "sets": [s.to_api_format() for s in self.sets],
        }


@dataclass
class RoutineConfig:
    """Configuração de uma rotina de treino."""
    
    title: str
    exercises: List[ExerciseConfig] = field(default_factory=list)
    folder_id: Optional[str] = None
    notes: Optional[str] = None
    
    def to_api_format(self) -> Dict[str, Any]:
        """Converte para formato da API do Hevy."""
        return {
            "title": self.title,
            "folder_id": self.folder_id,
            "notes": self.notes,
            "exercises": [e.to_api_format() for e in self.exercises],
        }


class WorkoutParser:
    """
    Parser para extrair rotinas de treino de diferentes formatos.
    
    Suporta:
    - JSON estruturado
    - Texto formatado (markdown, lista)
    - Links de treino (hevy.com)
    """
    
    # Padrões de texto comuns
    EXERCISE_PATTERN = re.compile(
        r"(?:^|\n)\s*[-*•]?\s*"  # Início de linha ou bullet
        r"(?:\d+\.\s*)?"  # Número opcional
        r"([A-Za-zÀ-ÿ\s\(\)]+?)"  # Nome do exercício
        r"\s*[-:–]\s*"  # Separador
        r"(\d+)\s*(?:x|×|X)\s*"  # Séries
        r"(\d+)(?:\s*-\s*(\d+))?"  # Reps (ou range)
        r"(?:\s*(?:@|com)\s*(\d+(?:[.,]\d+)?)\s*(?:kg|Kg|KG))?"  # Peso opcional
        r"(?:\s*[-,]\s*(\d+)\s*(?:s|seg|segundos?)?\s*(?:descanso|rest))?"  # Descanso opcional
        , re.IGNORECASE | re.MULTILINE
    )
    
    # Padrão simplificado: "Exercício: 3x10"
    SIMPLE_PATTERN = re.compile(
        r"(?:^|\n)\s*[-*•]?\s*"
        r"(?:\d+\.\s*)?"
        r"([A-Za-zÀ-ÿ\s\(\)]+?)"
        r"\s*[-:–]\s*"
        r"(\d+)\s*(?:x|×|X)\s*"
        r"(\d+)"
        , re.IGNORECASE | re.MULTILINE
    )
    
    # Padrão para título do treino
    TITLE_PATTERN = re.compile(
        r"(?:^|\n)\s*(?:#+\s*|Treino\s*[-:]\s*|Rotina\s*[-:]\s*)"
        r"([A-Za-zÀ-ÿ0-9\s\-–]+)"
        , re.IGNORECASE | re.MULTILINE
    )
    
    def __init__(self, exercise_templates: Optional[Dict[str, Dict[str, Any]]] = None):
        """
        Inicializa o parser.
        
        Args:
            exercise_templates: Dicionário de templates de exercícios do Hevy
                               (chave: id, valor: dados do template).
        """
        self.exercise_templates = exercise_templates or {}
        # Índice reverso: nome -> id
        self._name_to_id: Dict[str, str] = {}
        self._build_name_index()
    
    def _build_name_index(self) -> None:
        """Constrói índice de nomes para busca rápida."""
        for template_id, template in self.exercise_templates.items():
            name = template.get("title", "").lower().strip()
            if name:
                self._name_to_id[name] = template_id
    
    def find_exercise_id(self, name: str) -> Optional[str]:
        """
        Encontra o ID do template de exercício pelo nome.
        
        Args:
            name: Nome do exercício.
        
        Returns:
            ID do template ou None se não encontrado.
        """
        name_lower = name.lower().strip()
        
        # Busca exata
        if name_lower in self._name_to_id:
            return self._name_to_id[name_lower]
        
        # Busca parcial
        for template_name, template_id in self._name_to_id.items():
            if name_lower in template_name or template_name in name_lower:
                return template_id
        
        # Busca por palavras-chave
        name_words = set(name_lower.split())
        best_match = None
        best_score = 0
        
        for template_name, template_id in self._name_to_id.items():
            template_words = set(template_name.split())
            common = name_words & template_words
            score = len(common)
            if score > best_score:
                best_score = score
                best_match = template_id
        
        return best_match if best_score >= 1 else None
    
    def parse_json(self, json_str: str) -> Optional[RoutineConfig]:
        """
        Parseia JSON estruturado de treino.
        
        Formatos aceitos:
        {
            "title": "Treino A",
            "exercises": [
                {
                    "name": "Supino Reto",
                    "sets": 3,
                    "reps": 10,
                    "rest_seconds": 90
                }
            ]
        }
        """
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            return None
        
        if not isinstance(data, dict):
            return None
        
        title = data.get("title", "Treino Importado")
        notes = data.get("notes")
        folder_id = data.get("folder_id")
        
        exercises = []
        for ex_data in data.get("exercises", []):
            name = ex_data.get("name", "")
            template_id = ex_data.get("exercise_template_id") or self.find_exercise_id(name)
            
            # Constrói sets
            sets_data = ex_data.get("sets", [])
            if isinstance(sets_data, int):
                # Formato simplificado: sets=3, reps=10
                num_sets = sets_data
                reps = ex_data.get("reps", 10)
                rep_range = ex_data.get("rep_range", {})
                weight = ex_data.get("weight_kg")
                
                sets = [
                    SetConfig(
                        reps=reps,
                        weight_kg=weight,
                        rep_range_start=rep_range.get("start"),
                        rep_range_end=rep_range.get("end"),
                    )
                    for _ in range(num_sets)
                ]
            else:
                # Formato detalhado: lista de sets
                sets = []
                for s in sets_data:
                    sets.append(SetConfig(
                        type=s.get("type", "normal"),
                        weight_kg=s.get("weight_kg"),
                        reps=s.get("reps"),
                        rep_range_start=s.get("rep_range", {}).get("start"),
                        rep_range_end=s.get("rep_range", {}).get("end"),
                        rest_seconds=s.get("rest_seconds"),
                        distance_meters=s.get("distance_meters"),
                        duration_seconds=s.get("duration_seconds"),
                    ))
            
            exercises.append(ExerciseConfig(
                name=name,
                exercise_template_id=template_id,
                sets=sets,
                rest_seconds=ex_data.get("rest_seconds", 60),
                notes=ex_data.get("notes"),
                superset_id=ex_data.get("superset_id"),
            ))
        
        return RoutineConfig(
            title=title,
            exercises=exercises,
            folder_id=folder_id,
            notes=notes,
        )
    
    def parse_text(self, text: str) -> Optional[RoutineConfig]:
        """
        Parseia texto formatado de treino.
        
        Formatos aceitos:
        - "Supino Reto: 3x10"
        - "- Supino Reto - 3x10-12 @ 80kg - 90s descanso"
        - "1. Supino Reto: 3x10"
        """
        # Tenta extrair título
        title_match = self.TITLE_PATTERN.search(text)
        title = title_match.group(1).strip() if title_match else "Treino Importado"
        
        # Busca exercícios com padrão completo
        exercises = []
        matches = self.EXERCISE_PATTERN.findall(text)
        
        if not matches:
            # Tenta padrão simplificado
            matches = self.SIMPLE_PATTERN.findall(text)
            matches = [(m[0], m[1], m[2], None, None, None) for m in matches]
        
        for match in matches:
            name = match[0].strip()
            num_sets = int(match[1])
            reps_start = int(match[2])
            reps_end = int(match[3]) if match[3] is not None and match[3] != "" else None
            weight: Optional[float] = None
            if len(match) > 4 and match[4] is not None and match[4] != "":
                weight = float(str(match[4]).replace(",", "."))
            rest = int(match[5]) if len(match) > 5 and match[5] is not None and match[5] != "" else 60
            
            template_id = self.find_exercise_id(name)
            
            sets = [
                SetConfig(
                    reps=reps_start if not reps_end else None,
                    rep_range_start=reps_start if reps_end else None,
                    rep_range_end=reps_end,
                    weight_kg=weight,
                )
                for _ in range(num_sets)
            ]
            
            exercises.append(ExerciseConfig(
                name=name,
                exercise_template_id=template_id,
                sets=sets,
                rest_seconds=rest,
            ))
        
        if not exercises:
            return None
        
        return RoutineConfig(title=title, exercises=exercises)
    
    def parse(self, content: str) -> Optional[RoutineConfig]:
        """
        Parseia conteúdo automaticamente detectando o formato.
        
        Args:
            content: Texto ou JSON de treino.
        
        Returns:
            RoutineConfig ou None se não conseguir parsear.
        """
        content = content.strip()
        
        # Tenta JSON primeiro
        if content.startswith("{"):
            result = self.parse_json(content)
            if result:
                return result
        
        # Tenta extrair JSON de dentro do texto (markdown code block)
        json_match = re.search(r"```(?:json)?\s*(\{.+?\})\s*```", content, re.DOTALL)
        if json_match:
            result = self.parse_json(json_match.group(1))
            if result:
                return result
        
        # Parseia como texto
        return self.parse_text(content)
    
    def validate_routine(self, routine: RoutineConfig) -> Tuple[bool, List[str]]:
        """
        Valida uma rotina antes de criar na API.
        
        Returns:
            Tupla (válido, lista de erros/avisos).
        """
        errors = []
        
        if not routine.title:
            errors.append("Título da rotina é obrigatório")
        
        if not routine.exercises:
            errors.append("Rotina deve ter pelo menos um exercício")
        
        missing_ids = []
        for ex in routine.exercises:
            if not ex.exercise_template_id:
                missing_ids.append(ex.name)
            if not ex.sets:
                errors.append(f"Exercício '{ex.name}' não tem séries configuradas")
        
        if missing_ids:
            errors.append(
                f"Exercícios não encontrados no Hevy: {', '.join(missing_ids)}. "
                "Você pode criar exercícios customizados ou verificar os nomes."
            )
        
        return (len(errors) == 0, errors)


def format_routine_preview(routine: RoutineConfig) -> str:
    """
    Formata uma rotina para preview em texto.
    
    Args:
        routine: Configuração da rotina.
    
    Returns:
        Texto formatado para exibição.
    """
    lines = [f"**{routine.title}**"]
    
    if routine.notes:
        lines.append(f"_{routine.notes}_")
    
    lines.append("")
    
    for i, ex in enumerate(routine.exercises, 1):
        sets_info = f"{len(ex.sets)} séries"
        
        if ex.sets:
            first_set = ex.sets[0]
            if first_set.rep_range_start and first_set.rep_range_end:
                sets_info = f"{len(ex.sets)}x{first_set.rep_range_start}-{first_set.rep_range_end}"
            elif first_set.reps:
                sets_info = f"{len(ex.sets)}x{first_set.reps}"
        
        status = "✅" if ex.exercise_template_id else "⚠️"
        lines.append(f"{i}. {status} **{ex.name}** - {sets_info} ({ex.rest_seconds}s descanso)")
        
        if ex.notes:
            lines.append(f"   _{ex.notes}_")
    
    return "\n".join(lines)
