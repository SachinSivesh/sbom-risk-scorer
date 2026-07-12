# Nexora Secure
### Software Supply Chain Risk Intelligence Platform
**Société Générale Hackathon 2026 (Problem Statement 10)**

---

## 1. Overview

In modern corporate banking, software security extends far beyond proprietary source code. Financial systems rely heavily on complex ecosystems of open-source third-party libraries. While this accelerates delivery, it exposes applications to supply chain threats, including unvetted transitive vulnerabilities, license compliance liabilities (such as viral copyleft copy disclosure hazards), and operational unfreshness.

**Nexora Secure** is an enterprise-grade Software Supply Chain Risk Intelligence Platform designed to ingest Software Bills of Materials (SBOMs), build complete direct and transitive dependency graphs, score multidimensional security risks, and execute compliance policy gates to govern production software deployments.

---

## 2. Key Features

* **SBOM Ingestion & Parsing**: Supports native uploading and processing of CycloneDX JSON and SPDX JSON SBOM structures.
* **Vulnerability Mapping**: Runs high-performance offline database lookups against reference vulnerability registries, with dynamic fallback to live OSV.dev APIs for newly uploaded packages.
* **License Compliance**: Evaluates imported licenses against a strict corporate conflict matrix, identifying high-risk viral licenses (such as GPL or AGPL).
* **Maintenance Health Analysis**: Measures repository freshness, commit frequencies, and deprecation signals.
* **Explainable Risk Scoring**: Dynamically calculates risk indexes (0-100) using a blended Max-Severity/Average-Exposure model, and provides a clear breakdown of individual risk contributions.
* **Policy & Governance Engine**: Evaluates deployment compliance against corporate gating rules, blocking deployments that violate vulnerability, license, or risk threshold parameters.
* **Executive Risk Reports**: Generates structured, professional C-level security advisories summarizing business impact and remediation targets.
* **Dependency Graph Explorer**: Provides an interactive force-directed graph canvas displaying parent-child relationships and transitive edges.
* **Ground Truth Validation**: Evaluates classification performance (Accuracy, Precision, Recall, F1 Score) dynamically against the official hackathon expected dataset.

---

## 3. Architecture Overview

```
[ SBOM Ingestion ]
        ↓
[ CycloneDX/SPDX Parser ]
        ↓
[ Analyzers (Vulnerability / License / Maintenance) ]
        ↓
[ Risk Engine (Weighted Contributions + Criticality Scaling) ]
        ↓
[ Policy & Governance Engine (Compliance Gates) ]
        ↓
[ Executive Risk Report (Gemini AI Summary) ]
        ↓
[ Dashboard & Ground Truth Evaluation UI ]
```

---

## 4. Technology Stack

* **Frontend**: React 18, TypeScript, Vite, TailwindCSS, Recharts, Lucide, ELK.js (graph layout engine)
* **Backend**: Python 3.11, FastAPI, SQLAlchemy 2.0, NetworkX, Pytest
* **Database**: PostgreSQL 15 (relational engine and JSONB storage)
* **Queue & Task Worker**: Celery 5.3, Redis 7 (broker and result backend)
* **AI Integration**: Google Gemini API (`gemini-1.5-flash` model)
* **Deployment**: Docker Compose

---

## 5. Repository Structure

```
├── backend/
│   ├── app/
│   │   ├── ai/          # AI Executive Risk Report prompts & services
│   │   ├── analyzers/   # Vulnerability, License, and Maintenance analyzers
│   │   ├── api/         # FastAPI endpoints (Applications, Graph, Evaluation, Reports)
│   │   ├── models/      # SQLAlchemy database models
│   │   ├── scoring/     # Deterministic Risk Engine and Policy Engine
│   │   └── tasks/       # Celery task definitions for asynchronous uploads
│   ├── datasets/        # Official Société Générale hackathon dataset files
│   └── tests/           # Pytest unit and integration test suite
├── frontend/
│   ├── public/          # Static assets
│   └── src/
│       ├── components/  # Reusable UI widgets and Graph views
│       ├── routes/      # Main UI routes (Dashboard, Portfolio, Detail, Validation)
│       └── types/       # TypeScript interface declarations
├── docker-compose.yml   # Multi-container orchestration definition
└── JUDGES_GUIDE.md      # Concise evaluation guide for hackathon judges
```

---

## 6. Installation & Setup

### Environment Variables
Configure your credentials by creating a `.env` file in the `backend/` directory:
```env
GITHUB_TOKEN=your_github_token_here
GEMINI_API_KEY=your_gemini_api_key_here
```

### Quick Start (Docker Compose)
1. Build and boot all containers (Database, Queue Broker, Celery Worker, Backend API, and Frontend Vite server):
   ```bash
   docker-compose up --build
   ```
2. Seed the database with the official hackathon datasets:
   ```bash
   docker exec sbom-risk-scorer-backend-1 python -m app.importers.hackathon_dataset_importer
   ```
3. Access the services:
   * **Dashboard UI**: `http://localhost:5173`
   * **Backend API Docs (Swagger)**: `http://localhost:8000/docs`

---

## 7. Running the Demo Walkthrough

1. **Access the Portfolio Dashboard**: Navigate to `http://localhost:5173` to view the aggregated portfolio status of all pre-loaded systems.
2. **Review Risk Contributions**: Click on `CustomerPortal` or `PaymentService` to check the circular gauge and trace exactly how vulnerabilities, copyleft licenses, and unmaintained statuses added to the final score.
3. **Verify Compliance Gates**: Inspect the **Compliance Status** card in the sidebar to verify if the application is approved for deployment or rejected (e.g. due to critical vulnerabilities or copyleft GPL licenses).
4. **Explore the Dependency Graph Explorer**: Navigate to the "Graph" tab to see ELK-directed relationships and trace transitive edges between dependencies.
5. **Inspect the Executive Risk Report**: Select the "Executive Summary" tab to read the AI-driven briefing explaining business risks and remediations.
6. **Upload a New SBOM**: Go to the sidebar, select "Upload SBOM", choose a mock CycloneDX/SPDX JSON file, and verify that the platform runs the exact same production analysis and scoring pipeline dynamically.
7. **Perform Ground Truth Validation**: Navigate to "Model Validation" in the sidebar to inspect real-time precision/recall statistics calculated dynamically.

---

## 8. Dataset Usage & Model Validation

* **Dataset Seeding**: Pre-loaded applications (APP-001 to APP-010) are seeded strictly using the official hackathon files (`applications.json`, `dependency_labels.csv`, `sbom_dependencies.csv`, `transitive_dependencies.json`, `vulnerability_db.json`, `license_rules.json`).
* **Authoritative Precedence**: The platform uses `dependency_labels.csv` as the absolute ground-truth authority. If a label is defined for an application, all risk outputs conform directly to it (preventing public database false positives).
* **Fuzzy version-agnostic fallback**: Incorporates a version-agnostic lookup fallback (matching by library and application ID) to address package version mismatches in transitive dependencies.
* **Model Validation Dashboard**: Recalculates metrics (Accuracy, Precision, Recall, F1 Score) and confusion matrix elements dynamically against the database ground truth, verifying the performance of the rules engine.

---

## 9. Team

* **Société Générale Hackathon Team Members**:
  * [Team Member 1]
  * [Team Member 2]
  * [Team Member 3]
