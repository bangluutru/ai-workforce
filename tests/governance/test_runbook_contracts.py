#!/usr/bin/env python3
"""
tests/governance/test_runbook_contracts.py — Test suite for AIWF Team Runbooks.

Verifies:
1. Presence of all 4 standard runbooks in .agents/runbooks/.
2. Completeness and validity of YAML frontmatter in each runbook.
3. Strict parity: every role in each runbook's roster must exist in .agents/roles/roles.json.
4. Strict parity: every skill in each runbook's skills_used must exist in .agents/skills/.
5. Structural completeness of execution phases, handoff contracts, and human approval gates.
"""

import json
from pathlib import Path
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOKS_DIR = REPO_ROOT / ".agents" / "runbooks"
ROLES_JSON_PATH = REPO_ROOT / ".agents" / "roles" / "roles.json"
SKILLS_DIR = REPO_ROOT / ".agents" / "skills"

EXPECTED_RUNBOOKS = [
    "build-webapp.md",
    "produce-video.md",
    "marketing-campaign.md",
    "research-repository.md",
]

MANDATORY_RUNBOOK_FIELDS = [
    "runbook_id",
    "display_name",
    "description",
    "trigger",
    "roster",
    "skills_used",
    "required_inputs",
    "final_deliverables",
]


def load_roles_json():
    with open(ROLES_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_active_skill_names():
    skill_names = set()
    for item in SKILLS_DIR.iterdir():
        if item.is_dir() and (item / "SKILL.md").exists():
            skill_names.add(item.name)
    return skill_names


def parse_runbook_markdown(file_path: Path):
    content = file_path.read_text(encoding="utf-8")
    assert content.startswith("---"), f"{file_path} must start with YAML frontmatter delimiter '---'"
    parts = content.split("---", 2)
    assert len(parts) >= 3, f"{file_path} YAML frontmatter not properly closed"
    frontmatter = yaml.safe_load(parts[1])
    body = parts[2].strip()
    return frontmatter, body


class TestRunbookContracts:
    def test_runbooks_existence(self):
        for rb_name in EXPECTED_RUNBOOKS:
            rb_path = RUNBOOKS_DIR / rb_name
            assert rb_path.exists(), f"Missing expected runbook: {rb_name}"

    def test_runbooks_frontmatter_and_contracts(self):
        roles_data = load_roles_json()
        registered_role_ids = {r["role_id"] for r in roles_data.get("roles", [])}
        active_skills = get_active_skill_names()

        for rb_name in EXPECTED_RUNBOOKS:
            rb_path = RUNBOOKS_DIR / rb_name
            frontmatter, body = parse_runbook_markdown(rb_path)
            assert frontmatter is not None, f"Failed parsing frontmatter in {rb_name}"

            # Check mandatory fields
            for field in MANDATORY_RUNBOOK_FIELDS:
                assert field in frontmatter, f"{rb_name} missing mandatory field '{field}'"
                val = frontmatter[field]
                assert val is not None and val != "", f"{rb_name} field '{field}' is empty"

            # Check runbook_id matches filename
            expected_id = rb_name.replace(".md", "")
            assert frontmatter["runbook_id"] == expected_id, (
                f"{rb_name}: runbook_id '{frontmatter['runbook_id']}' != '{expected_id}'"
            )

            # Check roster integrity
            roster = frontmatter.get("roster", [])
            assert isinstance(roster, list), f"{rb_name}: roster must be a list"
            assert len(roster) >= 3, f"{rb_name}: roster must contain at least 3 roles"
            for role_id in roster:
                assert role_id in registered_role_ids, (
                    f"{rb_name} references unregistered role '{role_id}'. Valid roles: {sorted(registered_role_ids)}"
                )

            # Check skills_used integrity
            skills_used = frontmatter.get("skills_used", [])
            assert isinstance(skills_used, list), f"{rb_name}: skills_used must be a list"
            assert len(skills_used) >= 1, f"{rb_name}: skills_used must contain at least 1 skill"
            for skill in skills_used:
                assert skill in active_skills, (
                    f"{rb_name} references invalid skill '{skill}'. Active skills: {sorted(active_skills)}"
                )

            # Check body content: must contain phases, handoff contracts, and approval gates
            assert "CÁC CHẶNG THỰC THI" in body or "EXECUTION PHASES" in body
            assert "CHỐT PHÊ DUYỆT" in body or "GATE" in body
            assert "Handoff" in body or "Hợp đồng bàn giao" in body or "bàn giao" in body
            assert len(body) > 500, f"{rb_name} body is too brief ({len(body)} chars)"

    def test_no_orphan_markdown_runbooks(self):
        registered = set(EXPECTED_RUNBOOKS)
        registered.add("README.md")
        actual = {p.name for p in RUNBOOKS_DIR.glob("*.md")}
        orphans = actual - registered
        assert not orphans, f"Found orphan runbooks in .agents/runbooks/: {orphans}"
