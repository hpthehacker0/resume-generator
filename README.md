# 📄 Resume + Cover Letter Generator (Multi-Agent System)

## 📖 Overview

An AI-powered pipeline that rewrites, aligns, and enhances career documents based on job requirements. Provide a raw resume and a target job description — the system's multi-agent architecture takes care of the rest, generating an ATS-optimized resume and a personalized cover letter.

---

## ✨ Features

- **Job Analyzer Agent** — Extracts structured intelligence from job descriptions: required skills, preferred skills, keywords, and company tone.
- **Resume Optimizer Agent** — Rewrites the original resume to match job requirements, naturally inserts missing keywords, and improves the overall ATS score.
- **Cover Letter Writer Agent** — Generates a concise, 3–5 paragraph personalized cover letter that matches the company tone and connects user skills to job needs.
- **State Orchestration** — An orchestration layer acts as a controller that manages agents, passes outputs between them, and maintains context state.

---

## 🎥 Video Demo


https://github.com/user-attachments/assets/c2e0e188-9121-4ee8-8b44-0d0968c8a68f


---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | Python, FastAPI |
| Agent Framework | LangGraph & LangChain |
| Local LLM | Ollama (`gpt-oss:120b-cloud`) |
| Storage | PostgreSQL |
| State Management | LangGraph `MemorySaver` (configurable to Redis) |

---

## 🚀 Getting Started

### 1. Prerequisites

- Python 3.9+
- PostgreSQL installed and running
- [Ollama](https://ollama.com/) installed

---

### 2. Database Setup

Log into your PostgreSQL shell and run the following:

```bash
psql -U postgres
```

```sql
CREATE DATABASE resumedb;

\c resumedb

CREATE TABLE career_documents (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    optimized_resume TEXT NOT NULL,
    cover_letter TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 3. Local LLM Setup

Ensure your Ollama instance is running and pull the required model:

```bash
ollama run gpt-oss:120b-cloud
```

---

### 4. Backend Setup (FastAPI)

Install the required dependencies:

```bash
pip install fastapi uvicorn langgraph langchain-ollama pydantic asyncpg
```

Update the PostgreSQL connection string in `main.py` with your credentials:

```python
conn = await asyncpg.connect('postgresql://user:password@localhost/resumedb')
```

Start the FastAPI server:

```bash
uvicorn main:app --reload
```

The backend will be available at `http://localhost:8000`.

---

### 5. Frontend Setup (Streamlit)

Open a new terminal and install the frontend dependencies:

```bash
pip install streamlit requests
```

Run the Streamlit application:

```bash
streamlit run app.py
```

The frontend will be accessible at `http://localhost:8501`.

---

## 🧠 System Architecture & Workflow

The system uses a **Context Passing Strategy** — each agent reads from a shared context object, writes back to it, and never works in isolation.

```
User Input (Resume + Job Description)
            │
            ▼
    ┌───────────────┐
    │ Job Analyzer  │ → Structured JSON (skills, keywords, tone)
    └───────┬───────┘
            │
            ▼
    ┌──────────────────┐
    │ Resume Optimizer │ → ATS-Optimized Resume
    └────────┬─────────┘
             │
             ▼
    ┌─────────────────────┐
    │ Cover Letter Writer │ → Personalized Cover Letter
    └──────────┬──────────┘
               │
               ▼
         PostgreSQL DB
               │
               ▼
     Final Output + ATS Score
```

### Pipeline Steps

1. **User Input** — Raw resume + job description submitted via Streamlit UI.
2. **Job Analyzer** — Reads the JD and outputs structured JSON with required skills, preferred skills, keywords, and company tone.
3. **Resume Optimizer** — Reads the original resume + JSON context and outputs an ATS-optimized resume.
4. **Cover Letter Writer** — Reads the optimized resume + JSON context and outputs the final cover letter.
5. **Database** — Final outputs are saved to PostgreSQL.
6. **Final Output** — Formatted resume, cover letter, and ATS score improvement are returned to the user.

---

## 📁 Project Structure

```
resume-generator/
├── main.py              # FastAPI backend & agent orchestration
├── app.py               # Streamlit frontend
└── README.md
```

---

## 🔧 Configuration

| Variable | Description | Default |
|---|---|---|
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` |
| `DB_URL` | PostgreSQL connection string | `postgresql://user:password@localhost/resumedb` |
| `BACKEND_URL` | FastAPI server URL | `http://localhost:8000` |

---

## 📌 Notes

- **State Management** — `LangGraph MemorySaver` is used by default for local development. For distributed or production deployments, swap it out for a Redis-backed checkpointer.
- **ATS Scoring** — The Resume Optimizer agent reports a relative improvement score based on keyword coverage before and after optimization.
- **Model** — The system is configured to use `gpt-oss:120b-cloud` via Ollama. Swap the model name in `main.py` to use any other Ollama-compatible model.
