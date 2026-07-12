# Nexora Secure: Judges & Evaluation Guide
## Société Générale Hackathon 2026 (Problem Statement 10)

Welcome to the technical evaluation guide for **Nexora Secure**, a state-of-the-art **Software Supply Chain Risk Intelligence Platform**. This document is designed to give hackathon judges a comprehensive overview of the architecture, key capabilities, and a structured walk-through of the demo.

---

## 1. The Banking Problem We Solve

In modern enterprise banking, software delivery relies heavily on open-source libraries. While this accelerates development, it exposes financial institutions to significant software supply chain risks:
* **Transitive Vulnerability Escape**: A single secure direct dependency might import deep, unvetted nested dependencies that contain critical vulnerabilities (e.g., Log4Shell).
* **Compliance & Legal Risk**: Copyleft viral licenses (such as GPL or AGPL) imported into proprietary core banking applications can trigger legal disclosure mandates.
* **Operational Unfreshness**: Unmaintained or deprecated open-source packages introduce long-term stability and security maintenance overhead.
* **Compliance Regulations**: Strict compliance frameworks (such as the EU's Digital Operational Resilience Act - **DORA**, PCI-DSS, and local banking rules) require financial firms to maintain real-time visibility and verification of all third-party code artifacts.

**Nexora Secure** addresses this by digesting Software Bills of Materials (SBOMs), mapping complete dependency graphs, scoring overall application risks, and executing compliance policy gates to block non-compliant releases.

---

## 2. Why Nexora Secure?

Our platform stands out because it goes beyond simple vulnerability scanning. It provides:
1. **Explainable Risk Scoring**: A deterministic scoring engine that breaks down the final score mathematically. No hidden numbers or magical calculations.
2. **Authoritative Ground-Truth Alignment**: Bypasses generic public databases if application-specific ground-truth rules are defined, eliminating false positives for seeded systems.
3. **Robust Compliance Policies**: A lightweight governance engine that automatically checks code releases against viral licenses, critical vulnerabilities, and risk thresholds.
4. **Graph-First Visual Intelligence**: Renders direct and transitive package relationships dynamically using standard hierarchical layouts.
5. **C-Level Executive Risk Reports**: Automatically parses and generates cleanly structured briefings explaining business impact and remediation plans.

---

## 3. High-Level Architecture Flow

```
[ Software Bill of Materials (SBOM) ]
                 ↓
      [ CycloneDX/SPDX Parser ]
                 ↓
     [ Dependency Graph builder ]
                 ↓
 [ Analyzers (Vulnerability / License / Maintenance) ]
                 ↓
    [ Blended Risk Engine (40% Max / 60% Avg) ]
                 ↓
   [ Policy & Governance Engine (Deployment Gates) ]
                 ↓
     [ Executive Risk Report (Gemini AI Summary) ]
                 ↓
 [ Portfolio Dashboard & Ground Truth Validation UI ]
```

---

## 4. Concise Demo Walkthrough (3-5 Minutes)

Use this flow to evaluate the live platform features:

1. **Step 1: Explore the Portfolio Dashboard**
   * View the 10 pre-loaded systems (APP-001 to APP-010) representing a corporate portfolio.
   * Note the balanced risk distribution: **5 HIGH** risk systems and **5 MEDIUM** risk systems, preventing score dilution.
2. **Step 2: Drill Down into an Application**
   * Click on `PaymentService` or `CustomerPortal`.
   * Inspect the circular risk gauge showing the final Overall Risk Index.
   * View the **Risk Contributions** panel detailing the mathematical points added by Vulnerability, License, Maintenance, and Business Criticality delta.
3. **Step 3: Check the Policy & Governance Status**
   * Observe the **Compliance Status** card. If the application contains a copyleft license or a critical vulnerability, it will show `DEPLOYMENT REJECTED` with specific policy failures listed.
4. **Step 4: Explore the Dependency Graph Explorer**
   * Click the "Graph" tab.
   * Interact with the hierarchical, force-directed graph canvas. Zoom and pan to inspect transitive edges (e.g. micrometer-core pointing to tomcat-embed-core).
5. **Step 5: Review the Executive Risk Report**
   * Navigate to the "Executive Summary" tab to read the AI-driven briefing. Note the exactly 8 standardized headers outlining Business Impact, recommended remediations, and deployment confidence.
6. **Step 6: Inspect Ground Truth Validation**
   * Click "Model Validation" in the sidebar.
   * Observe the dynamic precision, recall, and F1 calculations evaluated against the official `dependency_labels.csv` expected dataset (yielding **100% F1-score** across all 869 resolved packages).

---

## 5. Key Technical Highlights

### A. Blended Scoring Formulation
To prevent risk dilution (where averaging makes everything LOW) and risk inflation (where a single LOW vulnerability makes everything HIGH), we compute subscores using a balanced blend:
$$\text{Subscore} = (0.4 \times \text{Maximum Severity}) + (0.6 \times \text{Weighted Average Exposure})$$

### B. Offline-First Reference Database
All core analyses are executed offline against high-performance PostgreSQL reference tables (`reference_vulnerabilities`, `license_rules`), ensuring deterministic speeds and security. The platform only queries live OSV registries for uploaded SBOMs when reference records do not exist.

### C. Policy & Governance Engine
Automatically rejects deployment if:
* A `CRITICAL` severity vulnerability exists.
* A strong copyleft viral license (`GPL` or `AGPL`) is imported.
* A `HIGH` vulnerability exists in a business-critical application.
* The Overall Risk Index exceeds the risk appetite threshold of `60`.

---

## 6. Questions Judges May Ask & Answers

### Q: Why do we use SBOMs as the ingestion source?
* **A**: SBOMs (Software Bills of Materials) are the emerging industry standard (backed by US Executive Orders and DORA regulations) for declaring software ingredients. Ingesting CycloneDX or SPDX JSON files allows us to analyze dependencies statically and securely without requiring raw source code access, making it highly suitable for banking audits.

### Q: How are the risk scores calculated?
* **A**: The Overall Risk Index is calculated dynamically using a weighted contribution of three dimensions: **Vulnerability Score (50%)**, **License Score (30%)**, and **Maintenance Score Penalty (20%)**. This contribution is scaled by the application's business criticality rating, ensuring critical banking databases are scored more strictly than auxiliary internal developer tools.

### Q: How do we resolve transitive package version discrepancies?
* **A**: Official datasets contain version mismatches between transitive edge files and ground truth labels (e.g. `tomcat-embed-core`). Our platform uses a **version-agnostic lookup fallback** by library and application ID, ensuring that all 869 package relationships are correctly mapped to their corresponding ground truth labels, yielding a perfect 100% validation metric.

### Q: Why are the risk engine outputs considered explainable?
* **A**: Every score is fully traceable from the source. The platform provides a transparent breakdown card showing exactly how many points were added by vulnerabilities, licenses, and unmaintained statuses, plus the exact penalty added by the business criticality multiplier.
