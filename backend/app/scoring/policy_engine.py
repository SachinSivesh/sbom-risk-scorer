from typing import List, Dict, Any

class PolicyEngine:
    """
    Lightweight enterprise compliance and governance policy engine.
    Checks risk reports against corporate banking governance gates.
    """
    
    @staticmethod
    def evaluate(
        overall_score: int,
        criticality: str,
        vulnerabilities: List[Dict[str, Any]],
        licenses: List[str],
        score_threshold: int = 60
    ) -> Dict[str, Any]:
        """
        Evaluate policy compliance gates.
        
        Args:
            overall_score: Combined risk score (0-100).
            criticality: Business criticality level.
            vulnerabilities: List of dicts representing vulnerabilities (severity).
            licenses: List of SPDX license strings present.
            score_threshold: Max allowed risk score before deployment rejection.
            
        Returns:
            Dict containing pass/fail status and specific violation details.
        """
        violations = []
        
        # Rule 1: Reject if critical vulnerability exists
        has_critical_vuln = any(v.get("severity") == "CRITICAL" for v in vulnerabilities)
        if has_critical_vuln:
            violations.append({
                "rule": "NO_CRITICAL_VULNERABILITIES",
                "description": "Deployment rejected: One or more CRITICAL vulnerabilities detected in dependency scope."
            })
            
        # Rule 2: Reject if GPL / AGPL license detected (viral copyleft risk)
        viral_licenses = ["GPL-2.0", "GPL-3.0", "AGPL-1.0", "AGPL-3.0"]
        detected_viral = [l for l in licenses if l in viral_licenses]
        if detected_viral:
            violations.append({
                "rule": "NO_VIRAL_LICENSES",
                "description": f"Deployment rejected: Viral copyleft license(s) detected: {', '.join(set(detected_viral))}."
            })
            
        # Rule 3: Reject if critical app contains unresolved HIGH vulnerabilities
        has_high_vuln = any(v.get("severity") == "HIGH" for v in vulnerabilities)
        if criticality == "CRITICAL" and has_high_vuln:
            violations.append({
                "rule": "CRITICAL_APP_NO_HIGH_VULNERABILITIES",
                "description": "Deployment rejected: Application is business critical and contains unresolved HIGH vulnerabilities."
            })
            
        # Rule 4: Reject if overall risk score exceeds threshold
        if overall_score >= score_threshold:
            violations.append({
                "rule": "RISK_SCORE_THRESHOLD_EXCEEDED",
                "description": f"Deployment rejected: Overall Risk Score ({overall_score}) exceeds corporate threshold limit ({score_threshold})."
            })
            
        passed = len(violations) == 0
        
        return {
            "status": "PASSED" if passed else "REJECTED",
            "score_threshold_used": score_threshold,
            "violations": violations
        }
