"""
Dashboard Streamlit para análise de treinos do Hevy.

Este módulo implementa uma interface web para visualização de dados de treino,
incluindo volume por grupamento muscular, rankings de exercícios, evoluções
e chat com IA para recomendações personalizadas.
"""
from __future__ import annotations

import os
import sys
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

# Adiciona o diretório src ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from client import HevyClient
from knowledge_base import ScienceKnowledgeBase
from llm_service import LlmConfig, OpenAiLikeClient
from processor import WorkoutProcessor
from recommendation_engine import RecommendationEngine
from user_profile import (
    BodyMeasurements,
    ExperienceLevel,
    TrainingGoal,
    UserProfile,
)

load_dotenv()

# Configuração da página
st.set_page_config(
    page_title="PersonAI Trainer",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Caminho para salvar o perfil do usuário
PROFILE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "user_profile.json"
)


def get_hevy_client() -> Optional[HevyClient]:
    """Obtém o cliente Hevy, retorna None se não configurado."""
    try:
        return HevyClient()
    except ValueError:
        return None


@st.cache_data(ttl=300)  # Cache por 5 minutos
def fetch_workouts(page_size: int = 50, max_pages: int = 10) -> List[Dict[str, Any]]:
    """Busca treinos do Hevy com cache."""
    client = get_hevy_client()
    if not client:
        return []
    
    all_workouts = []
    for page in range(1, max_pages + 1):
        workouts = client.get_recent_workouts(page=page, page_size=page_size)
        if not workouts:
            break
        all_workouts.extend(workouts)
        if len(workouts) < page_size:
            break
    return all_workouts


@st.cache_data(ttl=3600)  # Cache por 1 hora
def fetch_exercise_templates() -> Dict[str, Dict[str, Any]]:
    """Busca todos os templates de exercícios com cache."""
    client = get_hevy_client()
    if not client:
        return {}
    return client.get_all_exercise_templates()


def filter_workouts_by_date(
    workouts: List[Dict[str, Any]],
    start_date: date,
    end_date: date
) -> List[Dict[str, Any]]:
    """Filtra treinos por período de datas."""
    filtered = []
    for workout in workouts:
        workout_date_str = workout.get("start_time") or workout.get("created_at")
        if not workout_date_str:
            continue
        try:
            workout_date = pd.to_datetime(workout_date_str).date()
            if start_date <= workout_date <= end_date:
                filtered.append(workout)
        except:
            continue
    return filtered


def load_user_profile() -> UserProfile:
    """Carrega ou cria o perfil do usuário."""
    return UserProfile.load_or_create(PROFILE_PATH)


def save_user_profile(profile: UserProfile) -> None:
    """Salva o perfil do usuário."""
    profile.save_to_file(PROFILE_PATH)


def render_sidebar() -> Tuple[date, date, UserProfile]:
    """Renderiza a sidebar com filtros e perfil do usuário."""
    st.sidebar.title("🏋️ PersonAI Trainer")
    
    # Seletor de período
    st.sidebar.header("📅 Período")
    
    today = date.today()
    default_start = today - timedelta(days=90)
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input("Início", value=default_start, max_value=today)
    with col2:
        end_date = st.date_input("Fim", value=today, max_value=today)
    
    if start_date > end_date:
        st.sidebar.error("Data inicial deve ser anterior à data final.")
        start_date = end_date
    
    # Perfil do usuário
    st.sidebar.header("👤 Meu Perfil")
    profile = load_user_profile()
    
    with st.sidebar.expander("Editar Perfil", expanded=False):
        profile.name = st.text_input("Nome", value=profile.name)
        profile.weight_kg = st.number_input(
            "Peso (kg)", 
            min_value=30.0, 
            max_value=300.0, 
            value=profile.weight_kg or 70.0,
            step=0.5
        )
        profile.height_cm = st.number_input(
            "Altura (cm)", 
            min_value=100.0, 
            max_value=250.0, 
            value=profile.height_cm or 170.0,
            step=1.0
        )
        profile.age = st.number_input(
            "Idade", 
            min_value=10, 
            max_value=100, 
            value=profile.age or 30
        )
        profile.gender = st.selectbox(
            "Gênero",
            options=["male", "female", "other"],
            index=["male", "female", "other"].index(profile.gender) if profile.gender else 0
        )
        profile.body_fat_percentage = st.number_input(
            "Gordura corporal (%)",
            min_value=3.0,
            max_value=50.0,
            value=profile.body_fat_percentage or 15.0,
            step=0.5
        )
        profile.experience_level = ExperienceLevel(
            st.selectbox(
                "Nível de experiência",
                options=[e.value for e in ExperienceLevel],
                index=[e.value for e in ExperienceLevel].index(profile.experience_level.value)
            )
        )
        
        goals_options = [g.value for g in TrainingGoal]
        selected_goals = st.multiselect(
            "Objetivos",
            options=goals_options,
            default=[g.value for g in profile.training_goals]
        )
        profile.training_goals = [TrainingGoal(g) for g in selected_goals]
        
        injuries_text = st.text_area(
            "Lesões/Limitações (uma por linha)",
            value="\n".join(profile.injuries)
        )
        profile.injuries = [i.strip() for i in injuries_text.split("\n") if i.strip()]
        
        profile.notes = st.text_area("Observações", value=profile.notes)
        
        if st.button("💾 Salvar Perfil"):
            save_user_profile(profile)
            st.success("Perfil salvo!")
    
    # Exibe resumo do perfil
    if profile.weight_kg and profile.height_cm:
        st.sidebar.metric("IMC", f"{profile.bmi}", profile.bmi_category)
    
    return start_date, end_date, profile


def render_overview_tab(
    processor: WorkoutProcessor,
    workouts: List[Dict[str, Any]]
) -> None:
    """Renderiza a aba de visão geral."""
    st.header("📊 Visão Geral")
    
    if not workouts:
        st.warning("Nenhum treino encontrado no período selecionado.")
        return
    
    # Estatísticas resumidas
    stats = processor.get_summary_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total de Treinos", stats["total_workouts"])
    with col2:
        st.metric("Volume Total", f"{stats['total_volume']:,.0f} kg")
    with col3:
        st.metric("Total de Exercícios", stats["total_exercises"])
    with col4:
        st.metric("Total de Séries", stats["total_sets"])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Volume Médio/Treino", f"{stats['avg_volume_per_workout']:,.0f} kg")
    with col2:
        st.metric("Exercícios/Treino", f"{stats['avg_exercises_per_workout']:.1f}")
    with col3:
        st.metric("Séries/Treino", f"{stats['avg_sets_per_workout']:.1f}")


def render_muscle_groups_tab(processor: WorkoutProcessor) -> None:
    """Renderiza a aba de volume por grupamento muscular."""
    st.header("💪 Volume por Grupamento Muscular")
    
    df = processor.calculate_volume_by_muscle_group()
    
    if df.empty:
        st.warning("Sem dados de volume por grupamento muscular.")
        return
    
    df = df.sort_values("volume_total", ascending=False)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de barras
        fig_bar = px.bar(
            df,
            x="muscle_group",
            y="volume_total",
            color="volume_total",
            color_continuous_scale="Blues",
            title="Volume Total por Grupo Muscular",
            labels={"muscle_group": "Grupo Muscular", "volume_total": "Volume (kg)"}
        )
        fig_bar.update_layout(showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col2:
        # Gráfico de pizza
        fig_pie = px.pie(
            df,
            values="volume_total",
            names="muscle_group",
            title="Distribuição de Volume",
            hole=0.4
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # Tabela detalhada
    st.subheader("📋 Detalhes")
    df_display = df.copy()
    df_display["volume_total"] = df_display["volume_total"].apply(lambda x: f"{x:,.0f} kg")
    st.dataframe(df_display, use_container_width=True, hide_index=True)


def render_top_workouts_tab(processor: WorkoutProcessor, top_n: int = 10) -> None:
    """Renderiza a aba de top treinos."""
    st.header("🏆 Top Treinos por Volume")
    
    df = processor.calculate_total_volume()
    
    if df.empty:
        st.warning("Sem dados de treinos.")
        return
    
    df = df.sort_values("volume_total", ascending=False).head(top_n).reset_index(drop=True)
    
    # Gráfico de barras horizontais
    fig = px.bar(
        df,
        x="volume_total",
        y="title",
        orientation="h",
        color="volume_total",
        color_continuous_scale="Viridis",
        title=f"Top {top_n} Treinos por Volume",
        labels={"title": "Treino", "volume_total": "Volume (kg)"}
    )
    fig.update_layout(yaxis=dict(categoryorder="total ascending"), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabela
    df_display = df[["title", "date", "volume_total"]].copy()
    df_display["date"] = pd.to_datetime(df_display["date"]).dt.strftime("%d/%m/%Y")
    df_display["volume_total"] = df_display["volume_total"].apply(lambda x: f"{x:,.0f} kg")
    df_display.columns = ["Treino", "Data", "Volume"]
    st.dataframe(df_display, use_container_width=True, hide_index=True)


def render_top_exercises_tab(processor: WorkoutProcessor, top_n: int = 10) -> None:
    """Renderiza a aba de top exercícios."""
    st.header("🎯 Top Exercícios por Volume")
    
    df = processor.calculate_top_exercises(top_n=top_n)
    
    if df.empty:
        st.warning("Sem dados de exercícios.")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Gráfico de barras
        fig = px.bar(
            df,
            x="volume_total",
            y="exercise_name",
            orientation="h",
            color="muscle_group",
            title=f"Top {top_n} Exercícios por Volume",
            labels={
                "exercise_name": "Exercício",
                "volume_total": "Volume (kg)",
                "muscle_group": "Grupo Muscular"
            }
        )
        fig.update_layout(yaxis=dict(categoryorder="total ascending"))
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Tabela resumida
        df_display = df[["exercise_name", "muscle_group", "volume_total", "times_performed"]].copy()
        df_display["volume_total"] = df_display["volume_total"].apply(lambda x: f"{x:,.0f}")
        df_display.columns = ["Exercício", "Grupo", "Volume (kg)", "Frequência"]
        st.dataframe(df_display, use_container_width=True, hide_index=True)


def render_workout_evolution_tab(processor: WorkoutProcessor) -> None:
    """Renderiza a aba de evolução de treinos."""
    st.header("📈 Evolução dos Treinos")
    
    df = processor.calculate_workout_evolution(top_n=10)
    
    if df.empty:
        st.warning("Sem dados de evolução de treinos.")
        return
    
    # Gráfico de linha - volume ao longo do tempo
    fig_volume = px.line(
        df,
        x="date",
        y="volume_total",
        color="workout_title",
        markers=True,
        title="Evolução do Volume por Tipo de Treino",
        labels={
            "date": "Data",
            "volume_total": "Volume (kg)",
            "workout_title": "Treino"
        }
    )
    st.plotly_chart(fig_volume, use_container_width=True)
    
    # Se tiver duração, mostra também
    if "duration_minutes" in df.columns and df["duration_minutes"].notna().any():
        fig_duration = px.line(
            df.dropna(subset=["duration_minutes"]),
            x="date",
            y="duration_minutes",
            color="workout_title",
            markers=True,
            title="Evolução da Duração por Tipo de Treino",
            labels={
                "date": "Data",
                "duration_minutes": "Duração (min)",
                "workout_title": "Treino"
            }
        )
        st.plotly_chart(fig_duration, use_container_width=True)


def render_exercise_evolution_tab(processor: WorkoutProcessor) -> None:
    """Renderiza a aba de evolução de exercícios."""
    st.header("📊 Evolução dos Exercícios")
    
    df = processor.calculate_exercise_evolution(top_n=10)
    
    if df.empty:
        st.warning("Sem dados de evolução de exercícios.")
        return
    
    # Seletor de exercício
    exercises = df["exercise_name"].unique().tolist()
    selected_exercises = st.multiselect(
        "Selecione os exercícios para visualizar",
        options=exercises,
        default=exercises[:3] if len(exercises) >= 3 else exercises
    )
    
    if not selected_exercises:
        st.info("Selecione pelo menos um exercício.")
        return
    
    df_filtered = df[df["exercise_name"].isin(selected_exercises)]
    
    # Gráfico de peso máximo
    fig_weight = px.line(
        df_filtered,
        x="date",
        y="max_weight",
        color="exercise_name",
        markers=True,
        title="Evolução do Peso Máximo",
        labels={
            "date": "Data",
            "max_weight": "Peso Máximo (kg)",
            "exercise_name": "Exercício"
        }
    )
    st.plotly_chart(fig_weight, use_container_width=True)
    
    # Gráfico de volume
    fig_volume = px.line(
        df_filtered,
        x="date",
        y="volume_total",
        color="exercise_name",
        markers=True,
        title="Evolução do Volume por Sessão",
        labels={
            "date": "Data",
            "volume_total": "Volume (kg)",
            "exercise_name": "Exercício"
        }
    )
    st.plotly_chart(fig_volume, use_container_width=True)


def render_ai_chat_tab(
    profile: UserProfile,
    processor: WorkoutProcessor,
    df_volume_by_muscle: pd.DataFrame
) -> None:
    """Renderiza a aba de chat com IA."""
    st.header("🤖 Chat com Personal Trainer IA")
    
    # Verifica configuração do LLM
    try:
        llm_cfg = LlmConfig.from_env()
        llm_client = OpenAiLikeClient(llm_cfg)
        llm_available = True
    except ValueError:
        llm_available = False
    
    if not llm_available:
        st.warning(
            "LLM não configurado. Configure as variáveis de ambiente:\n"
            "- LLM_PROVIDER (openai ou gemini)\n"
            "- LLM_API_KEY\n"
            "- LLM_MODEL"
        )
        return
    
    # Contexto para o chat
    profile_context = profile.get_context_for_llm()
    
    # Resumo dos dados de treino
    stats = processor.get_summary_stats()
    workout_context = f"""
=== DADOS DE TREINO DO PERÍODO ===
Total de treinos: {stats['total_workouts']}
Volume total: {stats['total_volume']:,.0f} kg
Exercícios realizados: {stats['total_exercises']}
Séries realizadas: {stats['total_sets']}
Volume médio por treino: {stats['avg_volume_per_workout']:,.0f} kg
"""
    
    if not df_volume_by_muscle.empty:
        top_muscles = df_volume_by_muscle.nlargest(5, "volume_total")
        workout_context += "\nTop grupamentos musculares por volume:\n"
        for _, row in top_muscles.iterrows():
            workout_context += f"- {row['muscle_group']}: {row['volume_total']:,.0f} kg\n"
    
    # Histórico de chat
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    
    # Exibe histórico
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Input do usuário
    if prompt := st.chat_input("Faça uma pergunta sobre seus treinos..."):
        # Adiciona mensagem do usuário
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Gera resposta
        system_prompt = f"""Você é um personal trainer especializado em hipertrofia e musculação.
Use os dados do usuário e seus treinos para dar recomendações personalizadas e baseadas em evidência científica.

{profile_context}

{workout_context}

Responda de forma clara, objetiva e sempre justifique suas recomendações com base científica quando possível.
Se não tiver certeza de algo, seja honesto sobre isso.
"""
        
        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                try:
                    response = llm_client.generate(
                        system_prompt=system_prompt,
                        user_prompt=prompt,
                        max_tokens=1024
                    )
                    st.markdown(response)
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": response
                    })
                except Exception as e:
                    error_msg = f"Erro ao gerar resposta: {e}"
                    st.error(error_msg)
    
    # Botão para limpar histórico
    if st.session_state.chat_messages:
        if st.button("🗑️ Limpar histórico"):
            st.session_state.chat_messages = []
            st.rerun()


def render_recommendations_tab(
    processor: WorkoutProcessor,
    df_volume_by_muscle: pd.DataFrame
) -> None:
    """Renderiza a aba de recomendações automáticas."""
    st.header("💡 Recomendações de Treino")
    
    if df_volume_by_muscle.empty:
        st.warning("Sem dados suficientes para gerar recomendações.")
        return
    
    kb = ScienceKnowledgeBase()
    
    # Tenta usar LLM, senão usa modo determinístico
    try:
        llm_cfg = LlmConfig.from_env()
        llm_client = OpenAiLikeClient(llm_cfg)
    except ValueError:
        llm_client = None
    
    rec_engine = RecommendationEngine(knowledge_base=kb, llm_client=llm_client)
    
    with st.spinner("Gerando recomendações..."):
        try:
            recommendations = rec_engine.recommend_for_top_muscle_groups(
                df_volume_by_muscle=df_volume_by_muscle,
                top_n=3
            )
        except Exception as e:
            st.error(f"Erro ao gerar recomendações: {e}")
            # Tenta modo determinístico
            rec_engine = RecommendationEngine(knowledge_base=kb, llm_client=None)
            recommendations = rec_engine.recommend_for_top_muscle_groups(
                df_volume_by_muscle=df_volume_by_muscle,
                top_n=3
            )
    
    if not recommendations:
        st.info("Nenhuma recomendação disponível no momento.")
        return
    
    for rec in recommendations:
        with st.expander(f"💪 {rec.muscle_group}", expanded=True):
            st.markdown(rec.summary)
            
            if rec.sources:
                st.markdown("**📚 Fontes:**")
                for source in rec.sources:
                    st.markdown(f"- [{source.name}]({source.url})")


def main():
    """Função principal do dashboard."""
    # Renderiza sidebar e obtém filtros
    start_date, end_date, profile = render_sidebar()
    
    # Verifica se a API está configurada
    client = get_hevy_client()
    if not client:
        st.error(
            "⚠️ **API do Hevy não configurada**\n\n"
            "Configure a variável de ambiente `HEVY_API_KEY` no arquivo `.env`"
        )
        st.stop()
    
    # Busca dados
    with st.spinner("Carregando treinos..."):
        all_workouts = fetch_workouts()
        templates = fetch_exercise_templates()
    
    # Filtra por período
    workouts = filter_workouts_by_date(all_workouts, start_date, end_date)
    
    if not workouts:
        st.warning(
            f"Nenhum treino encontrado entre {start_date.strftime('%d/%m/%Y')} "
            f"e {end_date.strftime('%d/%m/%Y')}."
        )
        # Ainda permite acessar o chat
        tabs = st.tabs(["🤖 Chat IA"])
        with tabs[0]:
            processor = WorkoutProcessor([], exercise_templates=templates)
            render_ai_chat_tab(profile, processor, pd.DataFrame())
        return
    
    # Cria processador
    processor = WorkoutProcessor(workouts, hevy_client=client, exercise_templates=templates)
    
    # Calcula volume por músculo (usado em várias abas)
    df_volume_by_muscle = processor.calculate_volume_by_muscle_group()
    
    # Abas
    tabs = st.tabs([
        "📊 Visão Geral",
        "💪 Grupamentos",
        "🏆 Top Treinos",
        "🎯 Top Exercícios",
        "📈 Evolução Treinos",
        "📊 Evolução Exercícios",
        "💡 Recomendações",
        "🤖 Chat IA"
    ])
    
    with tabs[0]:
        render_overview_tab(processor, workouts)
    
    with tabs[1]:
        render_muscle_groups_tab(processor)
    
    with tabs[2]:
        render_top_workouts_tab(processor)
    
    with tabs[3]:
        render_top_exercises_tab(processor)
    
    with tabs[4]:
        render_workout_evolution_tab(processor)
    
    with tabs[5]:
        render_exercise_evolution_tab(processor)
    
    with tabs[6]:
        render_recommendations_tab(processor, df_volume_by_muscle)
    
    with tabs[7]:
        render_ai_chat_tab(profile, processor, df_volume_by_muscle)


if __name__ == "__main__":
    main()
