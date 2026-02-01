import unittest
from unittest.mock import Mock, patch
import pandas as pd
from src.processor import WorkoutProcessor
from src.client import HevyClient # Importa HevyClient para mocking, se necessário

class TestWorkoutProcessor(unittest.TestCase):

    def setUp(self):
        # Dados de exemplo para os testes
        self.sample_workouts = [
            {
                "id": "w1",
                "title": "Upper Body",
                "start_time": "2023-01-01T10:00:00Z",
                "exercises": [
                    {
                        "name": "Bench Press",
                        "muscle_group": "Chest",
                        "sets": [
                            {"weight": 60, "reps": 10},
                            {"weight": 70, "reps": 8}
                        ]
                    },
                    {
                        "name": "Bicep Curl",
                        "exercise_template_id": "et_bicep",
                        "sets": [
                            {"weight": 20, "reps": 12}
                        ]
                    }
                ]
            },
            {
                "id": "w2",
                "title": "Lower Body",
                "start_time": "2023-01-02T15:00:00Z",
                "exercises": [
                    {
                        "name": "Squat",
                        "muscle_group": "Legs",
                        "sets": [
                            {"weight": 100, "reps": 5},
                            {"weight": 110, "reps": 3}
                        ]
                    }
                ]
            }
        ]
        
        self.mock_hevy_client = Mock(spec=HevyClient)
        self.processor = WorkoutProcessor(self.sample_workouts, hevy_client=self.mock_hevy_client)

    def test_calculate_total_volume(self):
        df_volume = self.processor.calculate_total_volume()
        
        expected_data = [
            {"workout_id": "w1", "title": "Upper Body", "volume_total": (60*10) + (70*8) + (20*12)},
            {"workout_id": "w2", "title": "Lower Body", "volume_total": (100*5) + (110*3)}
        ]
        expected_df = pd.DataFrame(expected_data)
        pd.testing.assert_frame_equal(df_volume, expected_df, check_dtype=False)

    def test_get_muscle_group_from_exercise(self):
        exercise_with_group = {"name": "Deadlift", "muscle_group": "Back", "sets": []}
        self.assertEqual(self.processor._get_muscle_group(exercise_with_group), "Back")

    def test_get_muscle_group_from_client_and_cache(self):
        # Configura o mock do cliente para retornar um template
        self.mock_hevy_client.get_exercise_template.return_value = {"primary_muscle_group": "Biceps"}

        exercise_needs_lookup = {"name": "Bicep Curl", "exercise_template_id": "et_bicep", "sets": []}
        
        # Primeira chamada, deve ir ao cliente
        muscle_group = self.processor._get_muscle_group(exercise_needs_lookup)
        self.assertEqual(muscle_group, "Biceps")
        self.mock_hevy_client.get_exercise_template.assert_called_once_with("et_bicep")
        
        # Segunda chamada para o mesmo template, deve usar o cache
        self.mock_hevy_client.get_exercise_template.reset_mock() # Reseta o contador de chamadas
        muscle_group_cached = self.processor._get_muscle_group(exercise_needs_lookup)
        self.assertEqual(muscle_group_cached, "Biceps")
        self.mock_hevy_client.get_exercise_template.assert_not_called()

    def test_get_muscle_group_no_info(self):
        exercise_no_info = {"name": "Unknown", "sets": []}
        self.assertIsNone(self.processor._get_muscle_group(exercise_no_info))

    def test_calculate_volume_by_muscle_group(self):
        # Configura o mock do cliente para a busca de template, se necessário
        self.mock_hevy_client.get_exercise_template.return_value = {"primary_muscle_group": "Biceps"}

        df_volume_by_group = self.processor.calculate_volume_by_muscle_group()

        expected_data = [
            {"muscle_group": "Chest", "volume_total": (60*10) + (70*8)},
            {"muscle_group": "Biceps", "volume_total": (20*12)},
            {"muscle_group": "Legs", "volume_total": (100*5) + (110*3)}
        ]
        expected_df = pd.DataFrame(expected_data)
        pd.testing.assert_frame_equal(df_volume_by_group, expected_df, check_dtype=False)

    def test_calculate_volume_evolution_by_muscle_group(self):
        # Configura o mock do cliente para a busca de template, se necessário
        self.mock_hevy_client.get_exercise_template.return_value = {"primary_muscle_group": "Biceps"}

        df_evolution = self.processor.calculate_volume_evolution_by_muscle_group()

        expected_data = [
            {"workout_id": "w1", "date": "2023-01-01T10:00:00Z", "muscle_group": "Chest", "volume_total": (60*10) + (70*8)},
            {"workout_id": "w1", "date": "2023-01-01T10:00:00Z", "muscle_group": "Biceps", "volume_total": (20*12)},
            {"workout_id": "w2", "date": "2023-01-02T15:00:00Z", "muscle_group": "Legs", "volume_total": (100*5) + (110*3)}
        ]
        expected_df = pd.DataFrame(expected_data)
        expected_df["date"] = pd.to_datetime(expected_df["date"])

        pd.testing.assert_frame_equal(df_evolution, expected_df, check_dtype=False)

if __name__ == '__main__':
    unittest.main()
