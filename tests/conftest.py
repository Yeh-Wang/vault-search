from pathlib import Path

import pytest


@pytest.fixture
def sample_vault(tmp_path: Path) -> Path:
    root = tmp_path / "vault"
    (root / "wiki").mkdir(parents=True)
    (root / "IT-learning" / "java-basic").mkdir(parents=True)
    (root / "tmp").mkdir(parents=True)
    (root / ".obsidian").mkdir(parents=True)
    (root / ".pytest_cache").mkdir(parents=True)

    (root / "README.md").write_text("# Fixture Vault\n", encoding="utf-8")
    (root / "wiki" / "INDEX.md").write_text("# Wiki Index\nSee [[TLS]].\n", encoding="utf-8")
    (root / "wiki" / "TLS.md").write_text("# TLS\nTransport Layer Security\n", encoding="utf-8")
    (root / "IT-learning" / "java-basic" / "java.md").write_text(
        "---\ntags: [学习, java]\n---\n# Java\n[[Missing]]\n",
        encoding="utf-8",
    )
    (root / "tmp" / "ignored.md").write_text("# Ignored\n", encoding="utf-8")
    (root / ".obsidian" / "ignored.md").write_text("# Ignored\n", encoding="utf-8")
    (root / ".pytest_cache" / "README.md").write_text("# Pytest Cache\n", encoding="utf-8")
    (root / "plain.txt").write_text("not markdown\n", encoding="utf-8")
    return root
