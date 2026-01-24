import os
import requests
from dotenv import load_dotenv

load_dotenv()

class HevyClient:
    def __init__(self):
        self.api_key = os.getenv("HEVY_API_KEY")
        self.base_url = "https://api.hevyapp.com/v1"
        self.headers = {
            "api-key": self.api_key,
            "Accept": "application/json"
        }
    
    def get_recent_workouts(self, page=1, page_size=10):
            url = f"{self.base_url}/workouts"
            params = {"page": page, "pageSize": page_size}
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json().get('workouts', [])
    
    def get_exercise_template(self, exercise_template_id):
        """
        Busca informações do template de exercício através do exercise_template_id.
        Retorna o primary_muscle_group e outras informações do exercício.
        """
        url = f"{self.base_url}/exercise_templates/{exercise_template_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()