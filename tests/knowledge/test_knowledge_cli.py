"""Offline T03 CLI error and empty-collection behavior."""

import json

from proyek_certan.knowledge.cli import main


def test_search_empty_collection_outputs_json_without_model(tmp_path, capsys):
    assert main(["search", "--db", str(tmp_path), "--query", "wifi"]) == 0
    assert json.loads(capsys.readouterr().out) == []


def test_empty_cli_query_returns_error(tmp_path, capsys):
    assert main(["search", "--db", str(tmp_path), "--query", " "]) == 2
    assert "query" in capsys.readouterr().err


def test_index_missing_file_returns_error(tmp_path, capsys):
    assert main(["index", "--db", str(tmp_path / "db"), "--input", str(tmp_path / "missing.json")]) == 2
    assert "Error:" in capsys.readouterr().err
