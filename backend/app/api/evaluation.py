from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db
from app.models.application import Application
from app.models.dependency import Dependency
from app.models.vulnerability import Vulnerability
from app.models.maintenance import MaintenanceSignal
from app.models.dependency_label import DependencyLabelRef
from app.models.license import evaluate_license_expression

router = APIRouter()

@router.get("")
async def evaluate_risk_engine_performance(db: AsyncSession = Depends(get_db)):
    """Compare active dependency classifications against ground truth dependency labels."""
    # 1. Fetch all dataset applications (app_id starting with APP-)
    app_res = await db.execute(select(Application).filter(Application.app_id.like("APP-%")))
    apps = app_res.scalars().all()
    app_ids = [a.app_id for a in apps]
    app_uuid_to_id = {a.id: a.app_id for a in apps}

    if not app_ids:
        return {
            "accuracy": 0, "precision": 0, "recall": 0, "f1_score": 0,
            "confusion_matrix": {"tp": 0, "fp": 0, "fn": 0, "tn": 0},
            "total_evaluated": 0
        }

    # 2. Fetch all ground truth dependency labels
    label_res = await db.execute(select(DependencyLabelRef))
    labels = label_res.scalars().all()
    labels_dict = {(l.library, l.version, l.application_id): l for l in labels}

    # 3. Fetch all active dependencies for these applications
    dep_res = await db.execute(
        select(Dependency)
        .filter(Dependency.sbom_id.in_(
            select(Application.sboms.property.mapper.class_.id)
            .filter(Application.app_id.like("APP-%"))
        ))
        .options(
            selectinload(Dependency.vulnerabilities),
            selectinload(Dependency.maintenance_signal),
            selectinload(Dependency.sbom)
        )
    )
    dependencies = dep_res.scalars().all()

    tp = 0
    fp = 0
    fn = 0
    tn = 0
    
    detailed_results = []

    for d in dependencies:
        app_id_str = app_uuid_to_id.get(d.sbom.application_id) if d.sbom else None
        if not app_id_str:
            # Fallback lookup
            continue
            
        # Get ground truth label
        lbl = labels_dict.get((d.name, d.version, app_id_str))
        if not lbl:
            continue
            
        expected_risky = lbl.is_risky
        
        # Predict risky:
        # 1. Has vulnerabilities
        has_vulns = len(d.vulnerabilities) > 0
        # 2. Has bad maintenance status
        maint_bad = False
        if d.maintenance_signal and d.maintenance_signal.status in ("UNMAINTAINED", "DEPRECATED"):
            maint_bad = True
        # 3. Has high license risk
        _, lic_risk = evaluate_license_expression(d.license_id)
        license_bad = lic_risk in ("HIGH", "CRITICAL")
        
        predicted_risky = has_vulns or maint_bad or license_bad

        if expected_risky and predicted_risky:
            tp += 1
        elif not expected_risky and predicted_risky:
            fp += 1
        elif expected_risky and not predicted_risky:
            fn += 1
        else:
            tn += 1

        detailed_results.append({
            "library": d.name,
            "version": d.version,
            "app_id": app_id_str,
            "expected_risky": expected_risky,
            "predicted_risky": predicted_risky,
            "reasons": {
                "vulnerabilities": has_vulns,
                "maintenance": maint_bad,
                "license": license_bad
            }
        })

    total = tp + fp + fn + tn
    accuracy = (tp + tn) / total if total > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    return {
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "confusion_matrix": {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn
        },
        "total_evaluated": total,
        "sample_size": len(detailed_results)
    }
