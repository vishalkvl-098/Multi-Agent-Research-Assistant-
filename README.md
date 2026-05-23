 copy
# 🤖 Multi-Agent Research Assistant

> Orchestrate multiple AI agents that search, fact-check, and write —
> delivering polished research reports on any topic, automatically.

![Python](https://img.shields.io/badge/python-3.11+-blue)
![Claude](https://img.shields.io/badge/powered%20by-Claude%20API-orange)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 📖 Overview

Multi-Agent Research Assistant is a pipeline of specialized AI agents,
each with a distinct role. You give it a topic — it gives you a
structured, cited research report.

| Agent          | Role                                              |
|----------------|---------------------------------------------------|
| 🔍 Researcher  | Searches the web and gathers raw information      |
| ✅ Fact-Checker | Validates claims, flags inconsistencies           |
| ✍️ Writer      | Synthesizes verified info into a polished report  |
| 🎯 Orchestrator| Coordinates agents, manages workflow and retries  |

---

## 🚀 Demo

```bash
$ python main.py --topic "Impact of AI on healthcare in 2024"

[Orchestrator] Starting research pipeline...
[Researcher]   Searching: "AI healthcare 2024 breakthroughs"...
[Researcher]   Searching: "AI diagnostics clinical trials 2024"...
[Fact-Checker] Verifying 12 claims from researcher output...
[Fact-Checker] 11 verified ✅  1 flagged ⚠️  (removed)
[Writer]       Drafting introduction...
[Writer]       Drafting 4 sections with citations...
[Orchestrator] Report complete! Saved → reports/ai_healthcare_2024.md

✅ Done in 42s | 3 agents | 6 sources | 1,240 words
```

---

## 🏗️ Architecture

```
User Input (topic)
       │
       ▼
 ┌─────────────┐
 │ Orchestrator │  ← manages state, retries, flow
 └──────┬──────┘
        │
   ┌────┴────┐
   │         │
   ▼         ▼
Researcher  (parallel if multiple subtopics)
   │
   ▼
Fact-Checker  ← validates each claim
   │
   ▼
  Writer  ← produces final markdown report
   │
   ▼
 Output (Markdown / PDF / JSON)
```

Each agent is a self-contained class powered by Claude via the
Anthropic API. They communicate through a shared `ResearchContext`
dataclass — no shared global state.

---

## 📦 Installation

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/multi-agent-research-assistant.git
cd multi-agent-research-assistant
```

### 2. Set up a virtual environment

```bash
python -m venv venv
source venv/bin/activate       # macOS/Linux
venv\Scripts\activate          # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your API key

```bash
cp .env.example .env
# Edit .env and add your Anthropic API key
```

---

## ⚙️ Usage

### Basic

```bash
python main.py --topic "Quantum computing applications in 2025"
```

### With options

```bash
python main.py \
  --topic "Climate tech startups in Southeast Asia" \
  --depth deep \
  --format pdf \
  --output reports/
```

### As a Python library

```python
from src.orchestrator import ResearchOrchestrator

orchestrator = ResearchOrchestrator()
report = orchestrator.run("Future of remote work post-2025")
print(report.markdown)
```

### CLI flags

| Flag         | Default    | Description                              |
|--------------|------------|------------------------------------------|
| `--topic`    | required   | Research topic or question               |
| `--depth`    | `standard` | `quick` / `standard` / `deep`            |
| `--format`   | `markdown` | `markdown` / `pdf` / `json`              |
| `--output`   | `reports/` | Output directory                         |
| `--model`    | sonnet     | Claude model to use                      |
| `--verbose`  | False      | Print agent reasoning steps              |

---

## 🧠 How Each Agent Works

### 🔍 Researcher Agent
- Receives the topic and breaks it into sub-queries
- Uses Claude's `web_search` tool to fetch live results
- Returns a list of raw findings with source URLs

### ✅ Fact-Checker Agent
- Takes the researcher's raw findings as input
- Validates each claim against multiple sources
- Removes or flags unverified/contradictory claims
- Returns a cleaned, annotated list of verified facts

### ✍️ Writer Agent
- Receives verified facts and source metadata
- Structures content: intro → body sections → conclusion
- Adds inline citations and a references section
- Outputs polished Markdown (optionally converted to PDF)

### 🎯 Orchestrator
- Manages the full pipeline end-to-end
- Passes context between agents via `ResearchContext`
- Handles retries on agent failure
- Logs timing and token usage per agent

---

## 📁 Project Structure

```
multi-agent-research-assistant/
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── researcher.py       # Web search + info gathering
│   │   ├── fact_checker.py     # Claim validation
│   │   ├── writer.py           # Report generation
│   │   └── base_agent.py       # Shared base class
│   ├── orchestrator.py         # Pipeline coordinator
│   ├── context.py              # ResearchContext dataclass
│   └── utils/
│       ├── markdown_to_pdf.py  # Optional PDF export
│       └── logger.py           # Colored logging
├── reports/                    # Generated reports (gitignored)
├── tests/
│   ├── test_researcher.py
│   ├── test_fact_checker.py
│   └── test_writer.py
├── main.py                     # CLI entry point
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🔧 Configuration

In `.env`:

```env
ANTHROPIC_API_KEY=sk-ant-...

# Optional
RESEARCH_MODEL=claude-sonnet-4-20250514
MAX_SEARCH_RESULTS=10
MAX_RETRIES=3
OUTPUT_DIR=reports/
```

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

---

## 🛣️ Roadmap

- [x] Core 3-agent pipeline (Researcher → Fact-Checker → Writer)
- [x] CLI interface
- [x] Markdown output
- [ ] PDF export
- [ ] Parallel sub-topic research
- [ ] Vector store memory (persist research sessions)
- [ ] Streamlit / Gradio web UI
- [ ] Slack / Notion export integration
- [ ] Custom agent plugins

---

## 🤝 Contributing

Pull requests are welcome! For major changes, open an issue first.

1. Fork the repo
2. Create a branch: `git checkout -b feature/your-feature`
3. Commit: `git commit -m "add: your feature"`
4. Push: `git push origin feature/your-feature`
5. Open a PR

---

## 📄 License

MIT © 2025 — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgements

Built with [Anthropic Claude API](https://docs.anthropic.com).
Inspired by multi-agent frameworks like LangGraph and AutoGen.
