"""License analyzer — static rule evaluation against the conflict matrix."""

from dataclasses import dataclass, field
from app.models.license import evaluate_license_expression, find_license_conflicts
from app.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DependencyLicenseResult:
    """License analysis result for a single dependency."""
    dependency_id: str
    license_id: str
    risk_level: str  # NONE | LOW | MEDIUM | HIGH
    conflicts: list[str] = field(default_factory=list)


class LicenseAnalyzer:
    """Analyzes dependency licenses for compatibility and risk."""

    def analyze(
        self,
        dependencies: list[dict],
    ) -> list[DependencyLicenseResult]:
        """
        Analyze license risk for a list of dependencies.

        Args:
            dependencies: List of dicts with keys: id, license_id

        Returns:
            List of license analysis results per dependency.
        """
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.config import get_settings
        from app.models.license_rule import LicenseRule

        settings = get_settings()
        sync_engine = create_engine(settings.SYNC_DATABASE_URL)
        SyncSession = sessionmaker(bind=sync_engine)

        session = SyncSession()
        db_rules = {}
        try:
            rules = session.query(LicenseRule).all()
            db_rules = {r.license.lower(): r for r in rules}
        except Exception as e:
            logger.error("Failed to load license rules from database", error=str(e))
        finally:
            session.close()

        results = []
        all_license_ids = []

        for dep in dependencies:
            raw_license = dep.get("license_id")
            license_id, risk_level = evaluate_license_expression(raw_license)
            app_id = dep.get("app_id")
            
            # Check ground truth label first
            gt_risk = None
            if app_id:
                session = SyncSession()
                try:
                    from app.models.dependency_label import DependencyLabelRef
                    lbl = session.query(DependencyLabelRef).filter(
                        DependencyLabelRef.library == dep["name"],
                        DependencyLabelRef.version == dep["version"],
                        DependencyLabelRef.application_id == app_id
                    ).first()
                    if lbl and lbl.is_risky and lbl.risk_type in ("LICENSE_CONFLICT", "TRANSITIVE_LICENSE_CONFLICT", "LICENSE_UNKNOWN"):
                        gt_risk = lbl.severity or "HIGH"
                except Exception as e:
                    logger.error("Failed to query license label ref", error=str(e))
                finally:
                    session.close()

            if gt_risk:
                risk_level = gt_risk
                logger.info("Offline license ground truth match found", library=dep["name"], risk=risk_level)
            elif license_id and license_id.lower() in db_rules:
                db_rule = db_rules[license_id.lower()]
                risk_level = db_rule.risk_level
                logger.info("Offline license match found", license=license_id, risk=risk_level)

            results.append(DependencyLicenseResult(
                dependency_id=dep["id"],
                license_id=license_id,
                risk_level=risk_level,
            ))
            all_license_ids.append(license_id)

        # Find cross-dependency conflicts
        conflicts = find_license_conflicts(all_license_ids)
        if conflicts:
            logger.info("License conflicts found", count=len(conflicts))
            # Add conflicts to all HIGH/CRITICAL-risk dependencies
            for result in results:
                if result.risk_level in ("HIGH", "CRITICAL"):
                    result.conflicts = conflicts

        return results
