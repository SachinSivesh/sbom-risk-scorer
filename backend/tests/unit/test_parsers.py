import json
from pathlib import Path
from app.parsers.cyclonedx_parser import CycloneDXParser
from app.parsers.spdx_parser import SPDXParser
from app.parsers.base import SBOMParser

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def test_detect_format():
    # CycloneDX
    cyclonedx_file = FIXTURES_DIR / "sample_cyclonedx.json"
    with open(cyclonedx_file, "r") as f:
        data = json.load(f)
    assert SBOMParser.detect_format(data) == "cyclonedx"

    # SPDX
    spdx_file = FIXTURES_DIR / "sample_spdx.json"
    with open(spdx_file, "r") as f:
        data = json.load(f)
    assert SBOMParser.detect_format(data) == "spdx"


def test_parse_cyclonedx():
    cyclonedx_file = FIXTURES_DIR / "sample_cyclonedx.json"
    with open(cyclonedx_file, "r") as f:
        data = json.load(f)

    parser = CycloneDXParser()
    result = parser.parse(data)

    assert result.root_ref == "payments-service"
    assert len(result.dependencies) == 15
    assert len(result.edges) > 0

    # Check a specific dependency
    express = next(d for d in result.dependencies if d.name == "express")
    assert express.version == "4.17.1"
    assert express.ecosystem == "npm"
    assert express.license_id == "MIT"
    assert express.is_direct is True


def test_parse_spdx():
    spdx_file = FIXTURES_DIR / "sample_spdx.json"
    with open(spdx_file, "r") as f:
        data = json.load(f)

    parser = SPDXParser()
    result = parser.parse(data)

    assert result.root_ref == "SPDXRef-inventory-api"
    # 10 packages overall, 1 is the root/described application, so 9 dependencies
    assert len(result.dependencies) == 9
    assert len(result.edges) > 0

    flask = next(d for d in result.dependencies if d.name == "flask")
    assert flask.version == "2.0.1"
    assert flask.ecosystem == "pypi"
    assert flask.license_id == "BSD-3-Clause"
    assert flask.is_direct is True
