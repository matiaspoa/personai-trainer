"""
Dashboard Streamlit para análise de treinos do Hevy.

Este módulo implementa uma interface web para visualização de dados de treino,
incluindo volume por grupamento muscular, rankings de exercícios, evoluções
e chat com IA para recomendações personalizadas.
"""
from __future__ import annotations

import locale
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
from model_router import LiteLLMClient, ModelRouter
from processor import WorkoutProcessor
from recommendation_engine import RecommendationEngine
from user_profile import (
    BodyMeasurements,
    ExperienceLevel,
    TrainingGoal,
    UserProfile,
)
from workout_parser import WorkoutParser, RoutineConfig, format_routine_preview

load_dotenv()

# Tradução de exercícios (inglês -> português)
EXERCISE_PT = {
    # Peito
    "bench press": "Supino Reto",
    "incline bench press": "Supino Inclinado",
    "decline bench press": "Supino Declinado",
    "dumbbell bench press": "Supino com Halteres",
    "incline dumbbell press": "Supino Inclinado com Halteres",
    "chest press": "Chest Press",
    "chest fly": "Crucifixo",
    "cable fly": "Crucifixo no Cabo",
    "pec deck": "Pec Deck",
    "push up": "Flexão de Braço",
    "push-up": "Flexão de Braço",
    "dip": "Paralelas",
    "dips": "Paralelas",
    
    # Costas
    "lat pulldown": "Puxada Alta",
    "pull up": "Barra Fixa",
    "pull-up": "Barra Fixa",
    "chin up": "Barra Fixa Supinada",
    "chin-up": "Barra Fixa Supinada",
    "bent over row": "Remada Curvada",
    "barbell row": "Remada com Barra",
    "dumbbell row": "Remada Unilateral",
    "seated row": "Remada Sentada",
    "cable row": "Remada no Cabo",
    "t-bar row": "Remada Cavalinho",
    "deadlift": "Levantamento Terra",
    "romanian deadlift": "Stiff",
    "back extension": "Hiperextensão",
    
    # Ombros
    "shoulder press": "Desenvolvimento",
    "overhead press": "Desenvolvimento",
    "military press": "Desenvolvimento Militar",
    "dumbbell shoulder press": "Desenvolvimento com Halteres",
    "arnold press": "Arnold Press",
    "lateral raise": "Elevação Lateral",
    "front raise": "Elevação Frontal",
    "rear delt fly": "Crucifixo Invertido",
    "face pull": "Face Pull",
    "upright row": "Remada Alta",
    "shrug": "Encolhimento",
    "shrugs": "Encolhimento",
    
    # Bíceps
    "bicep curl": "Rosca Direta",
    "barbell curl": "Rosca com Barra",
    "dumbbell curl": "Rosca com Halteres",
    "hammer curl": "Rosca Martelo",
    "preacher curl": "Rosca Scott",
    "concentration curl": "Rosca Concentrada",
    "cable curl": "Rosca no Cabo",
    "incline curl": "Rosca Inclinada",
    
    # Tríceps
    "tricep pushdown": "Tríceps no Pulley",
    "tricep extension": "Extensão de Tríceps",
    "skull crusher": "Tríceps Testa",
    "overhead tricep extension": "Tríceps Francês",
    "close grip bench press": "Supino Pegada Fechada",
    "tricep dip": "Paralelas para Tríceps",
    "tricep kickback": "Tríceps Coice",
    
    # Pernas
    "squat": "Agachamento",
    "back squat": "Agachamento Livre",
    "front squat": "Agachamento Frontal",
    "leg press": "Leg Press",
    "leg extension": "Cadeira Extensora",
    "leg curl": "Mesa Flexora",
    "seated leg curl": "Cadeira Flexora",
    "lying leg curl": "Mesa Flexora",
    "lunges": "Avanço",
    "lunge": "Avanço",
    "walking lunge": "Avanço Caminhando",
    "bulgarian split squat": "Agachamento Búlgaro",
    "hack squat": "Hack Squat",
    "goblet squat": "Agachamento Goblet",
    "hip thrust": "Elevação de Quadril",
    "glute bridge": "Ponte de Glúteos",
    "hip abduction": "Abdução de Quadril",
    "hip adduction": "Adução de Quadril",
    "calf raise": "Elevação de Panturrilha",
    "seated calf raise": "Panturrilha Sentado",
    "standing calf raise": "Panturrilha em Pé",
    
    # Abdômen
    "crunch": "Abdominal",
    "sit up": "Abdominal",
    "sit-up": "Abdominal",
    "leg raise": "Elevação de Pernas",
    "hanging leg raise": "Elevação de Pernas na Barra",
    "plank": "Prancha",
    "russian twist": "Rotação Russa",
    "cable crunch": "Abdominal no Cabo",
    "ab wheel": "Roda Abdominal",
    "mountain climber": "Escalador",
    
    # Antebraços
    "wrist curl": "Rosca de Punho",
    "reverse wrist curl": "Rosca de Punho Invertida",
    "farmer walk": "Caminhada do Fazendeiro",
    "farmer's walk": "Caminhada do Fazendeiro",
    
    # Cardio
    "treadmill": "Esteira",
    "elliptical": "Elíptico",
    "cycling": "Bicicleta",
    "rowing": "Remo",
    "jump rope": "Pular Corda",
    "jumping jacks": "Polichinelo",
    "burpee": "Burpee",
    "burpees": "Burpees",
}

# Termos comuns para tradução parcial
EXERCISE_TERMS_PT = {
    "barbell": "Barra",
    "dumbbell": "Halter",
    "cable": "Cabo",
    "machine": "Máquina",
    "seated": "Sentado",
    "standing": "Em Pé",
    "lying": "Deitado",
    "incline": "Inclinado",
    "decline": "Declinado",
    "reverse": "Invertido",
    "single arm": "Unilateral",
    "single leg": "Unilateral",
    "close grip": "Pegada Fechada",
    "wide grip": "Pegada Aberta",
    "neutral grip": "Pegada Neutra",
    "overhand": "Pronada",
    "underhand": "Supinada",
}


def translate_exercise(exercise_name: str) -> str:
    """Traduz o nome do exercício para português."""
    if not exercise_name:
        return "Desconhecido"
    
    # Tenta tradução exata (case insensitive)
    name_lower = exercise_name.lower()
    
    # Remove termos de equipamento para busca
    for eng, pt in [("(barbell)", ""), ("(dumbbell)", ""), ("(cable)", ""), ("(machine)", ""), ("(barra)", "")]:
        name_lower = name_lower.replace(eng, "").strip()
    
    if name_lower in EXERCISE_PT:
        return EXERCISE_PT[name_lower]
    
    # Tenta buscar parcialmente
    for eng, pt in EXERCISE_PT.items():
        if eng in name_lower or name_lower in eng:
            return pt
    
    # Retorna o original se não encontrar tradução
    return exercise_name


# Tradução de grupos musculares (inglês -> português)
MUSCLE_GROUP_PT = {
    "chest": "Peito",
    "back": "Costas",
    "shoulders": "Ombros",
    "biceps": "Bíceps",
    "triceps": "Tríceps",
    "forearms": "Antebraços",
    "quadriceps": "Quadríceps",
    "hamstrings": "Posteriores",
    "glutes": "Glúteos",
    "calves": "Panturrilhas",
    "abs": "Abdômen",
    "abdominals": "Abdômen",
    "core": "Core",
    "traps": "Trapézio",
    "trapezius": "Trapézio",
    "lats": "Dorsais",
    "latissimus_dorsi": "Dorsais",
    "lower_back": "Lombar",
    "neck": "Pescoço",
    "full_body": "Corpo Inteiro",
    "cardio": "Cardio",
    "other": "Outros",
    # Variações comuns
    "legs": "Pernas",
    "arms": "Braços",
    "upper_back": "Costas Superior",
    "middle_back": "Costas Média",
    "obliques": "Oblíquos",
    "hip_flexors": "Flexores do Quadril",
    "adductors": "Adutores",
    "abductors": "Abdutores",
    # Mais variações da API Hevy
    "rear_delts": "Deltoides Posterior",
    "front_delts": "Deltoides Anterior",
    "side_delts": "Deltoides Lateral",
    "lateral_deltoid": "Deltoides Lateral",
    "anterior_deltoid": "Deltoides Anterior",
    "posterior_deltoid": "Deltoides Posterior",
    "rhomboids": "Romboides",
    "serratus": "Serrátil",
    "serratus_anterior": "Serrátil Anterior",
    "rotator_cuff": "Manguito Rotador",
    "erector_spinae": "Eretores da Espinha",
    "pectorals": "Peitorais",
    "pecs": "Peitorais",
    "delts": "Deltoides",
    "deltoids": "Deltoides",
    "quads": "Quadríceps",
    "hams": "Posteriores",
    "tibialis": "Tibial",
    "tibialis_anterior": "Tibial Anterior",
    "soleus": "Sóleo",
    "gastrocnemius": "Gastrocnêmio",
    "wrist_flexors": "Flexores do Punho",
    "wrist_extensors": "Extensores do Punho",
    "grip": "Pegada",
}

# Tradução de níveis de experiência
EXPERIENCE_LEVEL_PT = {
    "beginner": "Iniciante",
    "intermediate": "Intermediário",
    "advanced": "Avançado",
    "elite": "Elite",
}

# Tradução de objetivos
TRAINING_GOAL_PT = {
    "hypertrophy": "Hipertrofia",
    "strength": "Força",
    "endurance": "Resistência",
    "fat_loss": "Perda de Gordura",
    "maintenance": "Manutenção",
    "general_fitness": "Condicionamento Geral",
}

# Tradução de gênero
GENDER_PT = {
    "male": "Masculino",
    "female": "Feminino",
    "other": "Outro",
}


def translate_muscle_group(muscle_group: str) -> str:
    """Traduz o nome do grupo muscular para português."""
    if not muscle_group:
        return "Desconhecido"
    key = muscle_group.lower().replace(" ", "_")
    return MUSCLE_GROUP_PT.get(key, muscle_group.title())


def format_date_br(date_value) -> str:
    """Formata data para o padrão brasileiro DD/MM/YYYY."""
    if date_value is None:
        return ""
    if isinstance(date_value, str):
        try:
            date_value = pd.to_datetime(date_value)
        except:
            return date_value
    try:
        return date_value.strftime("%d/%m/%Y")
    except:
        return str(date_value)

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
def fetch_workouts(page_size: int = 10, max_pages: int = 50) -> List[Dict[str, Any]]:
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
        start_date = st.date_input("Início", value=default_start, max_value=today, format="DD/MM/YYYY")
    with col2:
        end_date = st.date_input("Fim", value=today, max_value=today, format="DD/MM/YYYY")
    
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
        
        # Gênero com labels em português
        gender_options = ["male", "female", "other"]
        gender_labels = [GENDER_PT[g] for g in gender_options]
        gender_index = gender_options.index(profile.gender) if profile.gender else 0
        selected_gender_label = st.selectbox("Gênero", options=gender_labels, index=gender_index)
        profile.gender = gender_options[gender_labels.index(selected_gender_label)]
        
        profile.body_fat_percentage = st.number_input(
            "Gordura corporal (%)",
            min_value=3.0,
            max_value=50.0,
            value=profile.body_fat_percentage or 15.0,
            step=0.5
        )
        
        # Nível de experiência com labels em português
        exp_options = [e.value for e in ExperienceLevel]
        exp_labels = [EXPERIENCE_LEVEL_PT[e] for e in exp_options]
        exp_index = exp_options.index(profile.experience_level.value)
        selected_exp_label = st.selectbox("Nível de experiência", options=exp_labels, index=exp_index)
        profile.experience_level = ExperienceLevel(exp_options[exp_labels.index(selected_exp_label)])
        
        # Objetivos com labels em português
        goals_options = [g.value for g in TrainingGoal]
        goals_labels = [TRAINING_GOAL_PT[g] for g in goals_options]
        current_goals_labels = [TRAINING_GOAL_PT[g.value] for g in profile.training_goals]
        selected_goals_labels = st.multiselect("Objetivos", options=goals_labels, default=current_goals_labels)
        profile.training_goals = [TrainingGoal(goals_options[goals_labels.index(label)]) for label in selected_goals_labels]
        
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
    
    # Traduz os nomes dos grupos musculares
    df["grupo_muscular"] = df["muscle_group"].apply(translate_muscle_group)
    df = df.sort_values("volume_total", ascending=False)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de barras
        fig_bar = px.bar(
            df,
            x="grupo_muscular",
            y="volume_total",
            color="volume_total",
            color_continuous_scale="Blues",
            title="Volume Total por Grupo Muscular",
            labels={"grupo_muscular": "Grupo Muscular", "volume_total": "Volume (kg)"}
        )
        fig_bar.update_layout(showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col2:
        # Gráfico de pizza
        fig_pie = px.pie(
            df,
            values="volume_total",
            names="grupo_muscular",
            title="Distribuição de Volume",
            hole=0.4
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # Tabela detalhada
    st.subheader("📋 Detalhes")
    df_display = df[["grupo_muscular", "volume_total", "sets_count"]].copy()
    df_display["volume_total"] = df_display["volume_total"].apply(lambda x: f"{x:,.0f} kg")
    df_display.columns = ["Grupo Muscular", "Volume Total", "Séries"]
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
    
    # Traduz grupos musculares e nomes de exercícios
    df["grupo_muscular"] = df["muscle_group"].apply(translate_muscle_group)
    df["exercicio"] = df["exercise_name"].apply(translate_exercise)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Gráfico de barras
        fig = px.bar(
            df,
            x="volume_total",
            y="exercicio",
            orientation="h",
            color="grupo_muscular",
            title=f"Top {top_n} Exercícios por Volume",
            labels={
                "exercicio": "Exercício",
                "volume_total": "Volume (kg)",
                "grupo_muscular": "Grupo Muscular"
            }
        )
        fig.update_layout(yaxis=dict(categoryorder="total ascending"))
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Tabela resumida
        df_display = df[["exercicio", "grupo_muscular", "volume_total", "times_performed"]].copy()
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
    fig_volume.update_xaxes(tickformat="%d/%m/%Y")
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
        fig_duration.update_xaxes(tickformat="%d/%m/%Y")
        st.plotly_chart(fig_duration, use_container_width=True)


def render_exercise_evolution_tab(processor: WorkoutProcessor) -> None:
    """Renderiza a aba de evolução de exercícios."""
    st.header("📊 Evolução dos Exercícios")
    
    df = processor.calculate_exercise_evolution(top_n=10)
    
    if df.empty:
        st.warning("Sem dados de evolução de exercícios.")
        return
    
    # Traduz nomes dos exercícios
    df["exercicio"] = df["exercise_name"].apply(translate_exercise)
    
    # Seletor de exercício (mostra traduzido)
    exercise_mapping = dict(zip(df["exercicio"], df["exercise_name"]))
    exercises_pt = df["exercicio"].unique().tolist()
    
    selected_exercises_pt = st.multiselect(
        "Selecione os exercícios para visualizar",
        options=exercises_pt,
        default=exercises_pt[:3] if len(exercises_pt) >= 3 else exercises_pt
    )
    
    if not selected_exercises_pt:
        st.info("Selecione pelo menos um exercício.")
        return
    
    # Filtra pelo nome original
    selected_originals = [exercise_mapping[ex] for ex in selected_exercises_pt]
    df_filtered = df[df["exercise_name"].isin(selected_originals)]
    
    # Gráfico de peso máximo
    fig_weight = px.line(
        df_filtered,
        x="date",
        y="max_weight",
        color="exercicio",
        markers=True,
        title="Evolução do Peso Máximo",
        labels={
            "date": "Data",
            "max_weight": "Peso Máximo (kg)",
            "exercicio": "Exercício"
        }
    )
    fig_weight.update_xaxes(tickformat="%d/%m/%Y")
    st.plotly_chart(fig_weight, use_container_width=True)
    
    # Gráfico de volume
    fig_volume = px.line(
        df_filtered,
        x="date",
        y="volume_total",
        color="exercicio",
        markers=True,
        title="Evolução do Volume por Sessão",
        labels={
            "date": "Data",
            "volume_total": "Volume (kg)",
            "exercicio": "Exercício"
        }
    )
    fig_volume.update_xaxes(tickformat="%d/%m/%Y")
    st.plotly_chart(fig_volume, use_container_width=True)


def detect_workout_suggestion(text: str) -> bool:
    """
    Detecta se o texto contém uma sugestão de treino estruturada.
    
    Procura por padrões como:
    - "Exercício: 3x10"
    - "Supino Reto - 4x8-12"
    - Listas de exercícios com séries/reps
    """
    import re
    
    # Padrões que indicam sugestão de treino
    patterns = [
        r"\d+\s*(?:x|×|X)\s*\d+",  # 3x10, 4x8
        r"séries?\s*(?:de|:)?\s*\d+",  # série de 3, séries: 4
        r"repeti[çc][õo]es?\s*(?:de|:)?\s*\d+",  # repetições de 10
        r"(?:supino|agachamento|leg press|remada|pulldown|desenvolvimento|rosca|tríceps|extensão|flexão)",  # nomes de exercícios
    ]
    
    matches = 0
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            matches += 1
    
    # Precisa ter pelo menos 2 padrões para considerar uma sugestão
    return matches >= 2


def render_save_routine_ui(
    response: str,
    exercise_templates: Dict[str, Any]
) -> None:
    """Renderiza UI para salvar rotina sugerida pela IA no Hevy."""
    
    # Inicializa parser com templates
    parser = WorkoutParser(exercise_templates=exercise_templates)
    
    # Tenta parsear a resposta
    routine = parser.parse(response)
    
    if not routine or not routine.exercises:
        st.info("💡 A IA sugeriu exercícios mas não foi possível extrair uma rotina estruturada.")
        return
    
    # Mostra preview da rotina
    st.markdown("---")
    st.subheader("📋 Rotina Detectada")
    
    # Preview da rotina
    preview = format_routine_preview(routine)
    st.code(preview, language=None)
    
    # Opções de edição
    with st.expander("✏️ Editar antes de salvar", expanded=False):
        new_title = st.text_input("Título da rotina:", value=routine.title)
        routine.title = new_title
        
        new_notes = st.text_area("Notas (opcional):", value=routine.notes or "")
        routine.notes = new_notes if new_notes else None
    
    # Mostra exercícios não encontrados
    missing_exercises = [
        ex.name for ex in routine.exercises 
        if not ex.exercise_template_id
    ]
    if missing_exercises:
        st.warning(
            f"⚠️ Exercícios sem correspondência no Hevy:\n" +
            "\n".join(f"- {name}" for name in missing_exercises)
        )
    
    # Botão para salvar
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("💾 Salvar no Hevy", type="primary"):
            try:
                client = get_hevy_client()
                if not client:
                    st.error("Cliente Hevy não configurado!")
                    return
                
                # Converte para formato da API
                routine_data = routine.to_api_format()
                
                # Cria a rotina usando os parâmetros corretos
                result = client.create_routine(
                    title=routine_data["title"],
                    exercises=routine_data["exercises"],
                    folder_id=routine_data.get("folder_id"),
                    notes=routine_data.get("notes")
                )
                
                st.success(f"✅ Rotina '{routine.title}' criada com sucesso!")
                st.json(result)
                
                # Limpa o estado de rotina pendente
                if "pending_routine" in st.session_state:
                    del st.session_state.pending_routine
                    
            except Exception as e:
                st.error(f"❌ Erro ao criar rotina: {e}")


def render_ai_chat_tab(
    profile: UserProfile,
    processor: WorkoutProcessor,
    df_volume_by_muscle: pd.DataFrame,
    workouts: list
) -> None:
    """Renderiza a aba de chat com IA."""
    st.header("🤖 Chat com Personal Trainer IA")
    
    # Inicializa o router de modelos com fallback
    try:
        router = ModelRouter()
        llm_client = LiteLLMClient(router)
        available_models = llm_client.available_models
        llm_available = len(available_models) > 0
    except Exception as e:
        llm_available = False
        available_models = []
    
    if not llm_available:
        st.warning(
            "Nenhum LLM configurado. Configure pelo menos uma das chaves no `.env`:\n"
            "- `GEMINI_API_KEY` (Google Gemini/Gemma)\n"
            "- `GROQ_API_KEY` (Groq Llama)\n"
            "- `OPENAI_API_KEY` (OpenAI GPT)"
        )
        return
    
    # Mostra modelos disponíveis
    with st.expander("🔧 Modelos disponíveis", expanded=False):
        for model in available_models:
            st.text(f"✅ {model}")
    
    # Carrega templates de exercícios para o parser
    exercise_templates = fetch_exercise_templates()
    
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
            muscle_pt = translate_muscle_group(row['muscle_group'])
            workout_context += f"- {muscle_pt}: {row['volume_total']:,.0f} kg\n"
    
    # Lista detalhada de todos os treinos
    if workouts:
        # Ordena por data
        sorted_workouts = sorted(workouts, key=lambda w: w.get("start_time", ""))
        
        workout_context += "\n=== LISTA DE TODOS OS TREINOS ===\n"
        
        # Primeiro treino
        first = sorted_workouts[0]
        first_date = first.get("start_time", "")[:10] if first.get("start_time") else "N/A"
        workout_context += f"\n📅 PRIMEIRO TREINO: {first.get('title', 'Sem nome')} em {format_date_br(first_date)}\n"
        
        # Último treino
        last = sorted_workouts[-1]
        last_date = last.get("start_time", "")[:10] if last.get("start_time") else "N/A"
        workout_context += f"📅 ÚLTIMO TREINO: {last.get('title', 'Sem nome')} em {format_date_br(last_date)}\n"
        
        # Limita a 20 treinos mais recentes para não estourar contexto
        recent_workouts = sorted_workouts[-20:] if len(sorted_workouts) > 20 else sorted_workouts
        workout_context += f"\n--- Últimos {len(recent_workouts)} treinos (de {len(sorted_workouts)} total) ---\n"
        for w in recent_workouts:
            w_date = w.get("start_time", "")[:10] if w.get("start_time") else "N/A"
            w_title = w.get("title", "Sem nome")
            
            # Calcula volume do treino
            volume = 0
            exercises_count = 0
            for ex in w.get("exercises", []):
                exercises_count += 1
                for s in ex.get("sets", []):
                    weight = s.get("weight_kg") or 0
                    reps = s.get("reps") or 0
                    volume += weight * reps
            
            workout_context += f"- {format_date_br(w_date)}: {w_title} | {volume:,.0f}kg | {exercises_count} exercícios\n"
    
    # Histórico de chat
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    
    # Exibe histórico com botões de salvar para respostas com treinos
    for idx, message in enumerate(st.session_state.chat_messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Se for resposta da IA e contiver sugestão de treino, mostra opção de salvar
            if message["role"] == "assistant" and detect_workout_suggestion(message["content"]):
                if st.button(f"📋 Extrair e salvar rotina", key=f"save_routine_{idx}"):
                    st.session_state.pending_routine = message["content"]
                    st.rerun()
    
    # Se há uma rotina pendente para salvar, mostra a UI
    if "pending_routine" in st.session_state:
        render_save_routine_ui(
            st.session_state.pending_routine,
            exercise_templates
        )
    
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
Você tem acesso ao histórico COMPLETO de treinos do usuário no período selecionado, incluindo datas, nomes dos treinos, volumes e exercícios realizados.

IMPORTANTE: Quando sugerir treinos, use este formato para facilitar a extração:
- Nome do Exercício: Séries x Repetições (peso opcional)
Exemplo:
- Supino Reto: 4x8-12
- Agachamento: 4x6-8
- Remada Curvada: 3x10-12
"""
        
        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                try:
                    response = llm_client.generate_text(
                        prompt=prompt,
                        system_prompt=system_prompt
                    )
                    st.markdown(response)
                    
                    # Mostra qual modelo foi usado
                    if llm_client.last_model_used:
                        st.caption(f"_Modelo: {llm_client.last_model_used}_")
                    
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": response
                    })
                    
                    # Se a resposta contém sugestão de treino, mostra botão
                    if detect_workout_suggestion(response):
                        st.info("💡 Detectei uma sugestão de treino! Clique no botão acima para extrair e salvar no Hevy.")
                        
                except Exception as e:
                    error_msg = f"Erro ao gerar resposta: {e}"
                    st.error(error_msg)
    
    # Botão para limpar histórico
    if st.session_state.chat_messages:
        if st.button("🗑️ Limpar histórico"):
            st.session_state.chat_messages = []
            if "pending_routine" in st.session_state:
                del st.session_state.pending_routine
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
    
    # Tenta usar LiteLLM Router com fallback
    try:
        router = ModelRouter()
        llm_client = LiteLLMClient(router)
        if not llm_client.available_models:
            llm_client = None
    except Exception:
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
        muscle_pt = translate_muscle_group(rec.muscle_group)
        with st.expander(f"💪 {muscle_pt}", expanded=True):
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
            render_ai_chat_tab(profile, processor, pd.DataFrame(), [])
        return
    
    # Cria processador
    processor = WorkoutProcessor(workouts, hevy_client=client, exercise_templates=templates)
    
    # Calcula volume por músculo (usado em várias abas)
    df_volume_by_muscle = processor.calculate_volume_by_muscle_group()
    
    # Lista de abas
    tab_names = [
        "📊 Visão Geral",
        "💪 Grupamentos",
        "🏆 Top Treinos",
        "🎯 Top Exercícios",
        "📈 Evolução Treinos",
        "📊 Evolução Exercícios",
        "💡 Recomendações",
        "🤖 Chat IA"
    ]
    
    # Usa session_state para manter a aba do Chat IA ativa após enviar mensagem
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = 0
    
    # Seleciona a aba via radio na sidebar para persistir
    st.sidebar.markdown("---")
    st.sidebar.subheader("🗂️ Navegação")
    selected_tab = st.sidebar.radio(
        "Selecione a aba:",
        options=range(len(tab_names)),
        format_func=lambda x: tab_names[x],
        index=st.session_state.active_tab,
        key="tab_selector"
    )
    st.session_state.active_tab = selected_tab
    
    # Renderiza apenas a aba selecionada
    st.markdown(f"## {tab_names[selected_tab]}")
    
    if selected_tab == 0:
        render_overview_tab(processor, workouts)
    elif selected_tab == 1:
        render_muscle_groups_tab(processor)
    elif selected_tab == 2:
        render_top_workouts_tab(processor)
    elif selected_tab == 3:
        render_top_exercises_tab(processor)
    elif selected_tab == 4:
        render_workout_evolution_tab(processor)
    elif selected_tab == 5:
        render_exercise_evolution_tab(processor)
    elif selected_tab == 6:
        render_recommendations_tab(processor, df_volume_by_muscle)
    elif selected_tab == 7:
        render_ai_chat_tab(profile, processor, df_volume_by_muscle, workouts)


if __name__ == "__main__":
    main()
