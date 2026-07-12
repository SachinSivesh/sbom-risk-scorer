from app.scoring.risk_engine import RiskEngine, DependencyScore


def test_compute_vuln_score():
    engine = RiskEngine()

    # Max severity used
    vulns = [
        {"severity": "LOW"},
        {"severity": "HIGH"},
        {"severity": "MEDIUM"},
    ]
    assert engine.compute_vuln_score(vulns) == 75

    # Zero vulns
    assert engine.compute_vuln_score([]) == 0

    # Unknown defaults to 50
    assert engine.compute_vuln_score([{"severity": "UNKNOWN"}]) == 50


def test_compute_license_score():
    engine = RiskEngine()
    assert engine.compute_license_score("NONE") == 0
    assert engine.compute_license_score("LOW") == 30
    assert engine.compute_license_score("MEDIUM") == 60
    assert engine.compute_license_score("HIGH") == 90


def test_calculate_risk_score():
    engine = RiskEngine()

    # Clean direct dependency, high-risk transitive dependency
    deps = [
        DependencyScore(
            dependency_id="direct",
            name="direct",
            version="1.0",
            is_direct=True,
            vuln_score=0,
            license_score=0,
            maintenance_score=100, # perfectly healthy
        ),
        DependencyScore(
            dependency_id="transitive",
            name="transitive",
            version="1.0",
            is_direct=False,
            vuln_score=75, # HIGH vuln
            license_score=90, # HIGH license risk
            maintenance_score=20, # poor maintenance
        ),
    ]

    result = engine.calculate(deps)

    # Let's verify the calculations:
    # direct (is_direct=True, weight=2)
    # transitive (is_direct=False, weight=1)
    
    # Blended Max (40%) and Average (60%) Formula:
    # vuln_avg = 25, vuln_max = 75 => blend = 75*0.4 + 25*0.6 = 45
    # license_avg = 30, license_max = 90 => blend = 90*0.4 + 30*0.6 = 54
    # maint_avg = 26.67, maint_max = 80 => blend = 80*0.4 + 26.67*0.6 = 48
    
    # overall_score: 0.5 * 45 + 0.3 * 54 + 0.2 * 48 = 22.5 + 16.2 + 9.6 = 48.3 -> rounds to 48
    assert result.vulnerability_subscore == 45
    assert result.license_subscore == 54
    assert result.maintenance_subscore == 48
    assert result.overall_score == 48
    assert result.category == "MEDIUM"
    assert result.breakdown["confidence"] == 1.0


def test_empty_dependencies():
    engine = RiskEngine()
    result = engine.calculate([])
    assert result.overall_score == 0
    assert result.category == "LOW"
