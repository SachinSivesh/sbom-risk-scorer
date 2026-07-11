# Software Supply Chain Risk Scorer (SBOM Analyzer)

A full-stack DevSecOps dashboard that ingests a Software Bill of Materials (SBOM) file, resolves its full dependency tree, cross-references it against vulnerability databases, license conflict matrices, maintenance metrics, and generates a single Application Risk Score and AI-driven remediation summary.

## Tech Stack

- **Backend**: Python 3.11, FastAPI, Celery, PostgreSQL 15, Redis 7, SQLAlchemy 2.0, networkx.
- **Frontend**: React 18, TypeScript, Vite, Recharts, react-force-graph-2d, Lucide.
- **AI Integration**: Google Gemini API (gemini-3.5-flash).
- **Deployment**: Docker Compose.

## Core Features

1. **SBOM Ingestion**: Support for CycloneDX JSON and SPDX JSON SBOM formats.
2. **Dependency Resolution**: Complete directed graph builder (direct & transitive dependencies) using networkx.
3. **Vulnerability Mapping**: OSV.dev batch queries to retrieve known vulnerabilities.
4. **License Compliance**: Evaluates copyleft licenses and identifies license compatibility conflicts.
5. **Maintenance Health Analysis**: Measures GitHub stars, pushing dates, and release frequencies.
6. **Deterministic Scoring Engine**: Calculates risk score (0-100) using direct dependency weight biases.
7. **AI Remediation Advisor**: Generates natural-language remediation suggestions using Google Gemini 2.5 Flash.
8. **Interactive Explorer**: Modern force-directed 2D canvas visualization graph with info drawer.

---

## Quick Start (Docker Compose)

### 1. Configure Environment variables
Create a `.env` file in the root directory:
```env
GITHUB_TOKEN=your_github_token_here
GEMINI_API_KEY=your_gemini_api_key_here
```

### 2. Launch Services
Run the following command to build and launch all backend services, database migrations, Celery worker, and the dashboard client:
```bash
docker-compose up --build
```
Once healthy, open your browser and navigate to:
- **Dashboard UI**: `http://localhost:5173` (dev) or container port.
- **Backend API Docs (Swagger)**: `http://localhost:8000/docs`

---

## Running Locally (Development Mode)

### Backend Setup
1. Navigate to the `backend` folder:
   ```bash
   cd backend
   ```
2. Install Python dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
3. Run migrations and start the server:
   ```bash
   alembic upgrade head
   uvicorn app.main:app --reload
   ```

### Frontend Setup
1. Navigate to the `frontend` folder:
   ```bash
   cd frontend
   ```
2. Install Node.js packages:
   ```bash
   npm install
   ```
3. Run the Vite development server:
   ```bash
   npm run dev
   ```

---

## Verifying with Tests

To run the unit tests covering SBOM parsing, cycle detection, license expression evaluations, and deterministic scoring calculations, run pytest in the `backend` directory:
```bash
pytest tests/unit/ -v
```
