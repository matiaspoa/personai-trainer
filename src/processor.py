import pandas as pd

class WorkoutProcessor:
    def __init__(self, workouts, hevy_client=None):
        """
        workouts: lista de treinos como retornado pela API do Hevy.
        Cada treino deve conter uma lista de exercícios e, para cada exercício,
        uma lista de sets (séries) com peso (weight) e repetições (reps).
        hevy_client: instância opcional de HevyClient para buscar informações dos exercícios.
        """
        self.workouts = workouts
        self.hevy_client = hevy_client
        self._exercise_template_cache = {}  # Cache para evitar múltiplas chamadas à API

    def calculate_total_volume(self):
        """
        Calcula o volume total (peso * repetições * séries) para cada treino.
        Retorna um DataFrame com o id/título do treino e o volume total.
        """
        records = []
        for workout in self.workouts:
            workout_id = workout.get("id")
            title = workout.get("title", workout_id)
            volume_total = 0
            exercises = workout.get("exercises", [])
            for exercise in exercises:
                sets = exercise.get("sets", [])
                for s in sets:
                    peso = s.get("weight", 0)
                    reps = s.get("reps", 0)
                    volume_total += peso * reps
            records.append({"workout_id": workout_id, "title": title, "volume_total": volume_total})

        return pd.DataFrame(records)

    def _get_muscle_group(self, exercise):
        """
        Obtém o grupamento muscular de um exercício.
        Primeiro tenta usar o campo muscle_group direto, depois busca via exercise_template_id.
        """
        # Primeiro tenta usar o muscle_group direto do exercício
        muscle_group = exercise.get("muscle_group")
        if muscle_group:
            return muscle_group
        
        # Se não tiver e tiver client, busca via exercise_template_id
        if self.hevy_client:
            exercise_template_id = exercise.get("exercise_template_id")
            if exercise_template_id:
                # Verifica cache primeiro
                if exercise_template_id in self._exercise_template_cache:
                    template = self._exercise_template_cache[exercise_template_id]
                else:
                    try:
                        template = self.hevy_client.get_exercise_template(exercise_template_id)
                        self._exercise_template_cache[exercise_template_id] = template
                    except Exception as e:
                        # Se falhar a busca, retorna None
                        print(f"Erro ao buscar template {exercise_template_id}: {e}")
                        return None
                
                # Retorna o primary_muscle_group do template
                return template.get("primary_muscle_group")
        
        return None

    def calculate_volume_by_muscle_group(self):
        """
        Calcula o volume total (peso * repetições) agrupado por grupamento muscular.
        Usa o campo muscle_group do exercício ou busca via exercise_template_id para obter primary_muscle_group.
        Retorna um DataFrame com muscle_group e volume_total.
        """
        muscle_group_volumes = {}
        
        for workout in self.workouts:
            exercises = workout.get("exercises", [])
            for exercise in exercises:
                muscle_group = self._get_muscle_group(exercise)
                if not muscle_group:
                    # Se não conseguir determinar o grupamento muscular, pula
                    continue
                
                sets = exercise.get("sets", [])
                for s in sets:
                    peso = s.get("weight", 0)
                    reps = s.get("reps", 0)
                    volume = peso * reps
                    
                    # Acumula o volume por grupamento muscular
                    if muscle_group in muscle_group_volumes:
                        muscle_group_volumes[muscle_group] += volume
                    else:
                        muscle_group_volumes[muscle_group] = volume
        
        # Converte o dicionário em lista de registros para o DataFrame
        records = [
            {"muscle_group": group, "volume_total": volume}
            for group, volume in muscle_group_volumes.items()
        ]
        
        return pd.DataFrame(records)

    def calculate_volume_evolution_by_muscle_group(self):
        """
        Calcula a evolução do volume por grupamento muscular ao longo do tempo.
        Retorna um DataFrame com workout_id, date, muscle_group e volume_total.
        Útil para análise de progresso e relatórios temporais.
        """
        records = []
        
        for workout in self.workouts:
            workout_id = workout.get("id")
            # Tenta obter a data do treino (pode ser start_time, date, ou created_at)
            workout_date = (
                workout.get("start_time") or 
                workout.get("date") or 
                workout.get("created_at") or 
                workout.get("end_time")
            )
            
            # Dicionário para acumular volume por grupo muscular neste treino
            muscle_group_volumes = {}
            
            exercises = workout.get("exercises", [])
            for exercise in exercises:
                muscle_group = self._get_muscle_group(exercise)
                if not muscle_group:
                    continue
                
                sets = exercise.get("sets", [])
                for s in sets:
                    peso = s.get("weight", 0)
                    reps = s.get("reps", 0)
                    volume = peso * reps
                    
                    # Acumula o volume por grupamento muscular neste treino
                    if muscle_group in muscle_group_volumes:
                        muscle_group_volumes[muscle_group] += volume
                    else:
                        muscle_group_volumes[muscle_group] = volume
            
            # Adiciona um registro para cada grupo muscular neste treino
            for muscle_group, volume in muscle_group_volumes.items():
                records.append({
                    "workout_id": workout_id,
                    "date": workout_date,
                    "muscle_group": muscle_group,
                    "volume_total": volume
                })
        
        df = pd.DataFrame(records)
        
        # Converte a coluna date para datetime se possível
        if not df.empty and "date" in df.columns:
            try:
                df["date"] = pd.to_datetime(df["date"])
            except:
                pass  # Se não conseguir converter, mantém como está
        
        return df