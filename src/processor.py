"""
Processador de dados de treino do Hevy.

Este módulo contém a classe WorkoutProcessor que processa dados brutos da API
do Hevy e calcula métricas como volume total, volume por grupamento muscular,
rankings de exercícios e evoluções ao longo do tempo.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd


class WorkoutProcessor:
    """
    Processa dados de treino e calcula métricas de volume e evolução.
    
    Attributes:
        workouts: Lista de treinos retornados pela API do Hevy.
        hevy_client: Cliente opcional para buscar dados adicionais da API.
    """

    def __init__(
        self, 
        workouts: List[Dict[str, Any]], 
        hevy_client: Optional[Any] = None,
        exercise_templates: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> None:
        """
        Inicializa o processador com dados de treino.
        
        Args:
            workouts: Lista de treinos como retornado pela API do Hevy.
            hevy_client: Instância opcional de HevyClient para buscar informações.
            exercise_templates: Dicionário opcional de templates pré-carregados
                               (chave: exercise_template_id, valor: template).
        """
        self.workouts = workouts
        self.hevy_client = hevy_client
        self._exercise_template_cache: Dict[str, Dict[str, Any]] = exercise_templates or {}
        self._templates_loaded = exercise_templates is not None

    def _ensure_templates_loaded(self) -> None:
        """
        Garante que todos os templates de exercícios estejam carregados no cache.
        
        Faz uma única chamada à API para buscar todos os templates de uma vez,
        evitando múltiplas chamadas individuais.
        """
        if self._templates_loaded or not self.hevy_client:
            return
        
        try:
            # Busca todos os templates de uma vez (muito mais eficiente)
            if hasattr(self.hevy_client, 'get_all_exercise_templates'):
                self._exercise_template_cache = self.hevy_client.get_all_exercise_templates()
                self._templates_loaded = True
        except Exception as e:
            print(f"Aviso: não foi possível carregar templates em batch: {e}")
            # Continua funcionando com cache individual

    def _get_exercise_template(self, exercise_template_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém um template de exercício pelo ID, usando cache.
        """
        if not exercise_template_id:
            return None
            
        if exercise_template_id in self._exercise_template_cache:
            return self._exercise_template_cache[exercise_template_id]
        
        if self.hevy_client:
            try:
                template = self.hevy_client.get_exercise_template(exercise_template_id)
                self._exercise_template_cache[exercise_template_id] = template
                return template
            except Exception as e:
                print(f"Aviso: erro ao buscar template {exercise_template_id}: {e}")
        
        return None

    def _get_muscle_group(self, exercise: Dict[str, Any]) -> Optional[str]:
        """Obtém o grupamento muscular de um exercício."""
        muscle_group = exercise.get("muscle_group")
        if muscle_group:
            return muscle_group
        
        exercise_template_id = exercise.get("exercise_template_id")
        if exercise_template_id:
            template = self._get_exercise_template(exercise_template_id)
            if template:
                return template.get("primary_muscle_group")
        
        return None

    def _get_exercise_title(self, exercise: Dict[str, Any]) -> str:
        """Obtém o título/nome do exercício."""
        title = exercise.get("title") or exercise.get("name")
        if title:
            return title
        
        exercise_template_id = exercise.get("exercise_template_id")
        if exercise_template_id:
            template = self._get_exercise_template(exercise_template_id)
            if template:
                return template.get("title", "Unknown")
        
        return "Unknown"

    def _calculate_set_volume(self, set_data: Dict[str, Any]) -> float:
        """Calcula o volume de um set: peso * repetições."""
        weight = set_data.get("weight_kg") or set_data.get("weight") or 0
        reps = set_data.get("reps") or 0
        return float(weight) * float(reps)

    def calculate_total_volume(self) -> pd.DataFrame:
        """Calcula o volume total para cada treino."""
        records = []
        for workout in self.workouts:
            workout_id = workout.get("id")
            title = workout.get("title") or workout.get("name") or workout_id
            date = workout.get("start_time") or workout.get("created_at") or workout.get("date")
            
            volume_total = 0.0
            for exercise in workout.get("exercises", []):
                for set_data in exercise.get("sets", []):
                    volume_total += self._calculate_set_volume(set_data)
            
            records.append({
                "workout_id": workout_id,
                "title": title,
                "date": date,
                "volume_total": volume_total
            })

        df = pd.DataFrame(records)
        if not df.empty and "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        return df

    def calculate_volume_by_muscle_group(self) -> pd.DataFrame:
        """Calcula o volume total agrupado por grupamento muscular."""
        self._ensure_templates_loaded()
        
        muscle_data: Dict[str, Dict[str, float]] = {}
        
        for workout in self.workouts:
            for exercise in workout.get("exercises", []):
                muscle_group = self._get_muscle_group(exercise)
                if not muscle_group:
                    continue
                
                if muscle_group not in muscle_data:
                    muscle_data[muscle_group] = {"volume_total": 0.0, "sets_count": 0}
                
                for set_data in exercise.get("sets", []):
                    muscle_data[muscle_group]["volume_total"] += self._calculate_set_volume(set_data)
                    muscle_data[muscle_group]["sets_count"] += 1
        
        records = [
            {"muscle_group": group, "volume_total": data["volume_total"], "sets_count": int(data["sets_count"])}
            for group, data in muscle_data.items()
        ]
        
        return pd.DataFrame(records)

    def calculate_top_exercises(self, top_n: int = 10) -> pd.DataFrame:
        """Calcula os top N exercícios por volume total."""
        self._ensure_templates_loaded()
        
        exercise_data: Dict[str, Dict[str, Any]] = {}
        
        for workout in self.workouts:
            for exercise in workout.get("exercises", []):
                exercise_id = exercise.get("exercise_template_id") or exercise.get("title")
                if not exercise_id:
                    continue
                
                exercise_name = self._get_exercise_title(exercise)
                muscle_group = self._get_muscle_group(exercise) or "Unknown"
                
                if exercise_id not in exercise_data:
                    exercise_data[exercise_id] = {
                        "exercise_name": exercise_name,
                        "muscle_group": muscle_group,
                        "volume_total": 0.0,
                        "sets_count": 0,
                        "times_performed": 0
                    }
                
                exercise_data[exercise_id]["times_performed"] += 1
                
                for set_data in exercise.get("sets", []):
                    exercise_data[exercise_id]["volume_total"] += self._calculate_set_volume(set_data)
                    exercise_data[exercise_id]["sets_count"] += 1
        
        records = list(exercise_data.values())
        df = pd.DataFrame(records)
        
        if not df.empty:
            df = df.sort_values("volume_total", ascending=False).head(top_n).reset_index(drop=True)
        
        return df

    def calculate_volume_evolution_by_muscle_group(self) -> pd.DataFrame:
        """Calcula a evolução do volume por grupamento muscular ao longo do tempo."""
        self._ensure_templates_loaded()
        
        records = []
        
        for workout in self.workouts:
            workout_id = workout.get("id")
            workout_date = workout.get("start_time") or workout.get("created_at") or workout.get("date")
            
            muscle_volumes: Dict[str, float] = {}
            
            for exercise in workout.get("exercises", []):
                muscle_group = self._get_muscle_group(exercise)
                if not muscle_group:
                    continue
                
                if muscle_group not in muscle_volumes:
                    muscle_volumes[muscle_group] = 0.0
                
                for set_data in exercise.get("sets", []):
                    muscle_volumes[muscle_group] += self._calculate_set_volume(set_data)
            
            for muscle_group, volume in muscle_volumes.items():
                records.append({
                    "workout_id": workout_id,
                    "date": workout_date,
                    "muscle_group": muscle_group,
                    "volume_total": volume
                })
        
        df = pd.DataFrame(records)
        if not df.empty and "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df = df.sort_values("date")
        
        return df

    def calculate_exercise_evolution(self, top_n: int = 10) -> pd.DataFrame:
        """Calcula a evolução dos top N exercícios mais frequentes ao longo do tempo."""
        self._ensure_templates_loaded()
        
        exercise_freq: Dict[str, int] = {}
        for workout in self.workouts:
            for exercise in workout.get("exercises", []):
                exercise_id = exercise.get("exercise_template_id")
                if exercise_id:
                    exercise_freq[exercise_id] = exercise_freq.get(exercise_id, 0) + 1
        
        top_exercises = sorted(exercise_freq.keys(), key=lambda x: exercise_freq[x], reverse=True)[:top_n]
        
        records = []
        for workout in self.workouts:
            workout_date = workout.get("start_time") or workout.get("created_at") or workout.get("date")
            
            for exercise in workout.get("exercises", []):
                exercise_id = exercise.get("exercise_template_id")
                if exercise_id not in top_exercises:
                    continue
                
                exercise_name = self._get_exercise_title(exercise)
                volume_total = 0.0
                max_weight = 0.0
                max_reps = 0
                
                for set_data in exercise.get("sets", []):
                    weight = set_data.get("weight_kg") or set_data.get("weight") or 0
                    reps = set_data.get("reps") or 0
                    volume_total += float(weight) * float(reps)
                    max_weight = max(max_weight, float(weight))
                    max_reps = max(max_reps, int(reps))
                
                records.append({
                    "date": workout_date,
                    "exercise_name": exercise_name,
                    "exercise_id": exercise_id,
                    "volume_total": volume_total,
                    "max_weight": max_weight,
                    "max_reps": max_reps
                })
        
        df = pd.DataFrame(records)
        if not df.empty and "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df = df.sort_values("date")
        
        return df

    def calculate_workout_evolution(self, top_n: int = 10) -> pd.DataFrame:
        """Calcula a evolução dos top N tipos de treino ao longo do tempo."""
        workout_freq: Dict[str, int] = {}
        for workout in self.workouts:
            title = workout.get("title") or "Untitled"
            workout_freq[title] = workout_freq.get(title, 0) + 1
        
        top_workout_types = sorted(workout_freq.keys(), key=lambda x: workout_freq[x], reverse=True)[:top_n]
        
        records = []
        for workout in self.workouts:
            title = workout.get("title") or "Untitled"
            if title not in top_workout_types:
                continue
            
            workout_date = workout.get("start_time") or workout.get("created_at") or workout.get("date")
            
            start_time = workout.get("start_time")
            end_time = workout.get("end_time")
            duration_minutes = None
            if start_time and end_time:
                try:
                    start = pd.to_datetime(start_time)
                    end = pd.to_datetime(end_time)
                    duration_minutes = (end - start).total_seconds() / 60
                except:
                    pass
            
            volume_total = 0.0
            exercises_count = len(workout.get("exercises", []))
            
            for exercise in workout.get("exercises", []):
                for set_data in exercise.get("sets", []):
                    volume_total += self._calculate_set_volume(set_data)
            
            records.append({
                "date": workout_date,
                "workout_title": title,
                "volume_total": volume_total,
                "exercises_count": exercises_count,
                "duration_minutes": duration_minutes
            })
        
        df = pd.DataFrame(records)
        if not df.empty and "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df = df.sort_values("date")
        
        return df

    def get_summary_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas resumidas dos treinos."""
        total_workouts = len(self.workouts)
        total_volume = 0.0
        total_exercises = 0
        total_sets = 0
        
        for workout in self.workouts:
            for exercise in workout.get("exercises", []):
                total_exercises += 1
                for set_data in exercise.get("sets", []):
                    total_sets += 1
                    total_volume += self._calculate_set_volume(set_data)
        
        return {
            "total_workouts": total_workouts,
            "total_volume": total_volume,
            "total_exercises": total_exercises,
            "total_sets": total_sets,
            "avg_volume_per_workout": total_volume / total_workouts if total_workouts > 0 else 0,
            "avg_exercises_per_workout": total_exercises / total_workouts if total_workouts > 0 else 0,
            "avg_sets_per_workout": total_sets / total_workouts if total_workouts > 0 else 0,
        }