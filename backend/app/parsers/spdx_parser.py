"""SPDX JSON SBOM parser."""

from app.parsers.base import SBOMParser, ParseResult, ParsedDependency, ParsedEdge


class SPDXParser(SBOMParser):
    """Parser for SPDX JSON SBOM format."""

    def parse(self, data: dict) -> ParseResult:
        """Parse an SPDX JSON SBOM into normalized dependencies and edges."""
        result = ParseResult()

        # Validate format
        if "spdxVersion" not in data:
            raise ValueError("Not a valid SPDX SBOM")

        # Find the described package (root)
        document_describes = data.get("documentDescribes", [])
        described_spdx_ids = set(document_describes)

        # Parse packages
        packages = data.get("packages", [])
        spdx_id_map: dict[str, ParsedDependency] = {}

        for pkg in packages:
            spdx_id = pkg.get("SPDXID", "")

            # Skip the document itself
            if spdx_id == "SPDXRef-DOCUMENT":
                continue

            # Check if this is the root/described package
            is_root = spdx_id in described_spdx_ids

            dep = self._parse_package(pkg)
            if is_root:
                result.root_ref = spdx_id
                # Don't add root as a dependency, it's the application itself
                spdx_id_map[spdx_id] = dep
                continue

            result.dependencies.append(dep)
            spdx_id_map[spdx_id] = dep

        # Parse relationships
        relationships = data.get("relationships", [])
        direct_refs = set()

        if not relationships:
            result.warnings.append("FLAT_GRAPH_FALLBACK")
            for dep in result.dependencies:
                dep.is_direct = True
        else:
            for rel in relationships:
                rel_type = rel.get("relationshipType", "")
                source_id = rel.get("spdxElementId", "")
                target_id = rel.get("relatedSpdxElement", "")

                # DEPENDS_ON: source depends on target
                if rel_type == "DEPENDS_ON":
                    if source_id in spdx_id_map and target_id in spdx_id_map:
                        result.edges.append(ParsedEdge(
                            from_ref=source_id,
                            to_ref=target_id,
                        ))
                        # If source is root, target is a direct dependency
                        if source_id == result.root_ref:
                            direct_refs.add(target_id)

                # DEPENDENCY_OF: target depends on source (reverse)
                elif rel_type == "DEPENDENCY_OF":
                    if source_id in spdx_id_map and target_id in spdx_id_map:
                        result.edges.append(ParsedEdge(
                            from_ref=target_id,
                            to_ref=source_id,
                        ))
                        if target_id == result.root_ref:
                            direct_refs.add(source_id)

            # Mark direct dependencies
            for dep in result.dependencies:
                if dep.bom_ref in direct_refs:
                    dep.is_direct = True

            # If no relationships reference root, mark all as direct
            if not direct_refs and result.root_ref:
                result.warnings.append("FLAT_GRAPH_FALLBACK")
                for dep in result.dependencies:
                    dep.is_direct = True

        return result

    def _parse_package(self, pkg: dict) -> ParsedDependency:
        """Parse a single SPDX package into a ParsedDependency."""
        name = pkg.get("name", "unknown")
        version = pkg.get("versionInfo", "unknown")
        spdx_id = pkg.get("SPDXID", "")

        # Extract purl from external refs
        purl = None
        external_refs = pkg.get("externalRefs", [])
        for ref in external_refs:
            if ref.get("referenceType") == "purl":
                purl = ref.get("referenceLocator")
                break

        # Determine ecosystem
        ecosystem = "unknown"
        if purl:
            ecosystem = self.extract_ecosystem_from_purl(purl)

        # Extract license
        license_id = self._extract_license(pkg)

        # Extract repo URL from external refs
        repo_url = None
        for ref in external_refs:
            url = ref.get("referenceLocator", "")
            if "github.com" in url:
                repo_url = url.rstrip("/")
                if repo_url.endswith(".git"):
                    repo_url = repo_url[:-4]
                break

        # Also check download location
        if not repo_url:
            download = pkg.get("downloadLocation", "")
            if "github.com" in download:
                repo_url = download.rstrip("/")
                if repo_url.endswith(".git"):
                    repo_url = repo_url[:-4]

        if not version or version.strip() == "" or version == "NOASSERTION":
            version = "unknown"

        return ParsedDependency(
            name=name,
            version=version,
            ecosystem=ecosystem,
            purl=purl,
            license_id=license_id,
            repo_url=repo_url,
            bom_ref=spdx_id,
        )

    def _extract_license(self, pkg: dict) -> str | None:
        """Extract license from SPDX package."""
        # Try licenseDeclared first (most authoritative)
        license_declared = pkg.get("licenseDeclared")
        if license_declared and license_declared not in ("NOASSERTION", "NONE"):
            return license_declared

        # Fall back to licenseConcluded
        license_concluded = pkg.get("licenseConcluded")
        if license_concluded and license_concluded not in ("NOASSERTION", "NONE"):
            return license_concluded

        return None
