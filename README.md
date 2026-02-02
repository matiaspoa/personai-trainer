# 🏋️ PersonAI Trainer

**PersonAI Trainer** is an automated personal training assistant that analyzes your workout data from the Hevy app and provides AI-powered training recommendations based on scientific evidence. Get insights into your training volume, muscle group distribution, exercise performance, and personalized recommendations to optimize your fitness journey.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.x](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/downloads/)

---

## ✨ Features

### 📊 Dual Interface
- **CLI Mode**: Command-line reports for quick analysis and automation
- **Dashboard Mode**: Interactive web-based dashboard with real-time charts

### 📈 Comprehensive Analytics
- **Total Volume Tracking**: Monitor your overall training volume over time
- **Muscle Group Analysis**: Detailed breakdown of volume per muscle group
- **Top Exercises & Workouts**: Rankings by volume and performance
- **Progression Tracking**: Visualize weight and volume evolution for each exercise
- **Workout Evolution**: Track trends over time by workout type

### 🤖 AI-Powered Recommendations
- Science-based training recommendations using GPT-4 or Google Gemini
- Personalized suggestions based on your:
  - Training history and patterns
  - User profile (weight, height, measurements)
  - Training goals (hypertrophy, strength, endurance)
  - Experience level
- Curated knowledge base from trusted sources (ExRx, Stronger By Science)

### 💬 Interactive AI Chat
- Real-time chat with your personal trainer AI
- Context-aware responses based on your workout data
- Get instant answers to training questions

### 📧 Automated Reports
- Email delivery via Resend API or SMTP
- Customizable report frequency

---

## 🚀 Getting Started

### Prerequisites

- Python 3.x
- A [Hevy](https://www.hevyapp.com/) account with workout data
- Hevy API key ([get one here](https://hevyapp.com/developer))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/matiaspoa/personai-trainer.git
   cd personai-trainer
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   
   Create a `.env` file in the root directory:
   ```env
   # Required: Hevy API
   HEVY_API_KEY="your_hevy_api_key_here"
   
   # Optional: LLM Provider (for AI recommendations)
   LLM_PROVIDER="gemini"  # Options: "gemini" or "openai"
   LLM_API_KEY="your_llm_api_key_here"
   LLM_MODEL="gemini-2.0-flash-exp"  # or "gpt-4o-mini" for OpenAI
   
   # Optional: Resend Email Service
   RESEND_API_KEY="your_resend_api_key"
   RESEND_FROM="Your Name <you@yourdomain.com>"
   RESEND_TO="recipient@example.com"
   
   # Optional: SMTP Email (fallback)
   EMAIL_SMTP_HOST="smtp.example.com"
   EMAIL_SMTP_PORT="587"
   EMAIL_USERNAME="your_username"
   EMAIL_PASSWORD="your_password"
   EMAIL_FROM="you@example.com"
   ```

---

## 💻 Usage

### CLI Mode

Run the command-line interface for quick reports:

```bash
python src/main.py
```

**Available options:**
- `--page`: Page number for Hevy API (default: 1)
- `--page-size`: Number of workouts per page (default: 10)
- `--top-n`: Number of items in rankings (default: 5)

**Example:**
```bash
python src/main.py --page 1 --page-size 20 --top-n 10
```

### Dashboard Mode

Launch the interactive web dashboard:

```bash
streamlit run src/dashboard.py
```

The dashboard will automatically open in your browser at `http://localhost:8501`

#### Dashboard Features

- **📅 Period Selector**: Filter workouts by custom date ranges
- **👤 User Profile**: Configure personal information
  - Body measurements (weight, height, body fat %)
  - Training goals (hypertrophy, strength, endurance, general fitness)
  - Experience level (beginner, intermediate, advanced, elite)
- **📊 Overview**: Summary statistics
  - Total workouts
  - Total volume (kg)
  - Unique exercises
  - Training frequency
- **💪 Muscle Groups**: Visual analysis
  - Volume distribution by muscle group (bar & pie charts)
  - Interactive charts with drill-down capabilities
- **🏆 Top Workouts**: Ranked by total volume
- **🎯 Top Exercises**: Performance leaders
- **📈 Workout Evolution**: Track progress over time
  - Volume trends by workout type
  - Duration analysis
- **📊 Exercise Evolution**: Individual exercise tracking
  - Maximum weight progression
  - Volume trends
- **💡 AI Recommendations**: Science-based training advice
- **🤖 Chat IA**: Interactive conversation with your AI trainer
  - Context-aware based on your profile
  - Real-time responses
  - Training tips and guidance

---

## 🧪 Testing

Run the test suite:

```bash
pytest tests/
```

With verbose output:
```bash
pytest tests/ -v
```

Run specific test files:
```bash
pytest tests/test_client.py -v
pytest tests/test_processor.py -v
pytest tests/test_user_profile.py -v
```

---

## 📁 Project Structure

```
personai-trainer/
├── src/                          # Source code
│   ├── main.py                   # CLI entry point
│   ├── dashboard.py              # Streamlit web dashboard
│   ├── client.py                 # Hevy API client
│   ├── processor.py              # Workout data processing
│   ├── recommendation_engine.py  # AI recommendation logic
│   ├── llm_service.py            # LLM integration (OpenAI/Gemini)
│   ├── model_router.py           # Multi-model routing with LiteLLM
│   ├── knowledge_base.py         # Scientific sources database
│   ├── user_profile.py           # User profile management
│   ├── email_service.py          # Email delivery (Resend/SMTP)
│   └── workout_parser.py         # Workout parsing utilities
├── tests/                        # Unit tests
│   ├── test_client.py
│   ├── test_processor.py
│   ├── test_user_profile.py
│   └── test_workout_parser.py
├── data/                         # User data (auto-created, gitignored)
│   └── user_profile.json
├── requirements.txt              # Python dependencies
├── .env                          # Environment variables (create this)
├── .gitignore
├── LICENSE                       # MIT License
└── README.md                     # This file
```

---

## 🛠️ Technologies

- **Language**: Python 3.x
- **Data Processing**: pandas, numpy
- **API Integration**: requests, python-dotenv
- **Web Dashboard**: Streamlit, Plotly
- **AI/LLM**: LiteLLM (OpenAI, Google Gemini)
- **Email**: Resend API, SMTP
- **Testing**: pytest

### Key APIs
- **Hevy API**: Workout data retrieval
- **OpenAI/Gemini**: AI-powered recommendations
- **Resend**: Email delivery service

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Make your changes
4. Run tests to ensure nothing breaks (`pytest tests/`)
5. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
6. Push to the branch (`git push origin feature/AmazingFeature`)
7. Open a Pull Request

### Code Style
- Follow PEP 8 guidelines
- Use type hints for function parameters and return values
- Add docstrings to functions and classes
- Write unit tests for new features

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Hevy](https://www.hevyapp.com/) for providing the workout tracking API
- [ExRx.net](https://exrx.net/) for exercise science resources
- [Stronger By Science](https://www.strongerbyscience.com/) for evidence-based training research

---

## 📧 Support

For issues, questions, or suggestions, please [open an issue](https://github.com/matiaspoa/personai-trainer/issues) on GitHub.

---

**Made with 💪 for fitness enthusiasts who love data**
