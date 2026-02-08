GenAI SQL Assistant


⚡ Overview

The GenAI SQL Assistant is a next-generation bridge between human curiosity and structured data. By leveraging high-performance Generative AI, this tool allows users to bypass complex SQL syntax and converse with their databases in plain English.

- Natural Language to SQL: Instantly transform business questions into precise code.
- Live Data Execution: Fetch real-time query results from structured databases.
- Intelligent Insights: Receive automated business recommendations based on the data trends.
- Conversational History: A sleek interface to track your data journey.


Live Application
[https://genai-sql-assistant.streamlit.app/]


Neural Architecture

User Question
   ↓
Prompt + Schema → OpenAIx
   ↓
Generated SQL
   ↓
SQLite Engine
   ↓
Results + Insights
   ↓
Streamlit UI

Tech Stack & Structure

genai-sql-assistant/
│
├── app.py                      # Streamlit UI
├── src/
│   └── genai_sql_engine.py     # Core GenAI + SQL logic
│
├── data/
│   └── csv/                    # Source CSV files 
│
├── requirements.txt            # Python dependencies
├── .gitignore                  # Excludes DB, secrets
└── README.md                   # Project documentation

Tech Stack

- Frontend: Streamlit
- Backend: Python
- Database: SQLite (auto-generated)
- AI Model: OpenAI (GPT-based)
- Data Handling: Pandas
- Deployment: Streamlit Cloud
- Version Control: Git & GitHub

Project Anatomy

- app.py: The heart of the Streamlit UI.
- src/genai_sql_engine.py: The core GenAI engine logic.
- data/csv: Secure storage for source data files.
- requirements.txt: Environment dependencies.

Security by Design

- Read-Only Access: The system is strictly prohibited from altering data.
- Query Governance: Built-in session limits to prevent resource exhaustion.
- Automated DB Management: The SQLite database is created dynamically at runtime and never committed to version control, ensuring data integrity.
- Secrets Management: Secure handling of API keys for production environments.


Launching the Assistant

Local Execution

1. Clone the Repository: git clone [your-repo-link].
2. Environment Setup: Install necessary dependencies via pip install -r requirements.txt.
3. Authentication: Configure your OpenAI API key.
4. Launch: Execute streamlit run app.py to start the local server.

Cloud Deployment

- Sync your project with GitHub.
- Connect to Streamlit Cloud for instant global access.
- Inject your API key into Streamlit Secrets for secure cloud operations.

Future Enhancements
- SQL edit mode
- Query result download (CSV)
- Multi-user authentication
- Cloud database integration
- Analytics dashboards




