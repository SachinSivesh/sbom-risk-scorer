"""Abstract base parser interface for SBOM formats."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ParsedDependency:
    """Normalized dependency extracted from an SBOM."""
    name: str
    version: str
    ecosystem: str = "unknown"
    purl: Optional[str] = None
    license_id: Optional[str] = None
    is_direct: bool = False
    repo_url: Optional[str] = None
    bom_ref: Optional[str] = None  # Internal reference ID within the SBOM


@dataclass
class ParsedEdge:
    """A directed dependency relationship edge."""
    from_ref: str  # bom-ref of the parent
    to_ref: str    # bom-ref of the child


@dataclass
class ParseResult:
    """Complete parsed result from an SBOM."""
    dependencies: list[ParsedDependency] = field(default_factory=list)
    edges: list[ParsedEdge] = field(default_factory=list)
    root_ref: Optional[str] = None  # bom-ref of the root/described component
    warnings: list[str] = field(default_factory=list)


class SBOMParser(ABC):
    """Abstract interface for SBOM format parsers."""

    @abstractmethod
    def parse(self, data: dict) -> ParseResult:
        """
        Parse raw SBOM JSON into normalized dependencies and edges.

        Args:
            data: Parsed JSON dict of the SBOM file.

        Returns:
            ParseResult with normalized dependencies and edges.

        Raises:
            ValueError: If the SBOM is malformed or unrecoverable.
        """
        ...

    @staticmethod
    def detect_format(data: dict) -> str:
        """Detect the SBOM format from the JSON data."""
        if data.get("bomFormat") == "CycloneDX":
            return "cyclonedx"
        elif "spdxVersion" in data:
            return "spdx"
        raise ValueError("UNSUPPORTED_SBOM_FORMAT")

    @staticmethod
    def extract_ecosystem_from_purl(purl: str) -> str:
        """Extract ecosystem from a Package URL (purl)."""
        # purl format: pkg:type/namespace/name@version
        if not purl or not purl.startswith("pkg:"):
            return "unknown"

        try:
            type_and_rest = purl[4:]  # Remove "pkg:"
            purl_type = type_and_rest.split("/")[0]

            ecosystem_map = {
                "npm": "npm",
                "pypi": "pypi",
                "maven": "maven",
                "golang": "go",
                "cargo": "cargo",
                "gem": "rubygems",
                "nuget": "nuget",
            }
            return ecosystem_map.get(purl_type, "unknown")
        except (IndexError, ValueError):
            return "unknown"

    @staticmethod
    def extract_repo_url(external_refs: list[dict] | None) -> Optional[str]:
        """Extract GitHub repo URL from external references."""
        if not external_refs:
            return None

        for ref in external_refs:
            url = ref.get("url", "")
            ref_type = ref.get("type", "")

            if "github.com" in url and ref_type in ("vcs", "website", "distribution"):
                # Normalize to owner/repo format
                url = url.rstrip("/")
                if url.endswith(".git"):
                    url = url[:-4]
                return url

        # Fallback: any GitHub URL in the references
        for ref in external_refs:
            url = ref.get("url", "")
            if "github.com" in url:
                url = url.rstrip("/")
                if url.endswith(".git"):
                    url = url[:-4]
                return url

        return None
