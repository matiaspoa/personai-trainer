# AGENTS.md

This document outlines essential information for agents working in this codebase.

## 1. Project Overview

This project is a Python application designed for personal fitness data analysis and AI-powered training recommendations. It interacts with the Hevy API to fetch workout data, processes it to calculate metrics like total workout volume and volume per muscle group, and generates science-based training recommendations using LLMs (OpenAI or Google Gemini).

**The application has two interfaces:**
- **CLI Mode:** Command-line reports via `main.py`
- **Dashboard Mode:** Web-based interactive dashboard via `dashboard.py` (Streamlit)

## 2. Project Type and Technologies

*   **Language:** Python 3.x
*   **Key Libraries:** 
    - `requests` (for API interactions with Hevy, LLM providers, and email services)
    - `pandas` (for data processing and analysis)
    - `python-dotenv` (for environment variable management)
    - `resend` (for email delivery via Resend API)
    - `streamlit` (for web dashboard UI)
    - `plotly` (for interactive charts)
*   **APIs:**
    - Hevy API (`https://api.hevyapp.com/v1`) — workout data
    - OpenAI/Gemini API — AI-powered recommendations
    - Resend API — email delivery

## 3. Code Organization and Structure

The codebase is organized as follows:

*   `.`: Root directory containing `requirements.txt`, `LICENSE`, `README.md`, `AGENTS.md`, and the `src/` and `tests/` directories.
*   `src/`: Contains the core Python application logic.
    *   `src/main.py`: CLI entry point and orchestrator. Fetches workouts, processes data, generates recommendations, and sends email reports.
    *   `src/dashboard.py`: **Streamlit dashboard** with interactive charts, period selector, and LLM chat interface.
    *   `src/client.py`: Defines the `HevyClient` class for all Hevy API interactions (fetching workouts, exercise templates, routines).
    *   `src/processor.py`: Defines the `WorkoutProcessor` class for data manipulation with `pandas` DataFrames (total volume, volume by muscle group, volume evolution, top exercises, etc.).
    *   `src/user_profile.py`: Defines `UserProfile`, `BodyMeasurements`, `TrainingGoal`, and `ExperienceLevel` for storing user data and generating LLM context.
    *   `src/recommendation_engine.py`: Defines `RecommendationEngine` class that generates AI-powered or deterministic training recommendations based on workout data and scientific sources.
    *   `src/llm_service.py`: Defines `LlmConfig` and `OpenAiLikeClient` for calling LLM providers (OpenAI, Google Gemini) to generate text.
    *   `src/knowledge_base.py`: Defines `ScienceKnowledgeBase` with curated scientific sources (ExRx, Stronger By Science) for each muscle group.
    *   `src/email_service.py`: Defines email sending capabilities via SMTP (`SmtpEmailSender`) and Resend API (`ResendEmailSender`).
*   `tests/`: Contains unit tests.
    *   `tests/test_client.py`: Unit tests for `HevyClient` with mocked API responses.
    *   `tests/test_processor.py`: Unit tests for `WorkoutProcessor` calculations.
    *   `tests/test_user_profile.py`: Unit tests for `UserProfile` serialization and BMI calculation.
*   `data/`: User data directory (auto-created).
    *   `data/user_profile.json`: Saved user profile (not committed to git).

## 4. Essential Commands

### 4.1. Setup

To set up the project locally:

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Environment Variables:**
    Create a `.env` file in the root directory with the following variables:
    
    ```env
    # Required: Hevy API
    HEVY_API_KEY="YOUR_HEVY_API_KEY"
    
    # Optional: LLM Provider (for AI recommendations)
    LLM_PROVIDER="gemini"  # or "openai"
    LLM_API_KEY="YOUR_LLM_API_KEY"
    LLM_MODEL="gemini-2.5-flash"  # or "gpt-4.1-mini" for OpenAI
    
    # Optional: Resend Email (preferred)
    RESEND_API_KEY="YOUR_RESEND_API_KEY"
    RESEND_FROM="Your Name <you@your-domain.com>"
    RESEND_TO="recipient@example.com"
    
    # Optional: SMTP Email (fallback)
    EMAIL_SMTP_HOST="smtp.example.com"
    EMAIL_SMTP_PORT="587"
    EMAIL_USERNAME="your_username"
    EMAIL_PASSWORD="your_password"
    EMAIL_FROM="you@example.com"
    ```

### 4.2. Running

#### CLI Mode
To run the command-line application:

```bash
python src/main.py
```

Command-line arguments:
- `--page`: Page number for the Hevy API /workouts endpoint (default: 1)
- `--page-size`: Number of workouts per page (default: 10)
- `--top-n`: Number of items to display in rankings (default: 5)

Example:
```bash
python src/main.py --page 1 --page-size 20 --top-n 10
```

#### Dashboard Mode
To run the Streamlit dashboard:

```bash
streamlit run src/dashboard.py
```

The dashboard will open in your browser at `http://localhost:8501`.

**Dashboard Features:**
- 📅 **Period Selector:** Filter workouts by date range
- 👤 **User Profile:** Configure weight, height, body measurements, goals
- 📊 **Overview:** Summary statistics (total workouts, volume, exercises)
- 💪 **Muscle Groups:** Volume by muscle group (bar chart + pie chart)
- 🏆 **Top Workouts:** Top 10 workouts ranked by volume
- 🎯 **Top Exercises:** Top 10 exercises ranked by volume
- 📈 **Workout Evolution:** Track volume/duration over time by workout type
- 📊 **Exercise Evolution:** Track max weight/volume over time for exercises
- 💡 **Recommendations:** AI-generated training recommendations
- 🤖 **Chat IA:** Interactive chat with personal trainer AI (uses user profile as context)

### 4.3. Testing

Run tests using `pytest`:

```bash
pytest tests/
```

Or with verbose output:
```bash
pytest tests/ -v
```

## 5. Coding Conventions and Style

*   **Naming Conventions:**
    *   Classes: CapWords (e.g., `HevyClient`, `WorkoutProcessor`, `RecommendationEngine`)
    *   Functions and variables: snake_case (e.g., `get_recent_workouts`, `total_volume`)
    *   Constants: UPPER_SNAKE_CASE (e.g., `HEVY_API_KEY`)
*   **Code Formatting:** Follows standard PEP 8 guidelines.
*   **Docstrings:** Functions and classes should have clear docstrings explaining their purpose, arguments, and return values.
*   **Type Hints:** Use type hints for function parameters and return values (see `from __future__ import annotations`).

## 6. Important Gotchas and Patterns

*   **API Key Management:** API keys (HEVY_API_KEY, LLM_API_KEY, RESEND_API_KEY) must be set in a `.env` file at the project root. Never commit secrets.
*   **Data Processing with Pandas:** The `WorkoutProcessor` heavily relies on `pandas` DataFrames. Agents should be familiar with `pandas` operations.
*   **Exercise Template Cache:** The `WorkoutProcessor` includes a `_exercise_template_cache` to minimize redundant API calls.
*   **Error Handling:** 
    - API errors use `response.raise_for_status()` and are wrapped in `RuntimeError`.
    - Configuration errors raise `ValueError`.
    - Secrets are never included in error messages.
*   **Graceful Degradation:**
    - If LLM configuration is missing, the app generates deterministic recommendations.
    - If email configuration is missing, the app skips email sending without failing.
*   **LLM Provider Flexibility:** Supports both OpenAI and Google Gemini APIs via `LLM_PROVIDER` environment variable.
