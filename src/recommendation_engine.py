from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import pandas as pd

from knowledge_base import ScienceKnowledgeBase, ScienceSource
from llm_service import LlmClient


@dataclass(frozen=True)
class Recommendation:
    """Recomendação de treino orientada a um grupamento muscular específico."""

    muscle_group: str
    summary: str
    sources: List[ScienceSource]


class RecommendationEngine:
    """
    Gera recomendações textuais com base nos dados de volume e em uma base científica.

    - Não depende diretamente de um provedor de IA específico.
    - Se nenhum LlmClient for passado, gera textos determinísticos e simples.
    """

    def __init__(
        self,
        knowledge_base: ScienceKnowledgeBase,
        llm_client: Optional[LlmClient] = None,
    ) -> None:
        self._kb = knowledge_base
        self._llm = llm_client

    def _build_prompt_for_muscle_group(
        self, muscle_group: str, df_volume_by_muscle: pd.DataFrame
    ) -> str:
        # Filtra linha(s) do grupamento em questão, se existirem.
        row = df_volume_by_muscle.loc[
            df_volume_by_muscle["muscle_group"] == muscle_group
        ].head(1)

        volume_info = ""
        if not row.empty:
            volume = float(row.iloc[0]["volume_total"])
            volume_info = f"Volume atual registrado para {muscle_group}: {volume:.2f} (soma de peso x repetições)."

        sources = self._kb.get_sources_for_muscle_group(muscle_group)
        ref_lines = "\n".join(f"- {s.name}: {s.url}" for s in sources)

        return (
            "Você é um treinador especializado em hipertrofia baseado em evidência.\n"
            f"{volume_info}\n"
            f"Grupamento alvo: {muscle_group}.\n\n"
            "Usando as seguintes referências como inspiração (não precisa citá-las literalmente, "
            "apenas respeitar os princípios gerais de volume, intensidade e recuperação):\n"
            f"{ref_lines}\n\n"
            "Gere um parágrafo curto (3–5 frases) com recomendações para o próximo bloco de treinos "
            "para esse grupamento, focando em progressão de volume e atenção à recuperação."
        )

    def recommend_for_top_muscle_groups(
        self,
        df_volume_by_muscle: pd.DataFrame,
        top_n: int = 3,
    ) -> List[Recommendation]:
        """
        Gera recomendações para os N grupamentos com maior volume total.

        Retorna uma lista de Recommendation, que pode ser impressa no terminal,
        enviada por e-mail, etc.
        """
        if df_volume_by_muscle.empty:
            return []

        df_sorted = (
            df_volume_by_muscle.sort_values("volume_total", ascending=False)
            .head(top_n)
            .reset_index(drop=True)
        )

        recommendations: List[Recommendation] = []

        for _, row in df_sorted.iterrows():
            muscle_group = str(row["muscle_group"])
            sources = self._kb.get_sources_for_muscle_group(muscle_group)

            if self._llm is None:
                # Fallback simples e determinístico (sem IA).
                summary = (
                    f"Para {muscle_group}, mantenha ou aumente gradualmente o volume semanal, "
                    "garantindo ao menos 2–3 sessões por semana e recuperação adequada. "
                    "Consulte as fontes associadas para detalhes de exercícios e técnica."
                )
            else:
                prompt = self._build_prompt_for_muscle_group(
                    muscle_group, df_volume_by_muscle
                )
                summary = self._llm.generate_text(prompt)

            recommendations.append(
                Recommendation(
                    muscle_group=muscle_group,
                    summary=summary,
                    sources=sources,
                )
            )

        return recommendations

