# 🎓 Multi-Agent AI Academic Project Assistant

> **Production-level AI system for MCA Final Year Project**  
> Automates the full academic project lifecycle using RAG, LLMs, and a Multi-Agent Architecture.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-red)](https://streamlit.io)
[![FAISS](https://img.shields.io/badge/FAISS-Vector%20DB-green)](https://github.com/facebookresearch/faiss)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   Streamlit Frontend                    │
│              (frontend/app.py — Dark UI)               │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│               Agent Orchestrator                        │
│         (agents/orchestrator.py)                        │
│    Shared SessionMemory · Lazy Agent Loading            │
└──┬──────┬──────┬──────────┬──────────┬─────────────────┘
   │      │      │          │          │
   ▼      ▼      ▼          ▼          ▼
Topic   Docs   Code    Plagiarism    PPT
Agent  Agent  Agent    Agent       Agent
   │      │      │          │          │
   └──────┴──────┴────┬─────┴──────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                  Shared Services                        │
│   LLMClient (Gemini/OpenAI) · EmbeddingEngine (FAISS)  │
│   DocumentLoader · Logger · Config · Metrics           │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
AI Multi-Agent Academic Project Assistant/
│
├── app.py                          # Root launcher (streamlit run app.py)
├── requirements.txt                # All Python dependencies
├── .env.example                    # Environment variable template
│
├── agents/                         # 🤖 All AI agents
│   ├── __init__.py
│   ├── orchestrator.py             # Central coordinator + SessionMemory
│   ├── topic_agent.py              # Topic Suggestion Agent (RAG-grounded)
│   ├── documentation_agent.py      # IEEE-style report generator
│   ├── code_agent.py               # Python code generator
│   ├── plagiarism_agent.py         # Semantic similarity checker
│   └── ppt_agent.py                # Presentation slide generator + PPTX export
│
├── rag/                            # 🧠 RAG Pipeline
│   ├── __init__.py
│   ├── embedder.py                 # FAISS vector store + sentence-transformers
│   └── document_loader.py          # PDF/TXT/DOCX ingestion
│
├── utils/                          # 🔧 Shared Utilities
│   ├── __init__.py
│   ├── config.py                   # Typed settings from .env
│   ├── logger.py                   # Loguru structured logging
│   ├── llm_client.py               # Unified Gemini/OpenAI client (cached, retried)
│   ├── helpers.py                  # Text processing, JSON extraction
│   └── metrics.py                  # Documentation & code quality evaluator
│
├── frontend/                       # 🎨 Streamlit UI
│   └── app.py                      # Multi-step dark-themed application
│
├── scripts/                        # 🛠️ Utility scripts
│   └── build_index.py              # Rebuild FAISS index from documents
│
├── data/                           # 📚 Data storage
│   ├── documents/                  # 📄 Place your PDFs/TXTs here for RAG
│   │   ├── machine_learning_overview.txt
│   │   ├── nlp_overview.txt
│   │   └── computer_vision_overview.txt
│   ├── faiss_index/                # 🗄️ Auto-generated vector index
│   └── output/                     # 📥 Generated PPTX files
│
└── logs/                           # 📋 Auto-generated rotating log files
```

---

## ⚙️ Setup Instructions

### 1. Prerequisites

- Python 3.10 or higher
- A **Gemini API key** (free): https://aistudio.google.com/app/apikey  
  *(Or an OpenAI API key)*

### 2. Install Dependencies

```bash
cd "AI Multi-Agent Academic Project Assistant"
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy the example file
copy .env.example .env

# Edit .env with your API key
# Set GEMINI_API_KEY=your_actual_key_here
```

### 4. (Optional) Build RAG Index

Add your own PDF papers to `data/documents/`, then:

```bash
python scripts/build_index.py
```

### 5. Launch the Application

```bash
streamlit run frontend/app.py
```

Or use the root launcher:

```bash
python app.py
```

Open your browser at **http://localhost:8501**

---

## 🔁 Workflow

| Step | Agent | What It Does |
|------|-------|-------------|
| 1 | **Setup** | Configure API key + LLM provider |
| 2 | **Topic Agent** | Generates 5–10 RAG-grounded project topics |
| 3 | **Selection** | User picks a topic |
| 4 | **Documentation Agent** | Writes full IEEE-style report (8 sections) |
| 5 | **Code Agent** | Generates complete Python implementation |
| 6 | **Plagiarism Agent** | Checks semantic similarity against corpus |
| 7 | **PPT Agent** | Creates 10-slide presentation + exports .pptx |

---

## 🤖 Agent Details

### Topic Suggestion Agent
- Retrieves relevant academic context using FAISS vector search
- Prompts the LLM with user domain/interest/difficulty
- Returns structured JSON with title, description, technologies, expected outcome

### Documentation Agent
- Generates 8 independent sections using targeted prompts
- Follows IEEE academic paper format
- Each section: 300–700 words of substantive content
- Includes realistic references

### Code Generator Agent
- Produces complete, runnable Python code (not stubs)
- Temperature set to 0.4 for deterministic, correct code
- Includes docstrings, comments, error handling
- Generates technical explanation + file structure

### Plagiarism Checker Agent
- Chunks content into 400-char segments
- Queries FAISS index for top-1 match per chunk
- Aggregates chunk scores → overall similarity
- Thresholds: <20% Original, 20-40% Low, 40-60% Moderate, >60% High

### PPT Generator Agent
- Converts documentation sections to 10 structured slides
- Includes speaker notes
- Exports to real `.pptx` file using python-pptx
- Slide types: title, content, section, conclusion

---

## 📊 Evaluation Metrics

The system includes built-in quality evaluation (`utils/metrics.py`):

**Documentation Metrics:**
- Word count, section count, reference presence
- Flesch Reading Ease score
- Overall quality label

**Code Metrics:**
- Line count, function/class count
- Comment ratio (target >10%)
- Docstring and error handling presence

---

## 🧠 RAG Pipeline

```
Documents (PDF/TXT/DOCX)
        ↓
   Text Extraction
        ↓
  Chunking (500 chars, 50 overlap)
        ↓
  Embedding (sentence-transformers)
        ↓
   FAISS IndexFlatL2
        ↓
  Semantic Search (top-k)
        ↓
  Context → LLM Prompt
```

The FAISS index is persisted to `data/faiss_index/` and loaded automatically on startup.

---

## 🔧 Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `gemini` | `gemini` or `openai` |
| `GEMINI_API_KEY` | — | Your Google AI Studio key |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Model name (free-tier) |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | HuggingFace model |
| `CACHE_TTL` | `3600` | Response cache TTL (seconds) |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

---

## 🌟 Features for High Marks

- ✅ **Logging**: Loguru-based structured logging with file rotation
- ✅ **Error handling**: Try/except at every agent boundary + retries
- ✅ **Caching**: TTLCache (1hr) prevents redundant LLM calls
- ✅ **Evaluation metrics**: Doc quality + code quality scores
- ✅ **Modular architecture**: Each module independently testable
- ✅ **RAG pipeline**: Real FAISS + sentence-transformers
- ✅ **Multi-provider**: Switch Gemini ↔ OpenAI with one env var
- ✅ **Export**: Download report (.md) + slides (.pptx) + code (.py)

---

## 📋 Sample Outputs

### Topic Suggestions (example)
```json
{
  "title": "Sentiment Analysis of Movie Reviews using BERT Fine-tuning",
  "description": "Build a sentiment classifier trained on IMDb reviews...",
  "technologies": ["Python", "HuggingFace Transformers", "PyTorch"],
  "difficulty": "Intermediate",
  "expected_outcome": "Web app achieving 92%+ accuracy"
}
```

### Plagiarism Report (example)
```
Overall Similarity: 8.34% — Likely Original ✅
Verdict: Safe to submit
No significant matches found in the indexed corpus.
```

---

## 📄 License

MIT License — Free for academic and educational use.

---

*Built as a final-year MCA project demonstration — production-quality architecture, not a toy.*
