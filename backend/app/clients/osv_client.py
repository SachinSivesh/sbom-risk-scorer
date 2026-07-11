"""OSV.dev API client for vulnerability lookups."""

import asyncio
from dataclasses import dataclass
from typing import Optional
import httpx
from app.utils.cache import get_cache
from app.utils.logging import get_logger
from app.config import get_settings

logger = get_logger(__name__)

OSV_BATCH_URL = "https://api.osv.dev/v1/querybatch"
OSV_BATCH_SIZE = 1000


@dataclass
class OSVVulnerability:
    """A vulnerability found via OSV.dev."""
    vuln_id: str
    severity: str  # LOW | MEDIUM | HIGH | CRITICAL | UNKNOWN
    summary: str
    fixed_version: Optional[str] = None
    source: str = "osv"


class OSVClient:
    """Async client for the OSV.dev vulnerability API."""

    def __init__(self):
        self.cache = get_cache()
        self.settings = get_settings()

    async def query_batch(
        self,
        packages: list[dict],
    ) -> dict[str, list[OSVVulnerability]]:
        """
        Query OSV.dev for vulnerabilities across multiple packages.

        Args:
            packages: List of dicts with keys: ecosystem, name, version

        Returns:
            Dict mapping "ecosystem:name:version" → list of vulnerabilities
        """
        results: dict[str, list[OSVVulnerability]] = {}

        # Check cache first, collect misses
        cache_misses = []
        for pkg in packages:
            key = f"{pkg['ecosystem']}:{pkg['name']}:{pkg['version']}"
            cache_key = f"osv:{key}"
            cached = await self.cache.get(cache_key)
            if cached is not None:
                results[key] = [OSVVulnerability(**v) for v in cached]
            else:
                cache_misses.append(pkg)

        if not cache_misses:
            return results

        # Batch query OSV.dev for cache misses
        for i in range(0, len(cache_misses), OSV_BATCH_SIZE):
            batch = cache_misses[i:i + OSV_BATCH_SIZE]

            queries = []
            for pkg in batch:
                if pkg["ecosystem"] == "unknown":
                    continue
                queries.append({
                    "package": {
                        "name": pkg["name"],
                        "ecosystem": self._map_ecosystem(pkg["ecosystem"]),
                    },
                    "version": pkg["version"],
                })

            if not queries:
                continue

            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await self._request_with_retry(
                        client, queries
                    )

                    if response and "results" in response:
                        for j, result in enumerate(response["results"]):
                            if j >= len(batch):
                                break
                            pkg = batch[j]
                            key = f"{pkg['ecosystem']}:{pkg['name']}:{pkg['version']}"
                            vulns = self._parse_vulns(result.get("vulns", []))
                            results[key] = vulns

                            # Cache the result
                            cache_key = f"osv:{key}"
                            await self.cache.set(
                                cache_key,
                                [{"vuln_id": v.vuln_id, "severity": v.severity,
                                  "summary": v.summary, "fixed_version": v.fixed_version,
                                  "source": v.source} for v in vulns],
                                ttl=self.settings.OSV_CACHE_TTL,
                            )

            except Exception as e:
                logger.error("OSV batch query failed", error=str(e), batch_size=len(batch))
                # Mark uncached packages with empty results
                for pkg in batch:
                    key = f"{pkg['ecosystem']}:{pkg['name']}:{pkg['version']}"
                    if key not in results:
                        results[key] = []

            # Self-imposed rate limit: 1 req/s between batches
            if i + OSV_BATCH_SIZE < len(cache_misses):
                await asyncio.sleep(1.0)

        return results

    async def _request_with_retry(
        self, client: httpx.AsyncClient, queries: list[dict], retries: int = 3
    ) -> Optional[dict]:
        """Make a request to OSV.dev with retry and exponential backoff."""
        for attempt in range(retries):
            try:
                response = await client.post(
                    OSV_BATCH_URL,
                    json={"queries": queries},
                )
                if response.status_code == 200:
                    return response.json()
                elif response.status_code >= 500:
                    wait = 2 ** attempt
                    logger.warning(
                        "OSV.dev returned 5xx, retrying",
                        status=response.status_code, attempt=attempt + 1, wait=wait,
                    )
                    await asyncio.sleep(wait)
                else:
                    # 4xx = client error, don't retry
                    logger.error("OSV.dev client error", status=response.status_code)
                    return None
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                wait = 2 ** attempt
                logger.warning(
                    "OSV.dev connection error, retrying",
                    error=str(e), attempt=attempt + 1, wait=wait,
                )
                await asyncio.sleep(wait)

        logger.error("OSV.dev exhausted all retries")
        return None

    def _parse_vulns(self, osv_vulns: list[dict]) -> list[OSVVulnerability]:
        """Parse OSV.dev vulnerability response into our model."""
        vulns = []
        for v in osv_vulns:
            vuln_id = v.get("id", "UNKNOWN")
            summary = v.get("summary", v.get("details", "No description available"))[:500]
            severity = self._extract_severity(v)
            fixed_version = self._extract_fixed_version(v)

            vulns.append(OSVVulnerability(
                vuln_id=vuln_id,
                severity=severity,
                summary=summary,
                fixed_version=fixed_version,
            ))
        return vulns

    def _extract_severity(self, vuln: dict) -> str:
        """Extract severity from OSV vulnerability data."""
        # Try database_specific severity first
        severity_list = vuln.get("severity", [])
        for sev in severity_list:
            if sev.get("type") == "CVSS_V3":
                score_str = sev.get("score", "")
                # Parse CVSS vector for score
                try:
                    # CVSS v3 vectors contain the score
                    if "/" in score_str:
                        # It's a vector string, not a score
                        pass
                    else:
                        score = float(score_str)
                        return self._cvss_to_severity(score)
                except (ValueError, TypeError):
                    pass

        # Try ecosystem-specific severity
        db_specific = vuln.get("database_specific", {})
        if "severity" in db_specific:
            raw = db_specific["severity"].upper()
            if raw in ("LOW", "MEDIUM", "MODERATE", "HIGH", "CRITICAL"):
                return "MEDIUM" if raw == "MODERATE" else raw

        # Try affected[].ecosystem_specific.severity
        for affected in vuln.get("affected", []):
            eco_specific = affected.get("ecosystem_specific", {})
            if "severity" in eco_specific:
                raw = eco_specific["severity"].upper()
                if raw in ("LOW", "MEDIUM", "MODERATE", "HIGH", "CRITICAL"):
                    return "MEDIUM" if raw == "MODERATE" else raw

        return "UNKNOWN"

    def _extract_fixed_version(self, vuln: dict) -> Optional[str]:
        """Extract the fixed version from OSV vulnerability data."""
        for affected in vuln.get("affected", []):
            for rng in affected.get("ranges", []):
                for event in rng.get("events", []):
                    if "fixed" in event:
                        return event["fixed"]
        return None

    def _cvss_to_severity(self, score: float) -> str:
        """Convert CVSS score to severity string."""
        if score >= 9.0:
            return "CRITICAL"
        elif score >= 7.0:
            return "HIGH"
        elif score >= 4.0:
            return "MEDIUM"
        elif score > 0:
            return "LOW"
        return "UNKNOWN"

    def _map_ecosystem(self, ecosystem: str) -> str:
        """Map our internal ecosystem names to OSV.dev ecosystem names."""
        mapping = {
            "npm": "npm",
            "pypi": "PyPI",
            "maven": "Maven",
            "go": "Go",
            "cargo": "crates.io",
            "rubygems": "RubyGems",
            "nuget": "NuGet",
        }
        return mapping.get(ecosystem, ecosystem)
