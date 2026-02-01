# AGENTS.md

This document outlines essential information for agents working in this codebase.

## 1. Project Overview

This project is a Python application designed for personal fitness data analysis and AI-powered training recommendations. It interacts with the Hevy API to fetch workout data, processes it to calculate metrics like total workout volume and volume per muscle group, and generates science-based training recommendations using LLMs (OpenAI or Google Gemini).
We'll have a dashboard where we can see the evolution and we set the period to fetch the API data.  

## 2. Project Type and Technologies

*   **Language:** Python 3.x
*   **Key Libraries:** 
    - `requests` (for API interactions with Hevy, LLM providers, and email services)
    - `pandas` (for data processing and analysis)
    - `python-dotenv` (for environment variable management)
    - `resend` (for email delivery via Resend API)
*   **APIs:**
    - Hevy API (`https://api.hevyapp.com/v1`) — workout data
    - OpenAI/Gemini API — AI-powered recommendations
    - Resend API — email delivery

## 3. Code Organization and Structure

The codebase is organized as follows:

*   `.`: Root directory containing `requirements.txt`, `LICENSE`, `README.md`, `AGENTS.md`, and the `src/` and `tests/` directories.
*   `src/`: Contains the core Python application logic.
    *   `src/main.py`: Entry point and orchestrator. Fetches workouts, processes data, generates recommendations, and sends email reports.
    *   `src/client.py`: Defines the `HevyClient` class for all Hevy API interactions (fetching workouts, exercise templates, routines).
    *   `src/processor.py`: Defines the `WorkoutProcessor` class for data manipulation with `pandas` DataFrames (total volume, volume by muscle group, volume evolution).
    *   `src/recommendation_engine.py`: Defines `RecommendationEngine` class that generates AI-powered or deterministic training recommendations based on workout data and scientific sources.
    *   `src/llm_service.py`: Defines `LlmConfig` and `OpenAiLikeClient` for calling LLM providers (OpenAI, Google Gemini) to generate text.
    *   `src/knowledge_base.py`: Defines `ScienceKnowledgeBase` with curated scientific sources (ExRx, Stronger By Science) for each muscle group.
    *   `src/email_service.py`: Defines email sending capabilities via SMTP (`SmtpEmailSender`) and Resend API (`ResendEmailSender`).
*   `tests/`: Contains unit tests.
    *   `tests/test_client.py`: Unit tests for `HevyClient` with mocked API responses.
    *   `tests/test_processor.py`: Unit tests for `WorkoutProcessor` calculations.

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

To run the main application:

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
