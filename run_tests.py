#!/usr/bin/env python3
"""Script para rodar testes."""
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import unittest

# Importa os testes
from tests.test_workout_parser import (
    TestSetConfig,
    TestExerciseConfig, 
    TestWorkoutParser,
    TestFormatRoutinePreview,
)
from tests.test_client import TestHevyClient

# Cria suite
loader = unittest.TestLoader()
suite = unittest.TestSuite()

# Adiciona testes
suite.addTests(loader.loadTestsFromTestCase(TestSetConfig))
suite.addTests(loader.loadTestsFromTestCase(TestExerciseConfig))
suite.addTests(loader.loadTestsFromTestCase(TestWorkoutParser))
suite.addTests(loader.loadTestsFromTestCase(TestFormatRoutinePreview))
suite.addTests(loader.loadTestsFromTestCase(TestHevyClient))

# Roda
runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)

# Resumo
print(f"\n{'='*50}")
print(f"Total: {result.testsRun}")
print(f"Falhas: {len(result.failures)}")
print(f"Erros: {len(result.errors)}")
print(f"{'='*50}")

sys.exit(0 if result.wasSuccessful() else 1)
