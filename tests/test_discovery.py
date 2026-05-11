from vault_search.discovery import discover_markdown_files, path_area


def test_discover_markdown_files_ignores_runtime_directories(sample_vault):
    result = discover_markdown_files(sample_vault)
    paths = [item.relative_path for item in result.files]

    assert paths == [
        "IT-learning/java-basic/java.md",
        "README.md",
        "wiki/INDEX.md",
        "wiki/TLS.md",
    ]
    assert result.ignored_files == 3


def test_path_area_uses_top_level_directory_or_root():
    assert path_area("wiki/INDEX.md") == "wiki"
    assert path_area("IT-learning/java-basic/java.md") == "IT-learning"
    assert path_area("README.md") == "root"
