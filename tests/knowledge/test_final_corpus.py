"""Final-corpus provenance, portable paths and safe persistent CLI boundaries."""

import json
import shutil

import numpy as np
import pytest

from proyek_certan.knowledge import final_cli
from proyek_certan.knowledge.embeddings import DEFAULT_MODEL_NAME
from proyek_certan.knowledge.final_corpus import (
    MANIFEST_PATH,
    REPOSITORY_ROOT,
    load_final_corpus,
    repository_path,
    verify_index,
)
from proyek_certan.knowledge.vector_store import VectorStore


@pytest.fixture
def copied_repository(tmp_path):
    """Copy only the provenance closure; tests never write to research evidence."""
    manifest = json.loads((REPOSITORY_ROOT / MANIFEST_PATH).read_text(encoding="utf-8"))
    paths = {
        MANIFEST_PATH.as_posix(),
        manifest["provenance_report"]["path"],
        manifest["chunks"]["path"],
        manifest["chunks"]["origin_path"],
    }
    for document in manifest["documents"]:
        paths.update(
            document[k] for k in ("active_text_file", "origin_text_file", "source_pdf")
        )
    for relative in paths:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPOSITORY_ROOT / relative, target)
    return tmp_path


class StorageEncoder:
    """384-D deterministic vectors test orchestration, not semantic accuracy."""

    model_name = DEFAULT_MODEL_NAME

    def encode(self, texts):
        count = 1 if isinstance(texts, str) else len(texts)
        vectors = np.zeros((count, 384), dtype=np.float32)
        vectors[:, 0] = 1
        return vectors


def test_final_copy_preserves_drafts_and_all_audited_ids():
    corpus = load_final_corpus()
    assert len(corpus.chunks) == 487
    assert len({c.chunk_id for c in corpus.chunks}) == 487
    drafts = [
        c for c in corpus.chunks if c.metadata["document_id"] in {"DOC09", "DOC10"}
    ]
    assert drafts and all(
        c.metadata["publication_status"].startswith("DRAFT") for c in drafts
    )


@pytest.mark.parametrize(
    "field", ["active_text_file", "origin_text_file", "source_pdf"]
)
def test_modified_text_or_original_pdf_is_rejected(copied_repository, field):
    corpus = load_final_corpus(copied_repository)
    path = copied_repository / corpus.manifest["documents"][0][field]
    path.write_bytes(path.read_bytes() + b"\nchanged")
    with pytest.raises(ValueError, match="SHA-256"):
        load_final_corpus(copied_repository)


@pytest.mark.parametrize(
    "relative", ["../outside.txt", str(REPOSITORY_ROOT / "README.md")]
)
def test_absolute_and_parent_paths_are_rejected(tmp_path, relative):
    with pytest.raises(ValueError, match="repository-relative"):
        repository_path(tmp_path, relative)


def test_duplicate_document_and_unregistered_text_are_rejected(copied_repository):
    path = copied_repository / MANIFEST_PATH
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["documents"][1] = manifest["documents"][0]
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="unique document"):
        load_final_corpus(copied_repository)


def test_extra_active_text_is_rejected(copied_repository):
    (copied_repository / MANIFEST_PATH.parent / "extra.txt").write_text(
        "extra", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="Unregistered"):
        load_final_corpus(copied_repository)


def test_missing_final_database_does_not_silently_create_one(tmp_path, capsys):
    db = tmp_path / "not-indexed"
    assert final_cli.main(["search", "--db", str(db), "--query", "DNS"]) == 2
    assert "index first" in capsys.readouterr().err
    assert not db.exists()


def test_mixed_database_is_rejected_before_encoding(tmp_path, capsys, monkeypatch):
    corpus = load_final_corpus()
    with VectorStore(tmp_path) as store:
        store.upsert(corpus.chunks[:1], StorageEncoder().encode(["first"]))

    def fail_if_loaded(**kwargs):
        pytest.fail("A mixed index must be rejected before model creation")

    monkeypatch.setattr(final_cli, "EmbeddingModel", fail_if_loaded)
    assert final_cli.main(["index", "--db", str(tmp_path)]) == 2
    assert "fresh database" in capsys.readouterr().err
    with VectorStore(tmp_path) as store:
        assert store.count() == 1


def test_final_cli_index_reopen_and_document_search(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(final_cli, "EmbeddingModel", lambda **kwargs: StorageEncoder())
    args = ["--db", str(tmp_path)]
    assert final_cli.main(["index", *args]) == 0
    assert json.loads(capsys.readouterr().out)["indexed"] == 487
    assert final_cli.main(["verify", "--index", *args]) == 0
    assert json.loads(capsys.readouterr().out)["index"] == "PASS"
    assert (
        final_cli.main(
            [
                "search",
                *args,
                "--query",
                "DNS",
                "--document-level",
                "--candidate-depth",
                "487",
                "--top-k",
                "5",
            ]
        )
        == 0
    )
    found = json.loads(capsys.readouterr().out)
    assert len({d["document_id"] for d in found}) == 5
    assert all(d["ranking_score"] == d["similarity"] for d in found)
    with VectorStore(tmp_path) as store:
        first = load_final_corpus().chunks[0]
        store.collection.update(
            ids=[first.chunk_id],
            documents=["corrupted index text"],
            embeddings=StorageEncoder().encode(["first"]),
        )
        with pytest.raises(ValueError, match="content mismatch"):
            verify_index(store, load_final_corpus())
