from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_SLUG = "ranrango/ai-harness-loop-lab"
OLD_REPOSITORY_SLUG = "ranrango/harness-loop-engineering"


def test_public_repository_links_use_current_repo_name():
    checked_files = [
        ROOT / "README.md",
        ROOT / "CONTRIBUTING.md",
        ROOT / "RELEASE_CANDIDATE_MANIFEST.md",
        ROOT / "pyproject.toml",
    ]

    for path in checked_files:
        content = path.read_text(encoding="utf-8")
        assert OLD_REPOSITORY_SLUG not in content, f"{path.name} still references old repo slug"
        assert REPOSITORY_SLUG in content, f"{path.name} should reference current repo slug"


def test_python_project_metadata_uses_lab_identity():
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert 'name = "ai-harness-loop-lab"' in pyproject
    assert (
        'description = "AI Harness/Loop lab using drone object detection as a reproducible case study"'
        in pyproject
    )
