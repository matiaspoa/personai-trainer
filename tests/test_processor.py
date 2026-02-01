import unittest
from unittest.mock import Mock, patch
import pandas as pd
from src.processor import WorkoutProcessor
from src.client import HevyClient


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
        # Configura o mock para retornar um dict vazio no batch loading
        self.mock_hevy_client.get_all_exercise_templates.return_value = {}
        self.processor = WorkoutProcessor(self.sample_workouts, hevy_client=self.mock_hevy_client)

    def test_calculate_total_volume(self):
        df_volume = self.processor.calculate_total_volume()
        
        # Verifica que as colunas esperadas existem
        self.assertIn("workout_id", df_volume.columns)
        self.assertIn("title", df_volume.columns)
        self.assertIn("volume_total", df_volume.columns)
        self.assertIn("date", df_volume.columns)
        
        # Verifica os valores de volume
        self.assertEqual(len(df_volume), 2)
        self.assertEqual(df_volume.iloc[0]["volume_total"], (60*10) + (70*8) + (20*12))
        self.assertEqual(df_volume.iloc[1]["volume_total"], (100*5) + (110*3))

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
        self.mock_hevy_client.get_exercise_template.reset_mock()
        muscle_group_cached = self.processor._get_muscle_group(exercise_needs_lookup)
        self.assertEqual(muscle_group_cached, "Biceps")
        self.mock_hevy_client.get_exercise_template.assert_not_called()

    def test_get_muscle_group_no_info(self):
        exercise_no_info = {"name": "Unknown", "sets": []}
        self.assertIsNone(self.processor._get_muscle_group(exercise_no_info))

    def test_calculate_volume_by_muscle_group(self):
        # Configura o mock do cliente para a busca de template
        self.mock_hevy_client.get_exercise_template.return_value = {"primary_muscle_group": "Biceps"}

        df_volume_by_group = self.processor.calculate_volume_by_muscle_group()

        # Verifica que as colunas esperadas existem
        self.assertIn("muscle_group", df_volume_by_group.columns)
        self.assertIn("volume_total", df_volume_by_group.columns)
        self.assertIn("sets_count", df_volume_by_group.columns)
        
        # Verifica os valores por grupo muscular
        chest_row = df_volume_by_group[df_volume_by_group["muscle_group"] == "Chest"]
        self.assertEqual(chest_row.iloc[0]["volume_total"], (60*10) + (70*8))
        self.assertEqual(chest_row.iloc[0]["sets_count"], 2)
        
        biceps_row = df_volume_by_group[df_volume_by_group["muscle_group"] == "Biceps"]
        self.assertEqual(biceps_row.iloc[0]["volume_total"], (20*12))
        self.assertEqual(biceps_row.iloc[0]["sets_count"], 1)

    def test_calculate_volume_evolution_by_muscle_group(self):
        # Configura o mock do cliente para a busca de template
        self.mock_hevy_client.get_exercise_template.return_value = {"primary_muscle_group": "Biceps"}

        df_evolution = self.processor.calculate_volume_evolution_by_muscle_group()

        # Verifica que as colunas esperadas existem
        self.assertIn("workout_id", df_evolution.columns)
        self.assertIn("date", df_evolution.columns)
        self.assertIn("muscle_group", df_evolution.columns)
        self.assertIn("volume_total", df_evolution.columns)
        
        # Verifica que a data foi convertida para datetime
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df_evolution["date"]))

    def test_calculate_top_exercises(self):
        # Configura o mock do cliente para a busca de template
        self.mock_hevy_client.get_exercise_template.return_value = {
            "primary_muscle_group": "Biceps",
            "title": "Bicep Curl"
        }

        df_top = self.processor.calculate_top_exercises(top_n=5)

        # Verifica que as colunas esperadas existem
        self.assertIn("exercise_name", df_top.columns)
        self.assertIn("muscle_group", df_top.columns)
        self.assertIn("volume_total", df_top.columns)
        self.assertIn("sets_count", df_top.columns)
        self.assertIn("times_performed", df_top.columns)

    def test_get_summary_stats(self):
        stats = self.processor.get_summary_stats()
        
        self.assertEqual(stats["total_workouts"], 2)
        self.assertEqual(stats["total_exercises"], 3)
        self.assertEqual(stats["total_sets"], 5)
        expected_volume = (60*10) + (70*8) + (20*12) + (100*5) + (110*3)
        self.assertEqual(stats["total_volume"], expected_volume)


if __name__ == '__main__':
    unittest.main()
