"""Testes para o módulo workout_parser."""
import unittest
from src.workout_parser import (
    WorkoutParser,
    RoutineConfig,
    ExerciseConfig,
    SetConfig,
    format_routine_preview,
)


class TestSetConfig(unittest.TestCase):
    """Testes para SetConfig."""

    def test_to_api_format_basic(self):
        """Testa conversão básica para formato da API."""
        set_config = SetConfig(reps=10, weight_kg=80)
        result = set_config.to_api_format()
        
        self.assertEqual(result['type'], 'normal')
        self.assertEqual(result['reps'], 10)
        self.assertEqual(result['weight_kg'], 80)
        # Deve gerar rep_range automático
        self.assertEqual(result['rep_range']['start'], 8)
        self.assertEqual(result['rep_range']['end'], 12)

    def test_to_api_format_with_rep_range(self):
        """Testa conversão com rep_range explícito."""
        set_config = SetConfig(
            rep_range_start=8,
            rep_range_end=12,
            weight_kg=100
        )
        result = set_config.to_api_format()
        
        self.assertEqual(result['rep_range']['start'], 8)
        self.assertEqual(result['rep_range']['end'], 12)

    def test_to_api_format_warmup(self):
        """Testa conversão de série de aquecimento."""
        set_config = SetConfig(type='warmup', reps=15, weight_kg=40)
        result = set_config.to_api_format()
        
        self.assertEqual(result['type'], 'warmup')


class TestExerciseConfig(unittest.TestCase):
    """Testes para ExerciseConfig."""

    def test_to_api_format(self):
        """Testa conversão de exercício para formato da API."""
        exercise = ExerciseConfig(
            name="Supino Reto",
            exercise_template_id="ABC123",
            rest_seconds=90,
            sets=[
                SetConfig(reps=10, weight_kg=80),
                SetConfig(reps=10, weight_kg=80),
            ]
        )
        result = exercise.to_api_format()
        
        self.assertEqual(result['exercise_template_id'], 'ABC123')
        self.assertEqual(result['rest_seconds'], 90)
        self.assertEqual(len(result['sets']), 2)


class TestWorkoutParser(unittest.TestCase):
    """Testes para WorkoutParser."""

    def setUp(self):
        """Configura templates de exercícios para testes."""
        self.templates = {
            'ex1': {'id': 'ex1', 'title': 'Bench Press'},
            'ex2': {'id': 'ex2', 'title': 'Incline Bench Press'},
            'ex3': {'id': 'ex3', 'title': 'Lat Pulldown'},
            'ex4': {'id': 'ex4', 'title': 'Barbell Squat'},
            'ex5': {'id': 'ex5', 'title': 'Supino Reto'},
        }
        self.parser = WorkoutParser(exercise_templates=self.templates)

    def test_find_exercise_id_exact(self):
        """Testa busca de exercício por nome exato."""
        result = self.parser.find_exercise_id("Bench Press")
        self.assertEqual(result, 'ex1')

    def test_find_exercise_id_case_insensitive(self):
        """Testa busca case-insensitive."""
        result = self.parser.find_exercise_id("bench press")
        self.assertEqual(result, 'ex1')

    def test_find_exercise_id_partial(self):
        """Testa busca parcial."""
        result = self.parser.find_exercise_id("Bench")
        self.assertIn(result, ['ex1', 'ex2'])  # Pode encontrar qualquer um com "bench"

    def test_find_exercise_id_not_found(self):
        """Testa busca de exercício inexistente."""
        result = self.parser.find_exercise_id("Exercício Inventado XYZ")
        self.assertIsNone(result)

    def test_parse_json_simple(self):
        """Testa parsing de JSON simples."""
        json_str = '''
        {
            "title": "Treino A",
            "exercises": [
                {
                    "name": "Bench Press",
                    "sets": 3,
                    "reps": 10,
                    "rest_seconds": 90
                }
            ]
        }
        '''
        result = self.parser.parse_json(json_str)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.title, "Treino A")
        self.assertEqual(len(result.exercises), 1)
        self.assertEqual(result.exercises[0].name, "Bench Press")
        self.assertEqual(len(result.exercises[0].sets), 3)
        self.assertEqual(result.exercises[0].exercise_template_id, 'ex1')

    def test_parse_json_detailed_sets(self):
        """Testa parsing de JSON com sets detalhados."""
        json_str = '''
        {
            "title": "Treino B",
            "exercises": [
                {
                    "name": "Supino Reto",
                    "rest_seconds": 120,
                    "sets": [
                        {"type": "warmup", "reps": 15, "weight_kg": 40},
                        {"type": "normal", "reps": 10, "weight_kg": 80},
                        {"type": "normal", "reps": 8, "weight_kg": 90}
                    ]
                }
            ]
        }
        '''
        result = self.parser.parse_json(json_str)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result.exercises[0].sets), 3)
        self.assertEqual(result.exercises[0].sets[0].type, 'warmup')
        self.assertEqual(result.exercises[0].sets[1].weight_kg, 80)

    def test_parse_json_invalid(self):
        """Testa parsing de JSON inválido."""
        result = self.parser.parse_json("isso não é json")
        self.assertIsNone(result)

    def test_parse_text_simple(self):
        """Testa parsing de texto simples."""
        text = """
        Treino A - Peito
        
        - Bench Press: 3x10
        - Incline Bench Press: 3x12
        """
        result = self.parser.parse_text(text)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result.exercises), 2)
        self.assertEqual(result.exercises[0].name, "Bench Press")
        self.assertEqual(len(result.exercises[0].sets), 3)

    def test_parse_text_with_weight_and_rest(self):
        """Testa parsing de texto com peso e descanso."""
        text = """
        Treino: Força
        
        - Bench Press - 4x8 @ 100kg - 120s descanso
        """
        result = self.parser.parse_text(text)
        
        self.assertIsNotNone(result)
        ex = result.exercises[0]
        self.assertEqual(len(ex.sets), 4)
        self.assertEqual(ex.sets[0].weight_kg, 100)
        self.assertEqual(ex.rest_seconds, 120)

    def test_parse_text_rep_range(self):
        """Testa parsing de texto com faixa de repetições."""
        text = """
        - Bench Press: 3x8-12
        """
        result = self.parser.parse_text(text)
        
        self.assertIsNotNone(result)
        ex = result.exercises[0]
        self.assertEqual(ex.sets[0].rep_range_start, 8)
        self.assertEqual(ex.sets[0].rep_range_end, 12)

    def test_parse_auto_detect_json(self):
        """Testa detecção automática de JSON."""
        content = '{"title": "Test", "exercises": []}'
        result = self.parser.parse(content)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.title, "Test")

    def test_parse_auto_detect_text(self):
        """Testa detecção automática de texto."""
        content = "- Bench Press: 3x10"
        result = self.parser.parse(content)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result.exercises), 1)

    def test_parse_json_in_markdown(self):
        """Testa extração de JSON de bloco markdown."""
        content = '''
        Aqui está o treino:
        
        ```json
        {"title": "Treino A", "exercises": [{"name": "Bench Press", "sets": 3, "reps": 10}]}
        ```
        '''
        result = self.parser.parse(content)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.title, "Treino A")

    def test_validate_routine_valid(self):
        """Testa validação de rotina válida."""
        routine = RoutineConfig(
            title="Treino A",
            exercises=[
                ExerciseConfig(
                    name="Bench Press",
                    exercise_template_id="ex1",
                    sets=[SetConfig(reps=10)]
                )
            ]
        )
        
        valid, errors = self.parser.validate_routine(routine)
        self.assertTrue(valid)
        self.assertEqual(len(errors), 0)

    def test_validate_routine_missing_title(self):
        """Testa validação de rotina sem título."""
        routine = RoutineConfig(
            title="",
            exercises=[
                ExerciseConfig(name="Test", exercise_template_id="ex1", sets=[SetConfig(reps=10)])
            ]
        )
        
        valid, errors = self.parser.validate_routine(routine)
        self.assertFalse(valid)
        self.assertTrue(any("Título" in e for e in errors))

    def test_validate_routine_missing_exercises(self):
        """Testa validação de rotina sem exercícios."""
        routine = RoutineConfig(title="Test", exercises=[])
        
        valid, errors = self.parser.validate_routine(routine)
        self.assertFalse(valid)
        self.assertTrue(any("pelo menos um exercício" in e for e in errors))

    def test_validate_routine_missing_template_id(self):
        """Testa validação de rotina com exercício sem ID."""
        routine = RoutineConfig(
            title="Test",
            exercises=[
                ExerciseConfig(
                    name="Exercício Desconhecido",
                    exercise_template_id=None,
                    sets=[SetConfig(reps=10)]
                )
            ]
        )
        
        valid, errors = self.parser.validate_routine(routine)
        self.assertFalse(valid)
        self.assertTrue(any("não encontrados" in e for e in errors))


class TestFormatRoutinePreview(unittest.TestCase):
    """Testes para format_routine_preview."""

    def test_format_basic(self):
        """Testa formatação básica."""
        routine = RoutineConfig(
            title="Treino A",
            exercises=[
                ExerciseConfig(
                    name="Bench Press",
                    exercise_template_id="ex1",
                    rest_seconds=90,
                    sets=[SetConfig(reps=10), SetConfig(reps=10), SetConfig(reps=10)]
                )
            ]
        )
        
        result = format_routine_preview(routine)
        
        self.assertIn("Treino A", result)
        self.assertIn("Bench Press", result)
        self.assertIn("3x10", result)
        self.assertIn("✅", result)  # Tem template_id

    def test_format_missing_template(self):
        """Testa formatação com template faltando."""
        routine = RoutineConfig(
            title="Test",
            exercises=[
                ExerciseConfig(
                    name="Unknown",
                    exercise_template_id=None,
                    sets=[SetConfig(reps=10)]
                )
            ]
        )
        
        result = format_routine_preview(routine)
        self.assertIn("⚠️", result)  # Sem template_id


if __name__ == '__main__':
    unittest.main()
