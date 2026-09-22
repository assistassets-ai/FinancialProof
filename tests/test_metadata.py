"""Contract test suite for FinancialProof metadata, licensing, and documentation parity.

Verifies:
1. Formal NOTICE file attribution.
2. THIRD_PARTY_LICENSES.md Level 1 SBOM and 10 governance invariants.
3. PEP 621 metadata and URL configuration in pyproject.toml (version intact).
4. 18-point Quick Navigation and bilingual parity between README.md and README_de.md.
5. Mermaid diagram syntax (autonumber, zero unquoted semicolons).
6. Statutory disclaimer (§ 521 BGB) and 48h security SLA.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_notice_file_exists_and_valid() -> None:
    notice_path = PROJECT_ROOT / "NOTICE"
    assert notice_path.is_file(), "NOTICE file must exist at project root"

    content = notice_path.read_text(encoding="utf-8")
    assert "FinancialProof" in content
    assert "Lukas Geiger" in content
    assert "assistassets-ai" in content
    assert "open-bricks" in content
    assert "MIT License" in content


def test_third_party_licenses_and_invariants() -> None:
    tpl_path = PROJECT_ROOT / "THIRD_PARTY_LICENSES.md"
    assert tpl_path.is_file(), "THIRD_PARTY_LICENSES.md must exist at project root"

    content = tpl_path.read_text(encoding="utf-8")
    assert "Level 1 SBOM Inventory" in content
    assert "RunAsInvoker" in content
    assert "Zero-Copyleft Guarantee" in content

    # Verify all 10 governance and runtime invariants
    expected_invariants = [
        "INV-LOCAL-01",
        "INV-NOADV-02",
        "INV-RUNAS-03",
        "INV-RATE-04",
        "INV-SQLITE-05",
        "INV-EXPORT-06",
        "INV-PWA-07",
        "INV-SEC-08",
        "INV-DOCS-09",
        "INV-SLA-10",
    ]
    for inv in expected_invariants:
        assert inv in content, f"Missing invariant {inv} in THIRD_PARTY_LICENSES.md"


def test_pep621_pyproject_metadata() -> None:
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    assert pyproject_path.is_file(), "pyproject.toml must exist"

    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)

    project = data.get("project", {})
    assert project.get("name") == "financial-proof"
    # Version protection rule (T-20260920-167562623): Path B must NEVER bump version
    assert project.get("version") == "1.0.0", "Version must remain 1.0.0 during Path B runs"

    license_files = project.get("license-files", [])
    assert "LICENSE" in license_files
    assert "NOTICE" in license_files
    assert "THIRD_PARTY_LICENSES.md" in license_files

    urls = project.get("urls", {})
    required_urls = [
        "Repository",
        "Documentation",
        "Issues",
        "Notice",
        "Third-Party Licenses",
        "Marketing Log",
        "LLM Ready",
    ]
    for key in required_urls:
        assert key in urls, f"Missing URL entry for {key} in pyproject.toml"

    keywords = project.get("keywords", [])
    assert len(keywords) >= 10, "Keywords must be rich and saturated for discoverability"
    assert "local-first" in keywords
    assert "technical-analysis" in keywords


def test_readme_navigation_and_bilingual_parity() -> None:
    en_path = PROJECT_ROOT / "README.md"
    de_path = PROJECT_ROOT / "README_de.md"

    assert en_path.is_file(), "README.md must exist"
    assert de_path.is_file(), "README_de.md must exist"

    en_content = en_path.read_text(encoding="utf-8")
    de_content = de_path.read_text(encoding="utf-8")

    # 18-point navigation parity
    for i in range(1, 19):
        anchor = f'id="{i}-'
        assert anchor in en_content, f"Missing anchor {i} in README.md"
        assert anchor in de_content, f"Missing anchor {i} in README_de.md"

    # Personas parity
    expected_personas = [
        "[PERSONA-01]",
        "[PERSONA-02]",
        "[PERSONA-03]",
        "[PERSONA-04]",
    ]
    for p in expected_personas:
        assert p in en_content, f"Missing {p} in README.md"
        assert p in de_content, f"Missing {p} in README_de.md"

    # All 10 invariants in comparison matrix
    for i in range(1, 11):
        inv_code = f"INV-"
        assert inv_code in en_content
        assert inv_code in de_content

    # Disclaimer and SLA
    assert "521 BGB" in en_content
    assert "521 BGB" in de_content
    assert "48h" in en_content or "48-Hour" in en_content
    assert "48h" in de_content or "48 Stunden" in de_content


def test_mermaid_diagrams_syntax() -> None:
    en_path = PROJECT_ROOT / "README.md"
    de_path = PROJECT_ROOT / "README_de.md"

    for path in [en_path, de_path]:
        content = path.read_text(encoding="utf-8")
        mermaid_blocks = re.findall(r"```mermaid\n(.*?)```", content, re.DOTALL)
        assert len(mermaid_blocks) >= 2, f"{path.name} must have at least 2 Mermaid diagrams"

        # Check flowchart and sequenceDiagram presence
        has_flowchart = any("flowchart" in b or "graph" in b for b in mermaid_blocks)
        has_sequence = any("sequenceDiagram" in b for b in mermaid_blocks)
        assert has_flowchart, f"{path.name} missing flowchart"
        assert has_sequence, f"{path.name} missing sequenceDiagram"

        # In sequenceDiagram, no statement-terminating semicolons
        for b in mermaid_blocks:
            if "sequenceDiagram" in b:
                assert ";" not in b, f"Found unquoted semicolon in sequenceDiagram in {path.name}"


def test_llms_txt_and_changelog() -> None:
    llms_path = PROJECT_ROOT / "llms.txt"
    changelog_path = PROJECT_ROOT / "CHANGELOG.md"

    assert llms_path.is_file(), "llms.txt must exist"
    assert changelog_path.is_file(), "CHANGELOG.md must exist"

    llms_content = llms_path.read_text(encoding="utf-8")
    assert "assistassets-ai/FinancialProof" in llms_content
    assert "2026-09-22" in llms_content

    changelog_content = changelog_path.read_text(encoding="utf-8")
    assert "## [Unreleased]" in changelog_content
