"""
Modelo de perfil do usuário para contexto de recomendações.

Este módulo define o perfil físico do usuário, incluindo medidas corporais
e objetivos de treino, que são usados como contexto para o LLM gerar
recomendações personalizadas.
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class TrainingGoal(str, Enum):
    """Objetivos de treino suportados."""
    HYPERTROPHY = "hypertrophy"
    STRENGTH = "strength"
    ENDURANCE = "endurance"
    FAT_LOSS = "fat_loss"
    MAINTENANCE = "maintenance"
    GENERAL_FITNESS = "general_fitness"


class ExperienceLevel(str, Enum):
    """Nível de experiência do praticante."""
    BEGINNER = "beginner"  # < 1 ano
    INTERMEDIATE = "intermediate"  # 1-3 anos
    ADVANCED = "advanced"  # 3-5 anos
    ELITE = "elite"  # > 5 anos


@dataclass
class BodyMeasurements:
    """Medidas corporais do usuário em centímetros."""
    chest: Optional[float] = None  # Peitoral
    waist: Optional[float] = None  # Cintura
    hips: Optional[float] = None  # Quadril
    biceps_left: Optional[float] = None  # Bíceps esquerdo
    biceps_right: Optional[float] = None  # Bíceps direito
    thigh_left: Optional[float] = None  # Coxa esquerda
    thigh_right: Optional[float] = None  # Coxa direita
    calf_left: Optional[float] = None  # Panturrilha esquerda
    calf_right: Optional[float] = None  # Panturrilha direita
    forearm_left: Optional[float] = None  # Antebraço esquerdo
    forearm_right: Optional[float] = None  # Antebraço direito
    neck: Optional[float] = None  # Pescoço
    shoulders: Optional[float] = None  # Ombros
    measurement_date: Optional[str] = None  # Data da medição (ISO format)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário, omitindo valores None."""
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    def get_summary(self) -> str:
        """Retorna um resumo das medidas em texto."""
        parts = []
        if self.chest:
            parts.append(f"Peitoral: {self.chest}cm")
        if self.waist:
            parts.append(f"Cintura: {self.waist}cm")
        if self.hips:
            parts.append(f"Quadril: {self.hips}cm")
        if self.biceps_left or self.biceps_right:
            biceps = self.biceps_left or self.biceps_right
            parts.append(f"Bíceps: {biceps}cm")
        if self.thigh_left or self.thigh_right:
            thigh = self.thigh_left or self.thigh_right
            parts.append(f"Coxa: {thigh}cm")
        if self.shoulders:
            parts.append(f"Ombros: {self.shoulders}cm")
        return ", ".join(parts) if parts else "Sem medidas registradas"


@dataclass
class UserProfile:
    """
    Perfil completo do usuário para personalização de recomendações.
    
    Attributes:
        name: Nome do usuário.
        weight_kg: Peso em quilogramas.
        height_cm: Altura em centímetros.
        age: Idade em anos.
        gender: Gênero (male/female/other).
        body_fat_percentage: Percentual de gordura corporal.
        experience_level: Nível de experiência em musculação.
        training_goals: Lista de objetivos de treino.
        injuries: Lista de lesões ou limitações.
        measurements: Medidas corporais detalhadas.
        notes: Observações adicionais.
    """
    name: str = "Usuário"
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    body_fat_percentage: Optional[float] = None
    experience_level: ExperienceLevel = ExperienceLevel.INTERMEDIATE
    training_goals: List[TrainingGoal] = field(default_factory=lambda: [TrainingGoal.HYPERTROPHY])
    injuries: List[str] = field(default_factory=list)
    measurements: BodyMeasurements = field(default_factory=BodyMeasurements)
    notes: str = ""
    
    @property
    def bmi(self) -> Optional[float]:
        """Calcula o IMC (Índice de Massa Corporal)."""
        if self.weight_kg and self.height_cm:
            height_m = self.height_cm / 100
            return round(self.weight_kg / (height_m ** 2), 1)
        return None
    
    @property
    def bmi_category(self) -> Optional[str]:
        """Retorna a categoria do IMC."""
        bmi = self.bmi
        if bmi is None:
            return None
        if bmi < 18.5:
            return "Abaixo do peso"
        elif bmi < 25:
            return "Peso normal"
        elif bmi < 30:
            return "Sobrepeso"
        else:
            return "Obesidade"
    
    def get_context_for_llm(self) -> str:
        """
        Gera um texto de contexto para ser usado no prompt do LLM.
        
        Returns:
            String formatada com informações relevantes do perfil.
        """
        lines = []
        lines.append("=== PERFIL DO USUÁRIO ===")
        lines.append(f"Nome: {self.name}")
        
        if self.weight_kg:
            lines.append(f"Peso: {self.weight_kg}kg")
        if self.height_cm:
            lines.append(f"Altura: {self.height_cm}cm")
        if self.bmi:
            lines.append(f"IMC: {self.bmi} ({self.bmi_category})")
        if self.age:
            lines.append(f"Idade: {self.age} anos")
        if self.gender:
            lines.append(f"Gênero: {self.gender}")
        if self.body_fat_percentage:
            lines.append(f"Gordura corporal: {self.body_fat_percentage}%")
        
        lines.append(f"Nível de experiência: {self.experience_level.value}")
        
        if self.training_goals:
            goals_str = ", ".join(g.value for g in self.training_goals)
            lines.append(f"Objetivos: {goals_str}")
        
        if self.injuries:
            lines.append(f"Lesões/Limitações: {', '.join(self.injuries)}")
        
        measurements_summary = self.measurements.get_summary()
        if measurements_summary != "Sem medidas registradas":
            lines.append(f"Medidas: {measurements_summary}")
        
        if self.notes:
            lines.append(f"Observações: {self.notes}")
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte o perfil para dicionário serializável."""
        return {
            "name": self.name,
            "weight_kg": self.weight_kg,
            "height_cm": self.height_cm,
            "age": self.age,
            "gender": self.gender,
            "body_fat_percentage": self.body_fat_percentage,
            "experience_level": self.experience_level.value,
            "training_goals": [g.value for g in self.training_goals],
            "injuries": self.injuries,
            "measurements": self.measurements.to_dict(),
            "notes": self.notes,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserProfile":
        """Cria um perfil a partir de um dicionário."""
        measurements_data = data.get("measurements", {})
        measurements = BodyMeasurements(**measurements_data) if measurements_data else BodyMeasurements()
        
        experience = data.get("experience_level", "intermediate")
        if isinstance(experience, str):
            experience = ExperienceLevel(experience)
        
        goals_data = data.get("training_goals", ["hypertrophy"])
        goals = [TrainingGoal(g) if isinstance(g, str) else g for g in goals_data]
        
        return cls(
            name=data.get("name", "Usuário"),
            weight_kg=data.get("weight_kg"),
            height_cm=data.get("height_cm"),
            age=data.get("age"),
            gender=data.get("gender"),
            body_fat_percentage=data.get("body_fat_percentage"),
            experience_level=experience,
            training_goals=goals,
            injuries=data.get("injuries", []),
            measurements=measurements,
            notes=data.get("notes", ""),
        )
    
    def save_to_file(self, filepath: str) -> None:
        """Salva o perfil em um arquivo JSON."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> "UserProfile":
        """Carrega o perfil de um arquivo JSON."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    @classmethod
    def load_or_create(cls, filepath: str) -> "UserProfile":
        """Carrega o perfil se existir, ou cria um novo."""
        if os.path.exists(filepath):
            return cls.load_from_file(filepath)
        return cls()
