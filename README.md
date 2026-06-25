# QueueStorm ⚡

[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.1.3-lightgrey.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

QueueStorm is a high-performance, stateless CRM Ticket Triage web service. Designed for modern support desks (e.g., financial services like bKash), it ingests customer support messages and instantly provides structured classification across multiple dimensions.

Built entirely on a rules-based heuristic engine, QueueStorm guarantees deterministic routing, zero external dependencies, and sub-millisecond classification latency—all without the need for GPUs or LLMs.

---

## 🎯 Core Capabilities

QueueStorm analyzes customer messages and intelligently resolves four critical dimensions:

1. **Case Type Classification:** Accurately categorizes the issue (`wrong_transfer`, `payment_failed`, `refund_request`, `phishing_or_social_engineering`, or `other`).
2. **Severity Assessment:** Determines the urgency of the ticket (`low`, `medium`, `high`, `critical`).
3. **Department Routing:** Routes the ticket to the most appropriate handling team (`customer_support`, `dispute_resolution`, `payments_ops`, `fraud_risk`).
4. **Agent Summarization:** Generates a concise, 2-second summary tailored for human agents, strictly ensuring no sensitive credentials (PINs, OTPs, passwords) are ever requested.

The engine also flags high-risk scenarios via the `human_review_required` attribute, ensuring that critical and security-sensitive tickets bypass automated handling for immediate human intervention.

---

## 🏗️ Architecture & Philosophy

QueueStorm is built on a **100% Rules-Based Engine**. 

### Why Rules-Based?
- **Speed & Efficiency:** Sub-millisecond latency. No network overhead or complex model inference times.
- **Cost-Effective:** Zero API costs, operates fully offline, and requires no GPU infrastructure.
- **Deterministic & Safe:** The system's behavior is 100% predictable. It strictly adheres to compliance protocols (e.g., never echoing raw user text that might contain PII, and sanitizing summaries).
- **Multilingual Support:** Natively processes English, Bangla, and mixed-locale inputs.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12 or higher
- Git

### Local Setup
```bash
# Clone the repository
git clone https://github.com/assassinyousuf/SUST_CSE_Carnival_2026_QueueStorm-Warmup-Mock-Preliminary-Task.git
cd queuestorm

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application

**Development Server:**
```bash
python -m app.main
```

**Production Server (Gunicorn):**
```bash
gunicorn app.main:app --bind 0.0.0.0:8000 --workers 2 --threads 4 --timeout 30
```

---

## 🔌 API Reference

QueueStorm provides a clean, RESTful interface.

### 1. Liveness Probe
**`GET /health`**

Validates service health and uptime. Responds in under 10 seconds.
```json
{ 
  "status": "ok", 
  "service": "queuestorm", 
  "version": "1.0.0" 
}
```

### 2. Ticket Triage
**`POST /sort-ticket`**

Accepts a CRM ticket payload and returns a structured triage object.

**Request payload:**
```json
{
  "ticket_id": "T-001",
  "channel": "app",
  "locale": "en",
  "message": "I sent 5000 taka to a wrong number this morning, please help me get it back"
}
```
*(Note: `ticket_id` and `message` are required fields).*

**Response payload:**
```json
{
  "ticket_id": "T-001",
  "case_type": "wrong_transfer",
  "severity": "high",
  "department": "dispute_resolution",
  "agent_summary": "Customer reports sending 5000 BDT to the wrong recipient and requests recovery of the funds.",
  "human_review_required": false,
  "confidence": 0.84
}
```

---

## 🛡️ Testing & Validation

QueueStorm includes a comprehensive test suite validating public sample constraints, security boundaries, schema integrity, and edge cases.

```bash
# Execute the test suite
python tests/test_samples.py
```
*Current Coverage: 40 tests passed, 0 failed.*

---

## ☁️ Deployment

QueueStorm is a standard WSGI application (`app.main:app`) and is containerization-ready. It requires no secrets—only the standard `PORT` environment variable.

- **Render:** Connect the repository. Render will automatically read the included `render.yaml` Blueprint.
- **Railway / Heroku:** Auto-detected via the included `Procfile`.
- **Docker / Fly.io:** Fully supported via the included `Dockerfile`.

---

## 📂 Project Structure

```text
queuestorm/
├── app/
│   ├── __init__.py
│   ├── main.py          # Flask REST API implementation
│   └── classifier.py    # Core rules-based heuristic engine
├── tests/
│   └── test_samples.py  # Validation test suite
├── index.html           # Web UI frontend
├── Procfile             # Railway / Heroku process configuration
├── render.yaml          # Render Blueprint
├── Dockerfile           # Containerization configuration
├── requirements.txt     # Python dependencies
└── runtime.txt          # Explicit Python version
```
