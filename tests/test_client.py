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

if __name__ == '__main__':
    unittest.main()
