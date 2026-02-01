from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Any, Dict, List

import pandas as pd
import requests

from client import HevyClient
from email_service import (
    EmailConfig,
    ResendEmailConfig,
    ResendEmailSender,
    SmtpEmailSender,
)
from knowledge_base import ScienceKnowledgeBase
from llm_service import LlmConfig, OpenAiLikeClient
from processor import WorkoutProcessor
from recommendation_engine import RecommendationEngine


@dataclass(frozen=True)
class AppConfig:
    """Configuração de execução do orquestrador (sem expor segredos)."""

    page: int = 1
    page_size: int = 10
    top_n: int = 5


def parse_args() -> AppConfig:
    parser = argparse.ArgumentParser(
        description="Personal Trainer AI — Hevy seasonal hypertrophy reports (orquestrador)."
    )
    parser.add_argument("--page", type=int, default=1, help="Página da API /workouts.")
    parser.add_argument(
        "--page-size", type=int, default=10, help="Quantidade de treinos por página."
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=5,
        help="Quantos itens exibir nos rankings (treinos e grupamentos).",
    )
    args = parser.parse_args()
    return AppConfig(page=max(1, args.page), page_size=max(1, args.page_size), top_n=max(1, args.top_n))


def fetch_workouts(client: HevyClient, cfg: AppConfig) -> List[Dict[str, Any]]:
    try:
        return client.get_recent_workouts(page=cfg.page, page_size=cfg.page_size)
    except requests.HTTPError as exc:
        # Não imprime API key; só contexto seguro.
        raise RuntimeError(f"Falha HTTP ao buscar treinos: {exc}") from exc
    except requests.RequestException as exc:
        raise RuntimeError(f"Falha de rede ao buscar treinos: {exc}") from exc


def print_summary(
    workouts: List[Dict[str, Any]],
    df_volume_by_workout: pd.DataFrame,
    df_volume_by_muscle: pd.DataFrame,
    top_n: int,
) -> None:
    print("\n=== Personal Trainer AI — Resumo (Hevy) ===\n")
    print(f"Treinos carregados: {len(workouts)}")

    total_volume = 0.0
    if not df_volume_by_workout.empty and "volume_total" in df_volume_by_workout.columns:
        total_volume = float(df_volume_by_workout["volume_total"].sum())
    print(f"Volume total (geral): {total_volume:.2f}\n")

    if df_volume_by_workout.empty:
        print("Sem dados de volume por treino.\n")
    else:
        df_top_workouts = (
            df_volume_by_workout.sort_values("volume_total", ascending=False)
            .head(top_n)
            .reset_index(drop=True)
        )
        print(f"Top {top_n} treinos por volume:")
        print(df_top_workouts.to_string(index=False))
        print()

    if df_volume_by_muscle.empty:
        print("Sem dados de volume por grupamento muscular.\n")
    else:
        df_top_muscles = (
            df_volume_by_muscle.sort_values("volume_total", ascending=False)
            .head(top_n)
            .reset_index(drop=True)
        )
        print(f"Top {top_n} grupamentos por volume:")
        print(df_top_muscles.to_string(index=False))
        print()


def main() -> int:
    cfg = parse_args()

    try:
        client = HevyClient()
    except ValueError as exc:
        print(f"Configuração inválida: {exc}")
        print("Dica: crie um arquivo .env com HEVY_API_KEY=... (não commitar).")
        return 2

    try:
        workouts = fetch_workouts(client, cfg)
    except RuntimeError as exc:
        print(str(exc))
        return 1

    if not workouts:
        print("Nenhum treino encontrado na resposta da API.")
        return 0

    processor = WorkoutProcessor(workouts, hevy_client=client)
    df_volume_by_workout = processor.calculate_total_volume()
    df_volume_by_muscle = processor.calculate_volume_by_muscle_group()

    print_summary(
        workouts=workouts,
        df_volume_by_workout=df_volume_by_workout,
        df_volume_by_muscle=df_volume_by_muscle,
        top_n=cfg.top_n,
    )

    # === Geração de recomendações baseadas em evidência (via IA + Knowledge Base) ===
    kb = ScienceKnowledgeBase()

    # LLM é opcional: se não houver configuração OU se a chamada falhar (429 etc.),
    # seguimos sem IA, usando mensagens determinísticas.
    llm_client = None
    try:
        llm_cfg = LlmConfig.from_env()
        llm_client = OpenAiLikeClient(llm_cfg)
    except ValueError:
        # Config ausente → modo offline, sem IA.
        pass

    rec_engine = RecommendationEngine(knowledge_base=kb, llm_client=llm_client)
    try:
        recommendations = rec_engine.recommend_for_top_muscle_groups(
            df_volume_by_muscle=df_volume_by_muscle,
            top_n=min(cfg.top_n, 3),
        )
    except RuntimeError as exc:
        # Falha ao chamar o provedor de IA (ex.: 429 do Gemini) → loga e volta para modo determinístico.
        print(str(exc))
        rec_engine = RecommendationEngine(knowledge_base=kb, llm_client=None)
        recommendations = rec_engine.recommend_for_top_muscle_groups(
            df_volume_by_muscle=df_volume_by_muscle,
            top_n=min(cfg.top_n, 3),
        )

    if recommendations:
        print("Recomendações para próximos treinos (por grupamento):\n")
        for rec in recommendations:
            print(f"[{rec.muscle_group}]")
            print(rec.summary)
            print("Fontes sugeridas:")
            for source in rec.sources:
                print(f"  - {source.name}: {source.url}")
            print()

    # === Envio opcional por e-mail ===
    # Prioridade:
    # 1. Se RESEND_* estiver configurado, usa Resend.
    # 2. Caso contrário, tenta SMTP clássico (EMAIL_*).
    email_body_lines: List[str] = []
    email_body_lines.append("Resumo de treinos recentes (Hevy):")
    email_body_lines.append(
        df_volume_by_workout.to_string(index=False)
        if not df_volume_by_workout.empty
        else "Sem dados de treinos."
    )
    email_body_lines.append("\nVolume por grupamento muscular:")
    email_body_lines.append(
        df_volume_by_muscle.to_string(index=False)
        if not df_volume_by_muscle.empty
        else "Sem dados por grupamento."
    )

    if recommendations:
        email_body_lines.append("\nRecomendações (resumo):")
        for rec in recommendations:
            email_body_lines.append(f"[{rec.muscle_group}] {rec.summary}")

    email_body = "\n\n".join(email_body_lines)

    # Tenta Resend primeiro
    try:
        resend_cfg = ResendEmailConfig.from_env()
        resend_sender = ResendEmailSender(resend_cfg)
        resend_sender.send_email(
            to_address=resend_cfg.to_address,
            subject="PersonAI Trainer — Relatório recente de hipertrofia (Hevy)",
            body=email_body,
        )
        print(f"Relatório enviado por e-mail via Resend para {resend_cfg.to_address}.")
    except ValueError:
        # Configuração Resend ausente → tenta SMTP.
        try:
            email_cfg = EmailConfig.from_env()
            email_sender = SmtpEmailSender(email_cfg)
            email_sender.send_email(
                to_address=email_cfg.from_address,
                subject="PersonAI Trainer — Relatório recente de hipertrofia (Hevy)",
                body=email_body,
            )
            print(f"Relatório enviado por e-mail (SMTP) para {email_cfg.from_address}.")
        except ValueError:
            # Nenhuma configuração de e-mail disponível → apenas não envia.
            pass
        except RuntimeError as exc:
            print(str(exc))
    except RuntimeError as exc:
        print(str(exc))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())