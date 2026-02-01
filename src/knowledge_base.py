from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class ScienceSource:
    """Representa uma fonte científica ou técnica usada nas recomendações."""

    name: str
    url: str


class ScienceKnowledgeBase:
    """
    Camada de conhecimento científico (stub inicial).

    Objetivo:
    - Centralizar referências de qualidade (ExRx, Stronger by Science, etc.).
    - Facilitar, no futuro, consultas mais sofisticadas (scraping, embeddings, RAG).

    Por enquanto, usamos apenas um mapeamento estático de exemplos.
    """

    def __init__(self) -> None:
        # Mapeamento simples: muscle_group → lista de fontes recomendadas.
        # Você pode evoluir isso para um arquivo YAML/JSON externo no futuro.
        self._sources_by_group: Dict[str, List[ScienceSource]] = {
            "chest": [
                ScienceSource(
                    name="ExRx — Chest Exercises",
                    url="https://exrx.net/Lists/ExList/ChestWt",
                ),
                ScienceSource(
                    name="Stronger By Science — Hypertrophy Guide",
                    url="https://www.strongerbyscience.com/hypertrophy/",
                ),
            ],
            "back": [
                ScienceSource(
                    name="ExRx — Back Exercises",
                    url="https://exrx.net/Lists/ExList/BackWt",
                ),
                ScienceSource(
                    name="Stronger By Science — Back Training",
                    url="https://www.strongerbyscience.com/back-training/",
                ),
            ],
            "shoulders": [
                ScienceSource(
                    name="ExRx — Shoulder Exercises",
                    url="https://exrx.net/Lists/ExList/SsshoijWt",
                ),
                ScienceSource(
                    name="Stronger By Science — Shoulder Training",
                    url="https://www.strongerbyscience.com/overhead-press/",
                ),
            ],
            "biceps": [
                ScienceSource(
                    name="ExRx — Biceps Exercises",
                    url="https://exrx.net/Lists/ExList/ArmWt#Biceps",
                ),
                ScienceSource(
                    name="Stronger By Science — Arm Training",
                    url="https://www.strongerbyscience.com/arm-training/",
                ),
            ],
            "triceps": [
                ScienceSource(
                    name="ExRx — Triceps Exercises",
                    url="https://exrx.net/Lists/ExList/ArmWt#Triceps",
                ),
                ScienceSource(
                    name="Stronger By Science — Arm Training",
                    url="https://www.strongerbyscience.com/arm-training/",
                ),
            ],
            "legs": [
                ScienceSource(
                    name="ExRx — Quadriceps Exercises",
                    url="https://exrx.net/Lists/ExList/ThighWt",
                ),
                ScienceSource(
                    name="Stronger By Science — Squat Guide",
                    url="https://www.strongerbyscience.com/squat/",
                ),
            ],
            "quadriceps": [
                ScienceSource(
                    name="ExRx — Quadriceps Exercises",
                    url="https://exrx.net/Lists/ExList/ThighWt#Quadriceps",
                ),
                ScienceSource(
                    name="Stronger By Science — Squat Guide",
                    url="https://www.strongerbyscience.com/squat/",
                ),
            ],
            "hamstrings": [
                ScienceSource(
                    name="ExRx — Hamstrings Exercises",
                    url="https://exrx.net/Lists/ExList/ThighWt#Hamstrings",
                ),
                ScienceSource(
                    name="Stronger By Science — Deadlift Guide",
                    url="https://www.strongerbyscience.com/deadlift/",
                ),
            ],
            "glutes": [
                ScienceSource(
                    name="ExRx — Glutes Exercises",
                    url="https://exrx.net/Lists/ExList/HipsWt#Gluteus",
                ),
                ScienceSource(
                    name="Stronger By Science — Hip Thrust Guide",
                    url="https://www.strongerbyscience.com/hip-thrust/",
                ),
            ],
            "calves": [
                ScienceSource(
                    name="ExRx — Calves Exercises",
                    url="https://exrx.net/Lists/ExList/CalfWt",
                ),
                ScienceSource(
                    name="Stronger By Science — Calf Training",
                    url="https://www.strongerbyscience.com/calves/",
                ),
            ],
            "abs": [
                ScienceSource(
                    name="ExRx — Abdominal Exercises",
                    url="https://exrx.net/Lists/ExList/WassiWt",
                ),
                ScienceSource(
                    name="Stronger By Science — Core Training",
                    url="https://www.strongerbyscience.com/core-training/",
                ),
            ],
            "core": [
                ScienceSource(
                    name="ExRx — Abdominal & Core Exercises",
                    url="https://exrx.net/Lists/ExList/WaistWt",
                ),
                ScienceSource(
                    name="Stronger By Science — Core Training",
                    url="https://www.strongerbyscience.com/core-training/",
                ),
            ],
            "forearms": [
                ScienceSource(
                    name="ExRx — Forearm Exercises",
                    url="https://exrx.net/Lists/ExList/FsoreijWt",
                ),
                ScienceSource(
                    name="Stronger By Science — Grip Training",
                    url="https://www.strongerbyscience.com/grip-training/",
                ),
            ],
            "traps": [
                ScienceSource(
                    name="ExRx — Trapezius Exercises",
                    url="https://exrx.net/Lists/ExList/NeckWt#Trapezius",
                ),
                ScienceSource(
                    name="Stronger By Science — Trap Training",
                    url="https://www.strongerbyscience.com/shrugs/",
                ),
            ],
            "lats": [
                ScienceSource(
                    name="ExRx — Latissimus Dorsi Exercises",
                    url="https://exrx.net/Lists/ExList/BackWt#Latissimus",
                ),
                ScienceSource(
                    name="Stronger By Science — Pull-up Guide",
                    url="https://www.strongerbyscience.com/pull-ups/",
                ),
            ],
        }

    def get_sources_for_muscle_group(self, muscle_group: str) -> List[ScienceSource]:
        """
        Retorna fontes sugeridas para um determinado grupamento muscular.

        Se não houver nada específico, retorna uma lista genérica.
        """
        key = muscle_group.lower()
        if key in self._sources_by_group:
            return self._sources_by_group[key]

        return [
            ScienceSource(
                name="ExRx — Exercise Directory",
                url="https://exrx.net/Lists/Directory",
            ),
            ScienceSource(
                name="Stronger By Science — Articles",
                url="https://www.strongerbyscience.com/articles/",
            ),
        ]

