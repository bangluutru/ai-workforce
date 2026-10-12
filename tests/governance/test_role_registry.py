#!/usr/bin/env python3
"""
tests/governance/test_role_registry.py — Test suite for AIWF Agent Role Registry.

Verifies:
1. roles.json schema, version, and role definitions.
2. 1-to-1 parity between roles.json and .agents/roles/*.md files.
3. Completeness of all 11 mandatory contract fields in each role's YAML frontmatter.
4. Validity of all referenced allowed_skills against active skills in .agents/skills/.
5. Absence of duplicate role IDs or conflicting definitions.
"""

import json
from pathlib import Path
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
ROLES_DIR = REPO_ROOT / ".agents" / "roles"
ROLES_JSON_PATH = ROLES_DIR / "roles.json"
SKILLS_DIR = REPO_ROOT / ".agents" / "skills"

MANDATORY_ROLE_FIELDS = [
    "role_id",
    "display_name",
    "purpose",
    "responsibilities",
    "allowed_skills",
    "required_inputs",
    "expected_outputs",
    "quality_criteria",
    "permission_boundaries",
    "handoff_contract",
    "escalation_conditions",
]


def load_roles_json():
    assert ROLES_JSON_PATH.exists(), f"Missing {ROLES_JSON_PATH}"
    with open(ROLES_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def parse_role_markdown(file_path: Path):
    content = file_path.read_text(encoding="utf-8")
    assert content.startswith("---"), f"{file_path} must start with YAML frontmatter delimiter '---'"
    parts = content.split("---", 2)
    assert len(parts) >= 3, f"{file_path} YAML frontmatter not properly closed"
    frontmatter = yaml.safe_load(parts[1])
    body = parts[2].strip()
    return frontmatter, body


def get_active_skill_names():
    skill_names = set()
    for item in SKILLS_DIR.iterdir():
        if item.is_dir() and (item / "SKILL.md").exists():
            skill_names.add(item.name)
    return skill_names


class TestRoleRegistry:
    def test_roles_json_structure(self):
        data = load_roles_json()
        assert data.get("$schema_version") == "1.0"
        roles = data.get("roles", [])
        assert len(roles) == 10, f"Expected exactly 10 curated roles, got {len(roles)}"

        role_ids = [r["role_id"] for r in roles]
        assert len(role_ids) == len(set(role_ids)), "Duplicate role_id in roles.json"

    def test_roles_files_parity_and_completeness(self):
        data = load_roles_json()
        roles_in_json = {r["role_id"]: r for r in data.get("roles", [])}
        active_skills = get_active_skill_names()

        for role_id, info in roles_in_json.items():
            file_name = info.get("file", f"{role_id}.md")
            role_file = ROLES_DIR / file_name
            assert role_file.exists(), f"Role file {role_file} does not exist for role {role_id}"

            frontmatter, body = parse_role_markdown(role_file)
            assert frontmatter is not None, f"Failed to parse frontmatter in {role_file}"

            # Check mandatory fields
            for field in MANDATORY_ROLE_FIELDS:
                assert field in frontmatter, f"{role_file.name} missing mandatory field '{field}'"
                val = frontmatter[field]
                assert val is not None and val != "", f"{role_file.name} field '{field}' is empty"

            # Check role_id consistency
            assert frontmatter["role_id"] == role_id, (
                f"Mismatch in {role_file.name}: frontmatter role_id '{frontmatter['role_id']}' != '{role_id}'"
            )

            # Check that allowed_skills map to valid active skills in AIWF
            allowed = frontmatter.get("allowed_skills", [])
            assert isinstance(allowed, list), f"{role_file.name}: allowed_skills must be a list"
            assert len(allowed) > 0, f"{role_file.name}: allowed_skills cannot be empty"
            for skill in allowed:
                assert skill in active_skills, (
                    f"{role_file.name} references invalid skill '{skill}'. Active skills: {sorted(active_skills)}"
                )

            # Check that body has substantial instructions
            assert len(body) > 200, f"{role_file.name} body is too short (got {len(body)} chars)"

    def test_no_orphan_markdown_roles(self):
        data = load_roles_json()
        registered_files = {r.get("file", f"{r['role_id']}.md") for r in data.get("roles", [])}
        registered_files.add("README.md")

        actual_files = {p.name for p in ROLES_DIR.glob("*.md")}
        orphan_files = actual_files - registered_files
        assert not orphan_files, f"Orphan markdown files found in .agents/roles/: {orphan_files}"
