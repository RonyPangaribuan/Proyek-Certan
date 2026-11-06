"""Independent-process integrity, persistence, historical regression and security audit."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import asdict
from datetime import UTC, datetime

import numpy as np
from benchmark_semantic_retrieval import metrics
from build_reviewed_corpus import check_store
from quality_v3 import OUT, ROOT, sha, verify_baseline, write_once
from title_candidate_v3 import rank_titles

from proyek_certan.corpus.ingestion import load_corpus
from proyek_certan.corpus.review_v3 import (
    VERSION,
    revise_v3,
    page_word_index,
    exact_page_span,
)
from proyek_certan.corpus.token_experiment import make_profile, token_length
from proyek_certan.knowledge.documents import distinct_documents
from proyek_certan.knowledge.embeddings import EmbeddingModel, _load_model
from proyek_certan.knowledge.models import validate_chunks
from proyek_certan.knowledge.retrieval import KnowledgeRetriever
from proyek_certan.knowledge.vector_store import VectorStore


def require(condition, message):
    if not condition:
        raise ValueError(message)


def security_scan():
    files = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        text=True,
    ).splitlines()
    rules = {
        "github_token": r"\b(?:ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{35,})\b",
        "aws_access_key": r"\bAKIA[A-Z0-9]{16}\b",
        "private_key": r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
        "api_key": r"\bsk-(?:proj-)?[A-Za-z0-9_-]{40,}\b",
    }
    hits = []
    count = 0
    for name in files:
        p = ROOT / name
        if p.suffix.lower() not in {
            ".py",
            ".md",
            ".txt",
            ".json",
            ".toml",
            ".yaml",
            ".yml",
            ".env",
        }:
            continue
        content = p.read_text(encoding="utf-8", errors="replace")
        count += 1
        for rule, pattern in rules.items():
            n = len(re.findall(pattern, content))
            if n:
                hits.append(dict(file=name, rule=rule, count=n))
    return dict(
        scanned_text_files=count,
        scope="Tracked and unignored new text files; cached models, databases and ignored environment files excluded.",
        high_confidence_token_matches=hits,
        limitation="Pattern scan cannot prove absence of every possible credential. Actual matched values are never printed.",
    )


def run():
    protocol = verify_baseline()
    corpus = json.loads(
        (ROOT / "evaluation/reviewed_corpus_v3.json").read_text(encoding="utf-8")
    )
    previous = json.loads(
        (ROOT / "evaluation/reviewed_corpus_v2.json").read_text(encoding="utf-8")
    )
    previous_docs = {d["document_id"]: d for d in previous["documents"]}
    require(len(corpus["documents"]) == 15, "Source count changed")
    loaded, audits = load_corpus(ROOT)
    by_id = {d["document_id"]: d for d in corpus["documents"]}
    indices = {}
    source_checks = []
    for item, audit in zip(loaded, audits, strict=True):
        doc = by_id[item["manifest"]["document_id"]]
        old = previous_docs[doc["document_id"]]
        original = (ROOT / old["revised_text_file"]).read_text(encoding="utf-8")
        revised, operations = revise_v3(doc["document_id"], original)
        actual = (ROOT / doc["revised_text_file"]).read_text(encoding="utf-8")
        require(
            actual == revised and original.split() == actual.split(),
            "Source words changed",
        )
        require(
            sha(ROOT / doc["revised_text_file"]) == doc["text_sha256"],
            "v3 text hash mismatch",
        )
        require(
            sha(ROOT / "data/corpus/raw" / doc["filename"]) == doc["source_pdf_sha256"],
            "Original PDF changed",
        )
        if doc.get("publication_status") == "DRAFT":
            require("DRAFT" in actual, "DRAFT text lost")
        item["text"] = actual
        audit["review_required"] = doc["review_required"]
        if doc["document_id"] in {"DOC11", "DOC13"}:
            indices[doc["document_id"]] = page_word_index(
                ROOT / "data/corpus/raw" / doc["filename"], doc["document_id"]
            )
        source_checks.append(
            dict(
                document_id=doc["document_id"],
                source_tokens_identical=True,
                operations=operations,
            )
        )
    embedder = EmbeddingModel()
    model = _load_model(embedder.model_name, embedder.cache_folder)
    count = lambda s: token_length(model.tokenizer, s)
    stores = {}
    for name, p in corpus["profiles"].items():
        require(
            sha(ROOT / p["chunk_file"]) == p["chunk_file_sha256"], "Chunk hash changed"
        )
        chunks = validate_chunks(
            json.loads((ROOT / p["chunk_file"]).read_text(encoding="utf-8"))
        )
        expected = make_profile(
            loaded, audits, count, p["max_total_tokens"], p["overlap_words_requested"]
        )
        require(len(chunks) == len(expected), "Regenerated chunk count differs")
        missing_pages = []
        for a, e in zip(chunks, expected, strict=True):
            require(
                a.chunk_id == f"{VERSION}-{e.chunk_id}" and a.text == e.text,
                "Regenerated chunk ID/text differs",
            )
            d = by_id[a.metadata["document_id"]]
            for key in (
                "document_id",
                "title",
                "section",
                "chunk_index",
                "review_required",
            ):
                require(
                    a.metadata[key] == e.metadata[key], f"Chunk metadata differs: {key}"
                )
            for key in (
                "publisher",
                "document_kind",
                "source_pdf_sha256",
                "text_sha256",
            ):
                require(a.metadata[key] == d[key], f"Provenance differs: {key}")
            require(
                a.metadata["source_url"] == d["verified_source_url"],
                "Source URL differs",
            )
            require(a.metadata["corpus_version"] == VERSION, "Corpus version differs")
            require(count(a.text) <= p["max_total_tokens"], "Token limit exceeded")
            if d.get("publication_status"):
                require(
                    a.metadata["publication_status"] == d["publication_status"],
                    "Publication status differs",
                )
            if d["document_id"] in indices:
                span = exact_page_span(a.text, d["title"], indices[d["document_id"]])
                if span:
                    for key, value in span.items():
                        require(a.metadata[key] == value, "Inaccurate page/offset")
                else:
                    require("page_start" not in a.metadata, "Guessed page number")
                    missing_pages.append(a.chunk_id)
        with VectorStore(ROOT / p["database_path"]) as store:
            check_store(store, chunks)
            vectors = np.asarray(
                store.collection.get(include=["embeddings"])["embeddings"]
            )
            require(
                vectors.shape == (len(chunks), 384),
                "Embedding dimension/count mismatch",
            )
            require(
                np.isfinite(vectors).all()
                and np.allclose(np.linalg.norm(vectors, axis=1), 1, atol=1e-5),
                "Invalid stored vectors",
            )
            stores[name] = dict(
                count=store.count(),
                independent_process_reopen=True,
                ids_text_metadata_identical=True,
                stored_vector_shape=list(vectors.shape),
                stored_vectors_normalized=True,
                configuration=store.collection.configuration_json,
                missing_exact_page_spans=missing_pages,
            )
    # Regression audit AFTER model/config selection: historical labels are never selectors.
    old_results = json.loads(
        (ROOT / "evaluation/retrieval_study_results_v2.json").read_text(
            encoding="utf-8"
        )
    )["arms"]["v2_t96_w10"]["queries"]
    vectors = embedder.encode([q["query"] for q in old_results])
    query_vectors = {q["query"]: v for q, v in zip(old_results, vectors, strict=True)}

    class CachedQueries:
        model_name = embedder.model_name

        def encode(self, text):
            return np.asarray([query_vectors[text]])

    lock = json.loads((OUT / "lock-r2.json").read_text(encoding="utf-8"))
    rows = []
    profile = corpus["profiles"]["v3_t96_w10"]
    with VectorStore(ROOT / profile["database_path"]) as store:
        retriever = KnowledgeRetriever(store, CachedQueries())
        metadata = retriever.catalog().documents
        titles = embedder.encode([str(m["title"]) for m in metadata.values()])
        for q in old_results:
            docs = distinct_documents(retriever.search(q["query"], top_k=100))
            title_scores = dict(
                zip(
                    metadata,
                    (float(s) for s in titles @ query_vectors[q["query"]]),
                    strict=True,
                )
            )
            reranked = rank_titles(docs, title_scores, lock["title_alpha"])
            rows.append(
                dict(
                    id=q["id"],
                    split=q["split"],
                    query=q["query"],
                    relevant_documents=q["relevant_documents"],
                    v2_metrics=q["metrics"],
                    v3_metrics=metrics(
                        [d.document_id for d in docs], set(q["relevant_documents"])
                    ),
                    v3_title_metrics=metrics(
                        [d.document_id for d in reranked], set(q["relevant_documents"])
                    ),
                    v2_top=q["documents"][:7],
                    v3_top=[asdict(d) for d in docs[:7]],
                    v3_title_top=[asdict(d) for d in reranked[:7]],
                )
            )
    historical = dict(
        generated_at_utc=datetime.now(UTC).isoformat(),
        purpose="Historical regression only; not used to select strategy or threshold.",
        queries=rows,
    )
    write_once(OUT / "historical_75_comparison.json", historical)
    report = dict(
        generated_at_utc=datetime.now(UTC).isoformat(),
        baseline_files_verified=len(protocol["baseline_sha256"]),
        source_count=15,
        source_checks=source_checks,
        indexes=stores,
        model=dict(
            name=embedder.model_name,
            dimension=embedder.dimension,
            max_seq_length=model.max_seq_length,
        ),
        security_scan=security_scan(),
        current_revision_code_sha256=sha(
            ROOT / "src/proyek_certan/corpus/review_v3.py"
        ),
        generation_revision_code_sha256=corpus["revision_code_sha256"],
        revision_code_note="Code was formatted after corpus generation. Deterministic source text and all chunk outputs verified above against the current implementation.",
        corpus_report_sha256=sha(ROOT / "evaluation/reviewed_corpus_v3.json"),
    )
    write_once(OUT / "verification.json", report)
    verify_baseline()
    print(
        json.dumps(
            dict(
                baseline_files_verified=report["baseline_files_verified"],
                source_count=15,
                indexes={n: r["count"] for n, r in stores.items()},
                security=report["security_scan"],
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    run()
