"""Pytest configuration - adds src to Python path."""
import sys
from pathlib import Path

# Add src directory to path so tests can import modules
sys.path.insert(0, str(Path(__file__).parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))
