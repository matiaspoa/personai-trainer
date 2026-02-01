"""
Testes unitários para o módulo user_profile.
"""
import json
import os
import tempfile
import unittest

from src.user_profile import (
    BodyMeasurements,
    ExperienceLevel,
    TrainingGoal,
    UserProfile,
)


class TestBodyMeasurements(unittest.TestCase):
    """Testes para a classe BodyMeasurements."""

    def test_to_dict_omits_none_values(self):
        """Verifica que to_dict omite valores None."""
        measurements = BodyMeasurements(chest=100.0, waist=80.0)
        result = measurements.to_dict()
        
        self.assertIn("chest", result)
        self.assertIn("waist", result)
        self.assertNotIn("hips", result)
        self.assertNotIn("biceps_left", result)

    def test_get_summary_with_data(self):
        """Verifica o resumo com dados."""
        measurements = BodyMeasurements(
            chest=105.0,
            waist=82.0,
            biceps_left=38.0,
            shoulders=120.0
        )
        summary = measurements.get_summary()
        
        self.assertIn("Peitoral: 105.0cm", summary)
        self.assertIn("Cintura: 82.0cm", summary)
        self.assertIn("Bíceps: 38.0cm", summary)
        self.assertIn("Ombros: 120.0cm", summary)

    def test_get_summary_empty(self):
        """Verifica o resumo sem dados."""
        measurements = BodyMeasurements()
        summary = measurements.get_summary()
        
        self.assertEqual(summary, "Sem medidas registradas")


class TestUserProfile(unittest.TestCase):
    """Testes para a classe UserProfile."""

    def setUp(self):
        """Cria um perfil de teste."""
        self.profile = UserProfile(
            name="Teste",
            weight_kg=80.0,
            height_cm=175.0,
            age=30,
            gender="male",
            body_fat_percentage=15.0,
            experience_level=ExperienceLevel.INTERMEDIATE,
            training_goals=[TrainingGoal.HYPERTROPHY, TrainingGoal.STRENGTH],
            injuries=["Tendinite no ombro"],
            notes="Treina 4x por semana"
        )

    def test_bmi_calculation(self):
        """Verifica o cálculo do IMC."""
        # IMC = 80 / (1.75)^2 = 26.1
        self.assertEqual(self.profile.bmi, 26.1)

    def test_bmi_category(self):
        """Verifica a categoria do IMC."""
        self.assertEqual(self.profile.bmi_category, "Sobrepeso")
        
        # Teste com peso normal
        normal_profile = UserProfile(weight_kg=70.0, height_cm=175.0)
        self.assertEqual(normal_profile.bmi_category, "Peso normal")

    def test_bmi_none_when_missing_data(self):
        """Verifica que IMC é None quando faltam dados."""
        profile = UserProfile(name="Test")
        self.assertIsNone(profile.bmi)
        self.assertIsNone(profile.bmi_category)

    def test_get_context_for_llm(self):
        """Verifica a geração de contexto para o LLM."""
        context = self.profile.get_context_for_llm()
        
        self.assertIn("Teste", context)
        self.assertIn("80.0kg", context)
        self.assertIn("175.0cm", context)
        self.assertIn("30 anos", context)
        self.assertIn("intermediate", context)
        self.assertIn("hypertrophy", context)
        self.assertIn("Tendinite no ombro", context)

    def test_to_dict_and_from_dict(self):
        """Verifica a serialização e deserialização."""
        data = self.profile.to_dict()
        
        self.assertEqual(data["name"], "Teste")
        self.assertEqual(data["weight_kg"], 80.0)
        self.assertEqual(data["experience_level"], "intermediate")
        self.assertIn("hypertrophy", data["training_goals"])
        
        # Recria a partir do dict
        recreated = UserProfile.from_dict(data)
        
        self.assertEqual(recreated.name, self.profile.name)
        self.assertEqual(recreated.weight_kg, self.profile.weight_kg)
        self.assertEqual(recreated.experience_level, self.profile.experience_level)
        self.assertEqual(recreated.training_goals, self.profile.training_goals)

    def test_save_and_load_from_file(self):
        """Verifica salvar e carregar de arquivo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "profile.json")
            
            # Salva
            self.profile.save_to_file(filepath)
            self.assertTrue(os.path.exists(filepath))
            
            # Carrega
            loaded = UserProfile.load_from_file(filepath)
            
            self.assertEqual(loaded.name, self.profile.name)
            self.assertEqual(loaded.weight_kg, self.profile.weight_kg)
            self.assertEqual(loaded.training_goals, self.profile.training_goals)

    def test_load_or_create_new(self):
        """Verifica load_or_create quando arquivo não existe."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "nonexistent.json")
            
            profile = UserProfile.load_or_create(filepath)
            
            self.assertEqual(profile.name, "Usuário")
            self.assertIsNone(profile.weight_kg)

    def test_load_or_create_existing(self):
        """Verifica load_or_create quando arquivo existe."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "existing.json")
            
            # Cria arquivo
            self.profile.save_to_file(filepath)
            
            # Carrega
            loaded = UserProfile.load_or_create(filepath)
            
            self.assertEqual(loaded.name, "Teste")
            self.assertEqual(loaded.weight_kg, 80.0)


class TestTrainingGoal(unittest.TestCase):
    """Testes para o enum TrainingGoal."""

    def test_all_goals_defined(self):
        """Verifica que todos os objetivos estão definidos."""
        expected_goals = [
            "hypertrophy",
            "strength",
            "endurance",
            "fat_loss",
            "maintenance",
            "general_fitness"
        ]
        actual_goals = [g.value for g in TrainingGoal]
        
        for goal in expected_goals:
            self.assertIn(goal, actual_goals)


class TestExperienceLevel(unittest.TestCase):
    """Testes para o enum ExperienceLevel."""

    def test_all_levels_defined(self):
        """Verifica que todos os níveis estão definidos."""
        expected_levels = ["beginner", "intermediate", "advanced", "elite"]
        actual_levels = [l.value for l in ExperienceLevel]
        
        for level in expected_levels:
            self.assertIn(level, actual_levels)


if __name__ == "__main__":
    unittest.main()
