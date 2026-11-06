"""Version v3: verified reflow and exact page provenance; all v2 inputs read only."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from statistics import median
from time import perf_counter

from build_reviewed_corpus import check_store, sha, write_json
from quality_v3 import verify_baseline, write_once
from proyek_certan.corpus.ingestion import load_corpus
from proyek_certan.corpus.review_v3 import (
    VERSION,
    revise_v3,
    page_word_index,
    exact_page_span,
)
from proyek_certan.corpus.token_experiment import make_profile, token_length
from proyek_certan.knowledge.embeddings import EmbeddingModel, _load_model
from proyek_certan.knowledge.models import KnowledgeChunk
from proyek_certan.knowledge.retrieval import KnowledgeRetriever
from proyek_certan.knowledge.vector_store import VectorStore

ROOT = Path(__file__).resolve().parents[1]


def run():
    verify_baseline()
    path = ROOT / "evaluation/reviewed_corpus_v3.json"
    if path.exists():
        raise FileExistsError("v3 already built; audit existing artifacts instead")
    previous = json.loads(
        (ROOT / "evaluation/reviewed_corpus_v2.json").read_text(encoding="utf-8")
    )
    by_id = {d["document_id"]: d for d in previous["documents"]}
    loaded, audits = load_corpus(ROOT)
    documents = []
    page_indices = {}
    for item, audit in zip(loaded, audits, strict=True):
        doc = by_id[item["manifest"]["document_id"]]
        before = (ROOT / doc["revised_text_file"]).read_text(encoding="utf-8")
        if sha(ROOT / doc["revised_text_file"]) != doc["text_sha256"]:
            raise ValueError("v2 source changed")
        text, operations = revise_v3(doc["document_id"], before)
        target = (
            ROOT
            / "data/corpus/processed/reviewed-v3"
            / Path(doc["revised_text_file"]).name
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if target.read_text(encoding="utf-8") != text:
                raise ValueError("Partial v3 output differs; inspect before replacing")
        else:
            with target.open("x", encoding="utf-8", newline="\n") as f:
                f.write(text)
        item["text"] = text
        audit["review_required"] = (
            doc["review_required"] and doc["document_id"] != "DOC13"
        )
        record = dict(
            doc,
            corpus_version=VERSION,
            revised_text_file=target.relative_to(ROOT).as_posix(),
            previous_text_sha256=doc["text_sha256"],
            text_sha256=sha(target),
            operations_v3=operations,
            review_required=audit["review_required"],
        )
        if doc["document_id"] == "DOC11":
            record["source_revision"] = "2022-01-19"
            record["unresolved"] = (
                "Visually inspected pages 1,2,5,6,9. Figure 1.1/1.2 tables and screenshots remain flattened in text; do not infer table-cell relationships from chunks alone. Source document-control notice preserved."
            )
        if doc["document_id"] == "DOC13":
            record["unresolved"] = None
            record["review_resolution"] = (
                "All five original PDF pages visually inspected; clauses, lettered items, revision and contact blocks verified. Whitespace reflow only; external policy applicability unchanged."
            )
        if doc["document_id"] in {"DOC11", "DOC13"}:
            page_indices[doc["document_id"]] = page_word_index(
                ROOT / "data/corpus/raw" / doc["filename"], doc["document_id"]
            )
        documents.append(record)
    documents_by_id = {d["document_id"]: d for d in documents}
    embedder = EmbeddingModel()
    model = _load_model(embedder.model_name, embedder.cache_folder)
    count = lambda s: token_length(model.tokenizer, s)
    report = dict(
        generated_at_utc=datetime.now(UTC).isoformat(),
        corpus_version=VERSION,
        previous_report_sha256=sha(ROOT / "evaluation/reviewed_corpus_v2.json"),
        revision_code_sha256=sha(ROOT / "src/proyek_certan/corpus/review_v3.py"),
        model_name=embedder.model_name,
        embedding_dimension=embedder.dimension,
        documents=documents,
        profiles={},
        visual_review=dict(
            renderer="pypdfium2 5.14.0 (QA only, not runtime dependency)",
            DOC11_pages=[1, 2, 5, 6, 9],
            DOC13_pages=[1, 2, 3, 4, 5],
            note="Only explicitly reviewed prose reflow changed. No table contents, diagrams or policy clauses invented.",
        ),
        page_alignment_note="Page numbers only for unique exact source-word matches in the two native-text PDFs; omitted for HTML-derived documents or ambiguous matches.",
    )
    for name, cap, overlap in (
        ("v3_t96_w10", 96, 10),
        ("v3_t120_w12", 120, 12),
        ("v3_t96_w0", 96, 0),
    ):
        base = make_profile(loaded, audits, count, cap, overlap)
        chunks = []
        for c in base:
            doc = documents_by_id[c.metadata["document_id"]]
            m = dict(
                c.metadata,
                source_url=doc["verified_source_url"],
                corpus_version=VERSION,
                publisher=doc["publisher"],
                document_kind=doc["document_kind"],
                source_pdf_sha256=doc["source_pdf_sha256"],
                text_sha256=doc["text_sha256"],
                text_file=doc["revised_text_file"],
                extraction_method=doc["extraction_method"],
                chunk_profile=name,
                review_note=doc["unresolved"]
                or "Source formatting verified; topical retrieval does not confer local operational authority.",
            )
            if doc.get("source_revision"):
                m["source_revision"] = doc["source_revision"]
            if doc["source_url"] != doc["verified_source_url"]:
                m["historical_source_url"] = doc["source_url"]
            if doc.get("license_url"):
                m["license_url"] = doc["license_url"]
            if doc["document_id"] in page_indices:
                m.update(
                    exact_page_span(
                        c.text, doc["title"], page_indices[doc["document_id"]]
                    )
                )
            chunks.append(KnowledgeChunk(f"{VERSION}-{c.chunk_id}", c.text, m))
        cp = ROOT / f"data/corpus/processed/reviewed-v3/knowledge_chunks_{name}.json"
        write_json(cp, [asdict(c) for c in chunks])
        db = ROOT / f".local/chroma-corpus-m3-{name}"
        if db.exists():
            raise FileExistsError("Fresh isolated v3 database required")
        with VectorStore(db) as store:
            start = perf_counter()
            KnowledgeRetriever(store, embedder).index_chunks(chunks)
            elapsed = perf_counter() - start
            check_store(store, chunks)
        with VectorStore(db) as reopened:
            check_store(reopened, chunks)
        lengths = [count(c.text) for c in chunks]
        report["profiles"][name] = dict(
            chunk_count=len(chunks),
            document_count=len({c.metadata["document_id"] for c in chunks}),
            max_total_tokens=cap,
            overlap_words_requested=overlap,
            source_word_coverage_verified=True,
            token_lengths=dict(
                min=min(lengths),
                median=median(lengths),
                max=max(lengths),
                over_model_limit=sum(n > 128 for n in lengths),
            ),
            chunks_per_document=dict(
                Counter(c.metadata["document_id"] for c in chunks)
            ),
            exact_page_spans=sum("page_start" in c.metadata for c in chunks),
            native_pdf_chunks=sum(
                c.metadata["document_id"] in page_indices for c in chunks
            ),
            index_duration_seconds=elapsed,
            database_path=db.relative_to(ROOT).as_posix(),
            chunk_file=cp.relative_to(ROOT).as_posix(),
            chunk_file_sha256=sha(cp),
        )
        print(name, report["profiles"][name], flush=True)
    write_once(path, report)
    verify_baseline()
    return report


if __name__ == "__main__":
    run()
