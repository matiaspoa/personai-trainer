import os
import requests
import pandas as pd 
from dotenv import load_dotenv

# Carrega as variáveis do .env
load_dotenv()

def test_hevy_connection():
    api_key = os.getenv("HEVY_API_KEY")
    url = "https://api.hevyapp.com/v1/workouts"

    headers = {
        "api-key": api_key,
        "Accept": "application/json"
    }

    print("iniciando conexão com Hevy")

    try:
        # Buscamos os últimos 5 treinos para testar
        response = requests.get(url, headers=headers, params={"page": 1, "pageSize": 5})
        response.raise_for_status() # levanta erro se a requisição falhar

        data = response.json()
        workouts = data.get('workout', [])

        if workouts:
            print(f"Tudo certo, {len(workouts)} treinos lidos.")

            # transformando em dataframe para ver como os dados são estruturados
            df = pd.dataframe(workouts)
            print("\n Prévia dos dados")
            print(df[['title','start_time', 'end_time']].head())
        else:
            print("nenhum treino encontrado")

    except Exception as e:
        print(f"erro: {e}")

if __name__ == "__main__":
    test_hevy_connection()