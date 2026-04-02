# CodeSentinel 🛡️

> Find vulnerabilities. Prove them real. Fix them automatically.

CodeSentinel is a full-stack security analysis platform that scans your GitHub repo or live URL, finds vulnerability chains, generates working PoC exploits to prove they're real, then produces LLM-powered patches — and can open a PR with all fixes applied.

## What it does

| Red Side (Attack) | Blue Side (Defense) |
|---|---|
| AST pattern scanning (12+ vuln types) | LLM-generated context-aware patches |
| Multi-step vulnerability chain detection | Red agent validates every patch |
| Working PoC exploit generation | Security headers auto-config |
| Git history secret excavation | Runtime sandbox simulation |
| Threat actor profile matching | One-click GitHub PR |

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Groq API Key (for fast, cloud LLM features) **OR** [Ollama](https://ollama.ai) running locally (if you have a good machine for local inference)

### 1. (Optional) Pull the LLM model
If you prefer to run the model locally instead of using Groq, pull the Ollama model:
```bash
ollama pull codellama:13b
```

### 2. Clone and configure
```bash
git clone https://github.com/your-org/codesentinel
cd codesentinel
cp .env.example .env
# Edit .env and add your GITHUB_TOKEN and GROQ_API_KEY (or use Ollama)
```

### 3. Run
```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs
- API health: http://localhost:8000/health

## Usage

### Web UI
1. Open http://localhost:3000
2. Paste a GitHub URL or upload a ZIP
3. Watch the live terminal feed
4. Review findings, chains, patches, and the attack graph
5. Hit "Open PR" to apply all verified patches

### API
```bash
# Start a scan
curl -X POST http://localhost:8000/api/scan \
  -H "Content-Type: application/json" \
  -d '{"github_url": "https://github.com/user/repo"}'

# Get results
curl http://localhost:8000/api/report/{scan_id}

# Get security badge SVG
curl http://localhost:8000/api/report/{scan_id}/badge
```

### GitHub Action
```yaml
# .github/workflows/security.yml
name: Security Scan
on: [push, pull_request]
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: your-org/codesentinel@v1
        with:
          api_url: https://your-codesentinel-instance.com
          fail_on_critical: true
          fail_threshold: 60
```

## Architecture

```
Input (GitHub URL / ZIP / Live URL)
        ↓
  Ingestion Layer
        ↓
  ┌─────────────────────────────┐
  │         Red Engine          │
  │  AST Scan → Chain Builder   │
  │  PoC Generator → Exploit    │
  │  Agent + Sandbox + Oracle    │
  │  Threat Actor Profiler      │
  └─────────────────────────────┘
        ↓
  ┌─────────────────────────────┐
  │         Blue Engine         │
  │  Patch Generator → Validator│
  │  Header Fixer → Runtime Sim │
  └─────────────────────────────┘
        ↓
  Scoring + Report + PR
        ↓
  Dashboard (Next.js + D3 graph)
```

## Detected Vulnerability Types

- SQL Injection
- Cross-Site Scripting (XSS)
- Command Injection
- Path Traversal
- Hardcoded Secrets (+ entropy detection)
- Insecure Deserialization
- Missing Authentication
- Weak Cryptography
- Sensitive Data in Logs
- High-entropy string detection
- Missing security headers
- Exposed endpoints (live probe)

## Stack

**Backend:** FastAPI · Python 3.11 · Tree-sitter · NetworkX · LangChain · Groq · Celery · Redis · SQLite  
**Frontend:** Next.js 14 · TypeScript · D3.js · TailwindCSS · Recharts  
**Infra:** Docker Compose · GitHub API · GitHub Actions

## Benchmark Harness

CodeSentinel includes a manifest-driven benchmark runner for Juliet-style cases and real-CVE-style repos.

The red-team demo path now uses a constrained exploit agent with fixed payload templates, a sandbox abstraction, and a type-specific confirmation oracle.

Each benchmark case lives in its own directory and can include a `benchmark.json` file like this:

```json
{
      "name": "sample-case",
      "expected_findings": [
            {
                  "vuln_type": "sqli",
                  "file_path": "app.py",
                  "line_number": 42,
                  "severity": "critical"
            }
      ]
}
```

Run it from the `backend` directory:

```bash
python -m benchmarks.cli /path/to/benchmarks --output table
python -m benchmarks.cli /path/to/benchmarks --output json --pretty
```

The runner reports per-case and aggregate precision, recall, and F1 using a small line-number tolerance to account for AST-based analysis.

## Ethical Use

This tool is designed for:
- Scanning **your own** repositories
- Authorized security audits
- Educational security research

Never scan repositories you don't own or have explicit authorization to test.

## License

MIT
