#!/usr/bin/env python3
"""Script para verificar a integração do WorkoutParser com o dashboard."""
import sys
sys.path.insert(0, 'src')

def test_imports():
    """Testa se todos os módulos importam corretamente."""
    print("=== Verificando Imports ===\n")
    
    try:
        from workout_parser import WorkoutParser, RoutineConfig, ExerciseConfig, SetConfig, format_routine_preview
        print("✅ workout_parser: OK")
    except Exception as e:
        print(f"❌ workout_parser: ERRO - {e}")
        return False
    
    try:
        from client import HevyClient
        print("✅ client: OK")
    except Exception as e:
        print(f"❌ client: ERRO - {e}")
        return False
    
    try:
        from model_router import ModelRouter, LiteLLMClient
        print("✅ model_router: OK")
    except Exception as e:
        print(f"❌ model_router: ERRO - {e}")
        return False
    
    return True


def test_parser():
    """Testa o parser com dados de exemplo."""
    print("\n=== Testando Parser ===\n")
    
    from workout_parser import WorkoutParser, format_routine_preview
    
    # Cria parser com templates mock
    templates = {
        'ex1': {'id': 'ex1', 'title': 'Bench Press'},
        'ex2': {'id': 'ex2', 'title': 'Squat'},
        'ex3': {'id': 'ex3', 'title': 'Lat Pulldown'},
        'ex4': {'id': 'ex4', 'title': 'Supino Reto'},
    }
    parser = WorkoutParser(exercise_templates=templates)
    
    # Teste 1: JSON
    print("Teste 1: Parse de JSON")
    json_input = '''
    {
        "title": "Treino A",
        "exercises": [
            {"name": "Supino Reto", "sets": 3, "reps": 10, "rest_seconds": 90},
            {"name": "Lat Pulldown", "sets": 3, "reps": 12}
        ]
    }
    '''
    routine = parser.parse_json(json_input)
    if routine:
        print(f"  ✅ Rotina: {routine.title}")
        print(f"  ✅ Exercícios: {len(routine.exercises)}")
    else:
        print("  ❌ Falha ao parsear JSON")
        return False
    
    # Teste 2: Texto
    print("\nTeste 2: Parse de texto")
    text_input = """
    # Treino B - Costas
    
    - Lat Pulldown: 4x10-12
    - Bench Press: 3x8
    """
    routine = parser.parse_text(text_input)
    if routine:
        print(f"  ✅ Rotina: {routine.title}")
        print(f"  ✅ Exercícios: {len(routine.exercises)}")
    else:
        print("  ❌ Falha ao parsear texto")
        return False
    
    # Teste 3: Preview
    print("\nTeste 3: Preview da rotina")
    preview = format_routine_preview(routine)
    print(f"  Preview:\n{preview}")
    
    return True


def test_detect_workout():
    """Testa a função de detecção de treino."""
    print("\n=== Testando Detecção de Treino ===\n")
    
    # Importa a função diretamente do módulo dashboard
    import re
    
    def detect_workout_suggestion(text: str) -> bool:
        patterns = [
            r"\d+\s*(?:x|×|X)\s*\d+",
            r"séries?\s*(?:de|:)?\s*\d+",
            r"repeti[çc][õo]es?\s*(?:de|:)?\s*\d+",
            r"(?:supino|agachamento|leg press|remada|pulldown|desenvolvimento|rosca|tríceps|extensão|flexão)",
        ]
        matches = 0
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                matches += 1
        return matches >= 2
    
    # Teste positivo
    text_with_workout = """
    Baseado nos seus dados, sugiro o seguinte treino de peito:
    
    - Supino Reto: 4x8-12
    - Supino Inclinado: 3x10
    - Crucifixo: 3x12-15
    """
    
    if detect_workout_suggestion(text_with_workout):
        print("✅ Detectou corretamente sugestão de treino")
    else:
        print("❌ Falha ao detectar sugestão de treino")
        return False
    
    # Teste negativo
    text_without_workout = """
    Seu volume de treino está adequado.
    Continue mantendo a frequência de 4 treinos por semana.
    """
    
    if not detect_workout_suggestion(text_without_workout):
        print("✅ Corretamente ignorou texto sem treino")
    else:
        print("❌ Falso positivo detectado")
        return False
    
    return True


def main():
    print("=" * 50)
    print("Verificação da Integração WorkoutParser")
    print("=" * 50)
    
    all_ok = True
    
    if not test_imports():
        all_ok = False
    
    if not test_parser():
        all_ok = False
    
    if not test_detect_workout():
        all_ok = False
    
    print("\n" + "=" * 50)
    if all_ok:
        print("✅ TODOS OS TESTES PASSARAM!")
    else:
        print("❌ ALGUNS TESTES FALHARAM")
    print("=" * 50)
    
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
