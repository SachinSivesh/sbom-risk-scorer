"""CycloneDX JSON SBOM parser."""

from app.parsers.base import SBOMParser, ParseResult, ParsedDependency, ParsedEdge
from app.models.license import evaluate_license_expression


class CycloneDXParser(SBOMParser):
    """Parser for CycloneDX JSON SBOM format."""

    def parse(self, data: dict) -> ParseResult:
        """Parse a CycloneDX JSON SBOM into normalized dependencies and edges."""
        result = ParseResult()

        # Validate format
        if data.get("bomFormat") != "CycloneDX":
            raise ValueError("Not a valid CycloneDX SBOM")

        # Extract root component reference
        metadata = data.get("metadata", {})
        root_component = metadata.get("component", {})
        result.root_ref = root_component.get("bom-ref")

        # Extract ecosystem hint from metadata
        default_ecosystem = self._detect_ecosystem_from_metadata(data)

        # Parse components
        components = data.get("components", [])
        bom_ref_map: dict[str, ParsedDependency] = {}

        for comp in components:
            dep = self._parse_component(comp, default_ecosystem)
            result.dependencies.append(dep)
            if dep.bom_ref:
                bom_ref_map[dep.bom_ref] = dep

        # Parse dependency graph
        dependencies_section = data.get("dependencies", [])
        if not dependencies_section:
            # No dependency relationships → flat graph fallback
            result.warnings.append("FLAT_GRAPH_FALLBACK")
            for dep in result.dependencies:
                dep.is_direct = True
        else:
            # Build edges from dependency relationships
            direct_refs = set()

            for dep_rel in dependencies_section:
                from_ref = dep_rel.get("ref")
                depends_on = dep_rel.get("dependsOn", [])

                # If this is the root component's dependencies, mark children as direct
                if from_ref == result.root_ref:
                    direct_refs = set(depends_on)

                for to_ref in depends_on:
                    if from_ref and to_ref:
                        result.edges.append(ParsedEdge(
                            from_ref=from_ref,
                            to_ref=to_ref,
                        ))

            # Mark direct dependencies
            for dep in result.dependencies:
                if dep.bom_ref in direct_refs:
                    dep.is_direct = True

            # If no root was found, mark all top-level components as direct
            if not result.root_ref:
                result.warnings.append("FLAT_GRAPH_FALLBACK")
                for dep in result.dependencies:
                    dep.is_direct = True

        return result

    def _parse_component(self, comp: dict, default_ecosystem: str) -> ParsedDependency:
        """Parse a single CycloneDX component into a ParsedDependency."""
        name = comp.get("name", "unknown")
        version = comp.get("version", "unknown")
        purl = comp.get("purl")
        bom_ref = comp.get("bom-ref")

        # Determine ecosystem from purl or fallback
        ecosystem = "unknown"
        if purl:
            ecosystem = self.extract_ecosystem_from_purl(purl)
        if ecosystem == "unknown" and default_ecosystem != "unknown":
            ecosystem = default_ecosystem

        # Extract license
        license_id = self._extract_license(comp)

        # Extract repo URL
        external_refs = comp.get("externalReferences", [])
        repo_url = self.extract_repo_url(external_refs)

        # Version validation
        if not version or version.strip() == "":
            version = "unknown"

        return ParsedDependency(
            name=name,
            version=version,
            ecosystem=ecosystem,
            purl=purl,
            license_id=license_id,
            repo_url=repo_url,
            bom_ref=bom_ref,
        )

    def _extract_license(self, comp: dict) -> str | None:
        """Extract SPDX license ID from a CycloneDX component."""
        licenses = comp.get("licenses", [])
        if not licenses:
            return None

        license_ids = []
        for lic in licenses:
            # CycloneDX supports both license.id and license.expression
            if "license" in lic:
                lic_obj = lic["license"]
                if "id" in lic_obj:
                    license_ids.append(lic_obj["id"])
                elif "name" in lic_obj:
                    license_ids.append(lic_obj["name"])
            elif "expression" in lic:
                return lic["expression"]

        if license_ids:
            return " OR ".join(license_ids) if len(license_ids) > 1 else license_ids[0]
        return None

    def _detect_ecosystem_from_metadata(self, data: dict) -> str:
        """Try to detect the ecosystem from SBOM metadata."""
        # Check components for purl patterns
        components = data.get("components", [])
        ecosystem_counts: dict[str, int] = {}

        for comp in components[:10]:  # Sample first 10
            purl = comp.get("purl", "")
            if purl:
                eco = self.extract_ecosystem_from_purl(purl)
                if eco != "unknown":
                    ecosystem_counts[eco] = ecosystem_counts.get(eco, 0) + 1

        if ecosystem_counts:
            return max(ecosystem_counts, key=ecosystem_counts.get)
        return "unknown"
