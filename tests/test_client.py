import unittest
from unittest.mock import patch, Mock
import os
import requests
from src.client import HevyClient

class TestHevyClient(unittest.TestCase):

    @patch.dict(os.environ, {'HEVY_API_KEY': 'test_api_key'})
    def setUp(self):
        self.client = HevyClient()

    @patch('requests.get')
    def test_get_recent_workouts_success(self, mock_get):
        # Configurar o mock para uma resposta bem-sucedida
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'workouts': [{'id': 'w1', 'title': 'Workout 1'}]}
        mock_get.return_value = mock_response

        workouts = self.client.get_recent_workouts(page=1, page_size=1)
        
        # Verificar se requests.get foi chamado corretamente
        mock_get.assert_called_once_with(
            "https://api.hevyapp.com/v1/workouts",
            headers={"api-key": "test_api_key", "Accept": "application/json"},
            params={"page": 1, "pageSize": 1},
            timeout=30
        )
        self.assertEqual(workouts, [{'id': 'w1', 'title': 'Workout 1'}])

    @patch('requests.get')
    def test_get_recent_workouts_http_error(self, mock_get):
        # Configurar o mock para simular um erro HTTP
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError
        mock_get.return_value = mock_response

        with self.assertRaises(requests.exceptions.HTTPError):
            self.client.get_recent_workouts()

    @patch('requests.get')
    def test_get_exercise_template_success(self, mock_get):
        # Configurar o mock para uma resposta bem-sucedida
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': 'et1', 'primary_muscle_group': 'Chest'}
        mock_get.return_value = mock_response

        template = self.client.get_exercise_template('et1')

        # Verificar se requests.get foi chamado corretamente
        mock_get.assert_called_once_with(
            "https://api.hevyapp.com/v1/exercise_templates/et1",
            headers={"api-key": "test_api_key", "Accept": "application/json"},
            timeout=30
        )
        self.assertEqual(template, {'id': 'et1', 'primary_muscle_group': 'Chest'})

    @patch('requests.get')
    def test_get_exercise_template_http_error(self, mock_get):
        # Configurar o mock para simular um erro HTTP
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError
        mock_get.return_value = mock_response

        with self.assertRaises(requests.exceptions.HTTPError):
            self.client.get_exercise_template('et_invalid')

    # ==================== Testes para métodos POST ====================

    @patch('requests.get')
    def test_get_routine_folders_success(self, mock_get):
        """Testa busca de pastas de rotinas."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'routine_folders': [
                {'id': 'folder1', 'title': 'Push'},
                {'id': 'folder2', 'title': 'Pull'}
            ]
        }
        mock_get.return_value = mock_response

        folders = self.client.get_routine_folders()
        
        self.assertEqual(len(folders), 2)
        self.assertEqual(folders[0]['title'], 'Push')

    @patch('requests.post')
    def test_create_routine_folder_success(self, mock_post):
        """Testa criação de pasta de rotinas."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'routine_folder': {'id': 'new_folder', 'title': 'Treinos IA'}
        }
        mock_post.return_value = mock_response

        result = self.client.create_routine_folder("Treinos IA")
        
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args[1]
        self.assertEqual(call_kwargs['json']['routine_folder']['title'], 'Treinos IA')
        self.assertEqual(result['routine_folder']['title'], 'Treinos IA')

    @patch('requests.post')
    def test_create_routine_success(self, mock_post):
        """Testa criação de rotina completa."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'routine': {
                'id': 'routine123',
                'title': 'Treino A - Peito',
                'exercises': []
            }
        }
        mock_post.return_value = mock_response

        exercises = [
            {
                'exercise_template_id': 'ABC123',
                'rest_seconds': 90,
                'sets': [
                    {'type': 'normal', 'reps': 10, 'weight_kg': 80},
                    {'type': 'normal', 'reps': 10, 'weight_kg': 80},
                    {'type': 'normal', 'reps': 10, 'weight_kg': 80},
                ]
            }
        ]

        result = self.client.create_routine(
            title="Treino A - Peito",
            exercises=exercises,
            notes="Focar na forma"
        )
        
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs['json']
        
        self.assertEqual(payload['routine']['title'], 'Treino A - Peito')
        self.assertEqual(len(payload['routine']['exercises']), 1)
        self.assertEqual(len(payload['routine']['exercises'][0]['sets']), 3)
        self.assertEqual(result['routine']['id'], 'routine123')

    @patch('requests.post')
    def test_create_routine_with_rep_range(self, mock_post):
        """Testa criação de rotina com faixa de repetições."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'routine': {'id': 'r1'}}
        mock_post.return_value = mock_response

        exercises = [
            {
                'exercise_template_id': 'ABC123',
                'rest_seconds': 60,
                'sets': [
                    {
                        'type': 'normal',
                        'reps': 10,
                        'rep_range': {'start': 8, 'end': 12}
                    }
                ]
            }
        ]

        self.client.create_routine(title="Test", exercises=exercises)
        
        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs['json']
        set_data = payload['routine']['exercises'][0]['sets'][0]
        
        self.assertEqual(set_data['rep_range']['start'], 8)
        self.assertEqual(set_data['rep_range']['end'], 12)

    @patch('requests.get')
    def test_search_exercise_template_exact_match(self, mock_get):
        """Testa busca de exercício por nome exato."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'exercise_templates': [
                {'id': 'ex1', 'title': 'Bench Press'},
                {'id': 'ex2', 'title': 'Incline Bench Press'},
            ]
        }
        mock_get.return_value = mock_response

        templates = self.client.get_all_exercise_templates(max_pages=1)
        result = self.client.search_exercise_template("Bench Press", templates)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['id'], 'ex1')

    @patch('requests.get')
    def test_search_exercise_template_partial_match(self, mock_get):
        """Testa busca de exercício por nome parcial."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'exercise_templates': [
                {'id': 'ex1', 'title': 'Barbell Bench Press'},
                {'id': 'ex2', 'title': 'Dumbbell Curl'},
            ]
        }
        mock_get.return_value = mock_response

        templates = self.client.get_all_exercise_templates(max_pages=1)
        result = self.client.search_exercise_template("bench press", templates)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['id'], 'ex1')

    @patch('requests.post')
    def test_create_routine_http_error(self, mock_post):
        """Testa erro HTTP ao criar rotina."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Bad Request")
        mock_post.return_value = mock_response

        with self.assertRaises(requests.exceptions.HTTPError):
            self.client.create_routine(title="Test", exercises=[])


if __name__ == '__main__':
    unittest.main()
