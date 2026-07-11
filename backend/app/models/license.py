"""License conflict matrix — static rule evaluation for SPDX license compatibility."""

# License risk levels: NONE (permissive), LOW (weak-copyleft), MEDIUM (unknown), HIGH (copyleft/undeclared)
LICENSE_RISK_MAP: dict[str, str] = {
    # Permissive — NONE risk
    "MIT": "NONE",
    "Apache-2.0": "NONE",
    "BSD-2-Clause": "NONE",
    "BSD-3-Clause": "NONE",
    "ISC": "NONE",
    "Unlicense": "NONE",
    "0BSD": "NONE",
    "CC0-1.0": "NONE",
    "Zlib": "NONE",
    "BSL-1.0": "NONE",
    "PSF-2.0": "NONE",
    "Python-2.0": "NONE",
    "WTFPL": "NONE",
    "X11": "NONE",
    "Fair": "NONE",

    # Weak copyleft — LOW risk
    "LGPL-2.1-only": "LOW",
    "LGPL-2.1-or-later": "LOW",
    "LGPL-3.0-only": "LOW",
    "LGPL-3.0-or-later": "LOW",
    "LGPL-2.1": "LOW",
    "LGPL-3.0": "LOW",
    "MPL-2.0": "LOW",
    "EPL-1.0": "LOW",
    "EPL-2.0": "LOW",
    "CDDL-1.0": "LOW",
    "CPL-1.0": "LOW",

    # Strong copyleft — HIGH risk (assuming closed-source application)
    "GPL-2.0-only": "HIGH",
    "GPL-2.0-or-later": "HIGH",
    "GPL-3.0-only": "HIGH",
    "GPL-3.0-or-later": "HIGH",
    "GPL-2.0": "HIGH",
    "GPL-3.0": "HIGH",
    "AGPL-3.0-only": "HIGH",
    "AGPL-3.0-or-later": "HIGH",
    "AGPL-3.0": "HIGH",
    "SSPL-1.0": "HIGH",
    "OSL-3.0": "HIGH",

    # Commercial / proprietary markers — MEDIUM
    "Commercial": "MEDIUM",
    "Proprietary": "MEDIUM",
}

# Copyleft licenses that conflict with proprietary / closed-source usage
COPYLEFT_LICENSES = {
    "GPL-2.0-only", "GPL-2.0-or-later", "GPL-3.0-only", "GPL-3.0-or-later",
    "GPL-2.0", "GPL-3.0", "AGPL-3.0-only", "AGPL-3.0-or-later", "AGPL-3.0",
    "SSPL-1.0", "OSL-3.0",
}


def get_license_risk(license_id: str | None) -> tuple[str, str]:
    """
    Determine the risk level for a given SPDX license identifier.

    Returns:
        Tuple of (normalized_license_id, risk_level)
    """
    if license_id is None or license_id.strip() == "":
        return "UNDECLARED", "HIGH"

    normalized = license_id.strip()

    # Check direct match
    if normalized in LICENSE_RISK_MAP:
        return normalized, LICENSE_RISK_MAP[normalized]

    # Check case-insensitive match
    for known_id, risk in LICENSE_RISK_MAP.items():
        if normalized.lower() == known_id.lower():
            return known_id, risk

    # Check for commercial/proprietary keywords
    lower = normalized.lower()
    if "commercial" in lower or "proprietary" in lower:
        return normalized, "MEDIUM"

    # Unknown license
    return "UNKNOWN", "MEDIUM"


def evaluate_license_expression(expression: str | None) -> tuple[str, str]:
    """
    Parse a SPDX license expression (supports OR / AND).
    OR: take least restrictive. AND: take most restrictive.

    Returns:
        Tuple of (license_id, risk_level)
    """
    if expression is None or expression.strip() == "":
        return "UNDECLARED", "HIGH"

    expr = expression.strip()

    # Risk level ordering for comparison
    risk_order = {"NONE": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3}

    # Handle OR expressions — take least restrictive
    if " OR " in expr:
        parts = [p.strip() for p in expr.split(" OR ")]
        results = [get_license_risk(p) for p in parts]
        # Return the least restrictive (lowest risk)
        best = min(results, key=lambda r: risk_order.get(r[1], 2))
        return best

    # Handle AND expressions — take most restrictive
    if " AND " in expr:
        parts = [p.strip() for p in expr.split(" AND ")]
        results = [get_license_risk(p) for p in parts]
        # Return the most restrictive (highest risk)
        worst = max(results, key=lambda r: risk_order.get(r[1], 2))
        return worst

    # Single license
    return get_license_risk(expr)


def find_license_conflicts(license_ids: list[str]) -> list[str]:
    """
    Find license conflicts within a set of dependencies.
    Returns a list of conflict description strings.
    """
    conflicts = []
    copyleft_found = []
    proprietary_found = []

    for lid in license_ids:
        if lid in COPYLEFT_LICENSES:
            copyleft_found.append(lid)
        elif lid in ("Commercial", "Proprietary", "UNDECLARED", "UNKNOWN"):
            proprietary_found.append(lid)

    # Copyleft + proprietary/unknown is a conflict
    if copyleft_found and proprietary_found:
        for cl in copyleft_found:
            for pl in proprietary_found:
                conflicts.append(
                    f"Copyleft license '{cl}' conflicts with '{pl}' in same application"
                )

    return conflicts
