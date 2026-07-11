from app.models.license import get_license_risk, evaluate_license_expression, find_license_conflicts
from app.analyzers.license_analyzer import LicenseAnalyzer


def test_license_risk_mapping():
    # Permissive
    assert get_license_risk("MIT") == ("MIT", "NONE")
    assert get_license_risk("Apache-2.0") == ("Apache-2.0", "NONE")

    # Weak copyleft
    assert get_license_risk("MPL-2.0") == ("MPL-2.0", "LOW")

    # Strong copyleft
    assert get_license_risk("GPL-3.0") == ("GPL-3.0", "HIGH")

    # Undeclared / Unknown
    assert get_license_risk(None) == ("UNDECLARED", "HIGH")
    assert get_license_risk("SomeRandomLicenseText") == ("UNKNOWN", "MEDIUM")


def test_evaluate_license_expression():
    # OR expression (takes least restrictive)
    assert evaluate_license_expression("GPL-3.0 OR MIT") == ("MIT", "NONE")

    # AND expression (takes most restrictive)
    assert evaluate_license_expression("MIT AND GPL-3.0") == ("GPL-3.0", "HIGH")


def test_license_conflicts():
    # Strong copyleft + commercial / undeclared should trigger a conflict
    conflicts = find_license_conflicts(["GPL-3.0", "Proprietary"])
    assert len(conflicts) > 0
    assert "conflicts with" in conflicts[0]

    # Permissive + weak copyleft should not conflict
    assert len(find_license_conflicts(["MIT", "MPL-2.0"])) == 0


def test_license_analyzer():
    analyzer = LicenseAnalyzer()
    deps = [
        {"id": "dep-1", "license_id": "MIT"},
        {"id": "dep-2", "license_id": "GPL-3.0"},
    ]

    results = analyzer.analyze(deps)
    assert len(results) == 2
    assert results[0].risk_level == "NONE"
    assert results[1].risk_level == "HIGH"
