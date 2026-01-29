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

