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
    
    # vuln_subscore: (0 * 2 + 75 * 1) / 3 = 25
    # license_subscore: (0 * 2 + 90 * 1) / 3 = 30
    # maintenance_subscore: ((100-100)*2 + (100-20)*1) / 3 = (0 + 80) / 3 = 26.67
    
    # overall_score: 0.5 * 25 + 0.3 * 30 + 0.2 * 26.67 = 12.5 + 9.0 + 5.33 = 26.83 -> rounds to 27
    assert result.vulnerability_subscore == 25
    assert result.license_subscore == 30
    assert result.maintenance_subscore == 27
    assert result.overall_score == 27
    assert result.category == "MEDIUM"
    assert result.breakdown["confidence"] == 1.0


def test_empty_dependencies():
    engine = RiskEngine()
    result = engine.calculate([])
    assert result.overall_score == 0
    assert result.category == "LOW"
