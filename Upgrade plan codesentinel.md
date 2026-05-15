# 🛡️ CodeSentinel
### AI-Powered Static Application Security Testing (SAST) Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-Python-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-TypeScript-black?style=flat-square&logo=next.js)](https://nextjs.org)
[![Tree-sitter](https://img.shields.io/badge/Tree--sitter-AST_Parsing-orange?style=flat-square)](https://tree-sitter.github.io)
[![LangChain](https://img.shields.io/badge/LangChain-Groq-purple?style=flat-square)](https://langchain.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker)](https://docker.com)
[![Redis](https://img.shields.io/badge/Redis-Celery-DC382D?style=flat-square&logo=redis)](https://redis.io)

A full-stack security analysis platform that combines **AST-based static analysis**, **AI-driven exploit generation**, and **automated patch + PR creation** to find, prove, and fix vulnerabilities in source code — autonomously.

[Features](#-features) · [What Makes This Unique](#-what-makes-this-unique) · [Architecture](#-architecture) · [Upgrades Roadmap](#-upgrades--what-was-improved) · [Quick Start](#-quick-start) · [How It Works](#-how-it-works)

---

## ✨ Features

| Category | What's Included |
|---|---|
| 🔍 **AST Scanning** | Tree-sitter language-aware parsing — no regex, real syntax trees |
| 🔗 **Chain Detection** | Multi-step vulnerability chains (e.g. path traversal → secret leak) |
| 💥 **PoC Generation** | LLM red agent generates working exploit code per vulnerability |
| 🩹 **Auto-Patching** | LLM blue agent writes a fix and opens a GitHub PR automatically |
| 🕵️ **Secret Excavation** | Scans full git history for accidentally committed credentials |
| ⚙️ **CI/CD Integration** | GitHub Actions workflow included — scans on every push |
| 📊 **Dashboard** | Next.js UI with scan history, severity breakdown, and diff viewer |
| 🐳 **Docker** | Full Docker Compose stack — spin up in one command |

---

## 🌟 What Makes This Unique

Most student security projects either (a) wrap an existing tool like Bandit/Semgrep, or (b) do simple regex pattern matching. CodeSentinel does neither.

### 1. Tree-sitter AST Parsing (Same Approach as Semgrep)
CodeSentinel parses source code into Abstract Syntax Trees using Tree-sitter — the same library that powers GitHub's code intelligence, Neovim's syntax highlighting, and Semgrep's analysis engine. This means:
- No false positives from strings that look like code
- Context-aware detection (e.g., `exec(user_input)` vs `exec("ls")`)
- Multi-language support without writing separate parsers

### 2. Vulnerability Chain Detection
Single-rule scanners miss chained vulnerabilities — where exploit A enables exploit B. CodeSentinel maps data flow between flagged nodes to detect multi-step attack paths:
```
path_traversal(filename) → open(filename) → read() → response
       ↑ chain: user controls path → reads arbitrary file → exfiltrates data
```

### 3. Red Agent Validates Every Finding (No False Positive PRs)
After detection, a LangChain red agent attempts to generate a working PoC. If the exploit fails validation, the finding is downgraded — preventing the blue agent from opening PRs for false positives. This red-validates-before-blue design is what separates CodeSentinel from tools that just dump findings.

### 4. Git History Secret Excavation
CodeSentinel doesn't just scan the current state — it walks the full git reflog looking for secrets (API keys, tokens, passwords) that were committed and later deleted. Deleted secrets are still exploitable if the attacker has a git clone.

### 5. End-to-End Autonomy: Detect → Prove → Fix → PR
No other student project in this space closes the loop fully. CodeSentinel goes from raw source code to an open GitHub PR with a validated patch — no human in the loop required.

---

## 🆕 Upgrades & What Was Improved

### Core Improvements

| Area | Upgrade |
|---|---|
| False positive rate | Red agent PoC validation before any patch is generated |
| Scan speed | Celery + Redis async job queue — scans don't block the API |
| Language coverage | Added Go and Java parsers alongside Python/JavaScript |
| Secret detection | Extended regex patterns for AWS, GCP, Azure, Stripe, Twilio tokens |
| Reporting | SARIF export format — importable into GitHub Advanced Security |

### New Features Added

- **🔴 Severity scoring** — CVSS-inspired 0–10 score per finding with justification
- **📜 SARIF export** — upload results directly to GitHub Security tab
- **🔁 Incremental scans** — only re-scan changed files on subsequent runs (git diff aware)
- **📁 Multi-repo support** — scan multiple repos from one dashboard
- **🗂️ Finding suppression** — mark false positives; suppressed in future scans
- **📧 Slack/email alerts** — notify on critical findings via webhook

### Planned Next Upgrades

- [ ] **Fine-tuned detection model** — replace zero-shot LLM with a model fine-tuned on CVE data
- [ ] **Dependency scanning** — check `requirements.txt`, `package.json`, `go.mod` against CVE databases
- [ ] **DAST integration** — dynamic scan mode using a sandboxed runtime
- [ ] **VS Code extension** — inline vulnerability highlighting during development
- [ ] **Unit test suite** — pytest for scanner rules, mock LLM for agent tests

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Next.js Dashboard                   │
│  Scan · Results · Chain View · Diff Viewer · History │
└──────────────────────┬──────────────────────────────┘
                       │ REST API
┌──────────────────────▼──────────────────────────────┐
│                FastAPI Backend                       │
│  Scan Router · Job Queue · Agent Orchestrator        │
└────────┬──────────────────────────┬─────────────────┘
         │                          │
┌────────▼──────────┐    ┌──────────▼────────────────┐
│  Celery Workers   │    │  Agent Pipeline            │
│  (Redis broker)   │    │  Tree-sitter → Chain Map   │
│  Async scan jobs  │    │  → Red Agent (PoC)         │
└───────────────────┘    │  → Blue Agent (Patch + PR) │
                         └───────────────────────────┘
```

### Scan Pipeline
```
Source Code
     │
     ▼
Tree-sitter AST Parse
     │
     ▼
Rule Engine (vulnerability patterns on AST nodes)
     │
     ▼
Data Flow Analysis → Chain Detection
     │
     ▼
Red Agent → PoC generation → validate exploit
     │
     ├── PoC fails → downgrade to "informational"
     │
     └── PoC passes → Blue Agent → write patch → open PR
```

---

## 📁 Project Structure

```
codesentinel/
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── routers/
│   │   ├── scan.py             # Scan endpoints
│   │   └── reports.py          # SARIF export, history
│   ├── scanner/
│   │   ├── ast_parser.py       # Tree-sitter parsing
│   │   ├── rule_engine.py      # Vulnerability rules on AST
│   │   ├── chain_detector.py   # Multi-step chain analysis
│   │   └── secret_excavator.py # Git history secret scanning
│   ├── agents/
│   │   ├── red_agent.py        # LangChain exploit generator
│   │   └── blue_agent.py       # LangChain patch + PR agent
│   ├── tasks/
│   │   └── celery_tasks.py     # Async scan job definitions
│   └── models/
│       └── findings.py         # SQLAlchemy finding schema
│
├── frontend/                   # Next.js + TypeScript
│   └── src/
│       ├── pages/
│       ├── components/
│       └── lib/api.ts
│
├── .github/
│   └── workflows/
│       └── codesentinel.yml    # GitHub Actions CI scan
│
├── docker-compose.yml
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- Docker + Docker Compose
- GitHub token (for PR creation)
- Groq API key (LLM inference)

### 1 · Clone & Configure
```bash
git clone https://github.com/NITHINKR06/codesentinel.git
cd codesentinel
cp .env.example .env
```

```env
# .env
GROQ_API_KEY=your_groq_api_key
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_REPO=owner/repo-to-scan
DATABASE_URL=sqlite:///./codesentinel.db
REDIS_URL=redis://redis:6379/0
```

### 2 · Launch with Docker Compose
```bash
docker compose up --build
```

| Service | URL |
|---|---|
| Dashboard | http://localhost:3000 |
| API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

### 3 · Scan a Repository
```bash
# Via API
curl -X POST http://localhost:8000/scan \
  -H "Content-Type: application/json" \
  -d '{"repo_path": "/path/to/target", "languages": ["python", "javascript"]}'

# Or submit from the dashboard UI
```

---

## 🔍 How It Works

### Detection Example
```python
# CodeSentinel flags this via AST rule on subprocess.call with user input:
user_cmd = request.args.get("cmd")
subprocess.call(user_cmd, shell=True)          # ← flagged: command injection

# Red agent generates PoC:
# GET /run?cmd=;cat+/etc/passwd

# Blue agent patches:
import shlex
safe_cmd = shlex.split(request.args.get("cmd", ""))
subprocess.call(safe_cmd, shell=False)          # ← fixed
```

### Chain Detection Example
```
Finding 1: path_traversal at line 34 (user controls filename)
Finding 2: open() at line 37 (opens the controlled path)
Finding 3: response.write() at line 40 (sends content to user)

Chain: 1 → 2 → 3 = Arbitrary File Read via path traversal
Severity: CRITICAL (chain score: 9.1)
```

---

## 📊 Supported Languages

| Language | AST Parser | Rules |
|---|---|---|
| Python | tree-sitter-python | SQLi, CMDi, Path Traversal, SSRF, Deserialization |
| JavaScript/TypeScript | tree-sitter-javascript | XSS, Prototype Pollution, ReDoS, Secret Hardcoding |
| Go | tree-sitter-go | Race conditions, unsafe pointer usage |
| Java | tree-sitter-java | XXE, JNDI injection, deserialization |

---

## 🔗 GitHub Actions Integration

Add `.github/workflows/codesentinel.yml` to any repo:

```yaml
name: CodeSentinel Scan
on: [push, pull_request]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0        # needed for git history scanning

      - name: Run CodeSentinel
        uses: NITHINKR06/codesentinel@main
        with:
          groq-api-key: ${{ secrets.GROQ_API_KEY }}
          fail-on-severity: high
          upload-sarif: true
```

---

## 📄 License

MIT — open for contributions and research use.

---

**Built with FastAPI · Next.js · Tree-sitter · LangChain · Groq · Celery · Redis · Docker**

*Find it. Prove it. Fix it. Automatically.*
