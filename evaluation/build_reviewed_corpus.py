"""Build isolated reviewed-v2 corpus, three chunk profiles and persistent indexes.

The baseline is validated/read, never overwritten. Repeated builds verify the
entire existing index before reuse; stale IDs/text/metadata cause a hard error.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from statistics import median
from time import perf_counter

import requests

from proyek_certan.corpus.ingestion import load_corpus
from proyek_certan.corpus.prepare import (
    USER_AGENT,
    _get_limited,
    extract_html_text,
    extract_pdf_text,
    robots_allows,
)
from proyek_certan.corpus.revision import VERSION, document_kind, revise_text
from proyek_certan.corpus.token_experiment import make_profile, token_length
from proyek_certan.knowledge.embeddings import EmbeddingModel, _load_model
from proyek_certan.knowledge.models import KnowledgeChunk, validate_chunks
from proyek_certan.knowledge.retrieval import KnowledgeRetriever
from proyek_certan.knowledge.vector_store import VectorStore

ROOT = Path(__file__).resolve().parents[1]
PROFILES = (("v2_t96_w10", 96, 10), ("v2_t120_w12", 120, 12), ("v2_t96_w0", 96, 0))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def check_store(store: VectorStore, chunks: list[KnowledgeChunk]) -> None:
    actual = store.collection.get(include=["documents", "metadatas"])
    contents = {
        i: (t, m)
        for i, t, m in zip(
            actual["ids"], actual["documents"], actual["metadatas"], strict=True
        )
    }
    expected = {c.chunk_id: (c.text, c.metadata) for c in chunks}
    if contents != expected:
        raise ValueError(
            "index differs from versioned chunks; use a fresh isolated path"
        )


def verify_html_sources(loaded: list[dict]) -> list[dict]:
    """Reuse hashed local source snapshots or fetch each official page once."""
    folder = ROOT / ".local/corpus-review-v2"
    path = folder / "source_checks.json"
    if path.exists():
        checks = json.loads(path.read_text(encoding="utf-8"))
        for check in checks:
            if sha(folder / f"{check['document_id']}.html") != check["html_sha256"]:
                raise ValueError("HTML source snapshot hash changed")
        return checks
    folder.mkdir(parents=True, exist_ok=True)
    checks = []
    with requests.Session() as session:
        session.headers["User-Agent"] = USER_AGENT
        session.max_redirects = 3
        cache = {}
        for item in loaded:
            doc = item["manifest"]
            if doc["document_id"] not in {"DOC06", "DOC09", "DOC10"}:
                continue
            allowed, note = robots_allows(session, doc["source_url"], cache)
            if not allowed:
                raise ValueError("official source robots.txt disallows audit")
            response, body = _get_limited(session, doc["source_url"])
            if (
                response.url != doc["source_url"]
                or "text/html" not in response.headers.get("Content-Type", "").lower()
            ):
                raise ValueError(
                    "official source changed URL or content type; audit manually"
                )
            extracted = extract_html_text(body, doc["publisher"])
            equal = extracted == (ROOT / doc["text_file"]).read_text(encoding="utf-8")
            (folder / f"{doc['document_id']}.html").write_bytes(body)
            checks.append(
                {
                    "document_id": doc["document_id"],
                    "source_url": doc["source_url"],
                    "status": "verified",
                    "retrieved_at_utc": datetime.now(UTC).isoformat(),
                    "robots": note,
                    "html_sha256": hashlib.sha256(body).hexdigest(),
                    "extracted_equals_baseline": equal,
                    "characters": len(extracted),
                }
            )
    write_json(path, checks)
    return checks


def run() -> dict:
    loaded, audits = load_corpus(ROOT)
    protocol = json.loads(
        (ROOT / "evaluation/retrieval_study_protocol_v2.json").read_text(
            encoding="utf-8"
        )
    )
    for path, expected in protocol["frozen_baseline_sha256"].items():
        if sha(ROOT / path) != expected:
            raise ValueError(f"baseline changed: {path}")
    source_checks = verify_html_sources(loaded)
    if {
        c["document_id"]
        for c in source_checks
        if c["status"] == "verified" and c["extracted_equals_baseline"]
    } != {"DOC06", "DOC09", "DOC10"}:
        raise ValueError(
            "official HTML audit must succeed before building reviewed corpus"
        )
    for check in source_checks:
        if (
            sha(ROOT / f".local/corpus-review-v2/{check['document_id']}.html")
            != check["html_sha256"]
        ):
            raise ValueError("HTML source snapshot hash changed")
    processing = json.loads(
        (ROOT / "evaluation/corpus_processing.json").read_text(encoding="utf-8")
    )
    prior = {d["document_id"]: d for d in processing["documents"]}
    provenance_file = ROOT / "evaluation/source_provenance_v2.json"
    provenance = json.loads(provenance_file.read_text(encoding="utf-8"))["documents"]
    documents = []
    unresolved = {
        "DOC09": "DRAFT, institutional placeholders and indicative SLA; requires source-owner approval, no local CERTAN authority.",
        "DOC10": "DRAFT, institutional placeholders and indicative deadlines; requires source-owner approval.",
        "DOC11": "Hard wraps, TOC leaders, multi-column Figure 1.1 SLA table and diagrams remain. No semantic table reconstruction attempted; source distribution/control notice preserved.",
        "DOC13": "Running headers and clause prose reflow corrected; front matter/contact layout retained. Full visual source review pending.",
    }
    for item, audit in zip(loaded, audits, strict=True):
        doc = item["manifest"]
        doc_id = doc["document_id"]
        raw = ROOT / "data/corpus/raw" / doc["filename"]
        if sha(raw) != prior[doc_id]["source_pdf_sha256"]:
            raise ValueError(f"raw source changed: {doc_id}")
        correction = provenance.get(doc_id, {})
        if correction and (
            correction["source_pdf_sha256"] != sha(raw)
            or correction["historical_source_url"] != doc["source_url"]
        ):
            raise ValueError(f"{doc_id}: provenance correction refers to another source")
        original = (ROOT / doc["text_file"]).read_text(encoding="utf-8")
        if (
            doc_id in {"DOC11", "DOC13"}
            and extract_pdf_text(raw, doc["title"]) != original
        ):
            raise ValueError(f"{doc_id}: original TXT differs from PDF extraction")
        revised, operations = revise_text(doc_id, original)
        target = (
            ROOT
            / "data/corpus/processed/reviewed-v2"
            / (Path(doc["filename"]).stem + ".txt")
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(revised, encoding="utf-8", newline="\n")
        item["text"] = revised
        audit["review_required"] = doc_id in unresolved
        documents.append(
            dict(
                **doc,
                corpus_version=VERSION,
                document_kind=document_kind(doc["title"]),
                revised_text_file=target.relative_to(ROOT).as_posix(),
                original_text_sha256=sha(ROOT / doc["text_file"]),
                text_sha256=sha(target),
                source_pdf_sha256=sha(raw),
                verified_source_url=correction.get("verified_source_url", doc["source_url"]),
                source_revision=correction.get("source_revision"),
                extraction_method=prior[doc_id]["method"],
                baseline_quality_flags=audit["quality_flags"],
                review_required=audit["review_required"],
                unresolved=unresolved.get(doc_id),
                **operations,
            )
        )
    embedder = EmbeddingModel()
    model = _load_model(embedder.model_name, embedder.cache_folder)
    tokenizer = model.tokenizer
    if (
        model.max_seq_length != 128
        or tokenizer.num_special_tokens_to_add(pair=False) != 2
    ):
        raise ValueError("model input limits changed")
    count = lambda text: token_length(tokenizer, text)
    by_id = {d["document_id"]: d for d in documents}
    report = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "corpus_version": VERSION,
        "model_name": embedder.model_name,
        "embedding_dimension": embedder.dimension,
        "model_max_sequence_tokens": int(model.max_seq_length),
        "source_checks": source_checks,
        "provenance_corrections_sha256": sha(provenance_file),
        "visual_review_limitation": "Poppler unavailable; PyMuPDF native DLL blocked by Windows Application Control. No claim of complete visual review. pypdf page-boundary/text checks performed; ambiguous layouts retained.",
        "documents": documents,
        "profiles": {},
    }
    previous_path = ROOT / "evaluation/reviewed_corpus_v2.json"
    previous = (
        json.loads(previous_path.read_text(encoding="utf-8"))
        if previous_path.exists()
        else {}
    )
    for name, cap, overlap in PROFILES:
        original_chunks = make_profile(loaded, audits, count, cap, overlap)
        chunks = []
        for c in original_chunks:
            doc = by_id[str(c.metadata["document_id"])]
            metadata = dict(
                c.metadata,
                corpus_version=VERSION,
                document_kind=doc["document_kind"],
                publisher=doc["publisher"],
                source_pdf_sha256=doc["source_pdf_sha256"],
                text_sha256=doc["text_sha256"],
                extraction_method=doc["extraction_method"],
                text_file=doc["revised_text_file"],
                chunk_profile=name,
                review_note=doc["unresolved"]
                or "Reviewed source-specific formatting; topical use only.",
            )
            if doc["verified_source_url"] != doc["source_url"]:
                metadata["source_url"] = doc["verified_source_url"]
                metadata["historical_source_url"] = doc["source_url"]
                metadata["source_revision"] = doc["source_revision"]
            if doc.get("license_url"):
                metadata["license_url"] = doc["license_url"]
            chunks.append(KnowledgeChunk(f"{VERSION}-{c.chunk_id}", c.text, metadata))
        validate_chunks(chunks)
        chunk_path = (
            ROOT / f"data/corpus/processed/reviewed-v2/knowledge_chunks_{name}.json"
        )
        write_json(chunk_path, [asdict(c) for c in chunks])
        database = ROOT / f".local/chroma-corpus-m3-{name}-provenance"
        duration = None
        with VectorStore(database) as store:
            if store.count() == 0:
                start = perf_counter()
                KnowledgeRetriever(store, embedder).index_chunks(chunks)
                duration = round(perf_counter() - start, 3)
            check_store(store, chunks)
        # Reopen, rather than trusting the writer's in-memory collection.
        with VectorStore(database) as reopened:
            check_store(reopened, chunks)
        lengths = [count(c.text) for c in chunks]
        if duration is None:
            duration = (
                previous.get("profiles", {}).get(name, {}).get("index_duration_seconds")
            )
        report["profiles"][name] = {
            "chunk_count": len(chunks),
            "document_count": len({c.metadata["document_id"] for c in chunks}),
            "max_total_tokens": cap,
            "overlap_words_requested": overlap,
            "source_word_coverage_verified": True,
            "token_lengths": {
                "min": min(lengths),
                "median": median(lengths),
                "max": max(lengths),
                "over_model_limit": sum(n > 128 for n in lengths),
            },
            "chunks_per_document": dict(
                sorted(Counter(c.metadata["document_id"] for c in chunks).items())
            ),
            "index_duration_seconds": duration,
            "stored_ids_text_metadata_verified": True,
            "database_path": database.relative_to(ROOT).as_posix(),
            "chunk_file": chunk_path.relative_to(ROOT).as_posix(),
            "chunk_file_sha256": sha(chunk_path),
        }
        print(name, report["profiles"][name], flush=True)
    write_json(previous_path, report)
    return report


if __name__ == "__main__":
    run()
