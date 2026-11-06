"""Audit final organization and replay saved research; optionally run legacy queries.

No label authoring, selection or validation/final-test retrieval is executed.
New receipts may only be written under evaluation/results, never over history.
"""

from __future__ import annotations

import argparse
import ast
from collections import Counter
from datetime import UTC, datetime
import json
from pathlib import Path
import re
from statistics import median
import subprocess
import sys
from urllib.parse import unquote

from proyek_certan.knowledge.documents import distinct_documents
from proyek_certan.knowledge.embeddings import EmbeddingModel, _load_model
from proyek_certan.knowledge.final_corpus import load_final_corpus, sha256, verify_index
from proyek_certan.knowledge.retrieval import KnowledgeRetriever
from proyek_certan.knowledge.vector_store import VectorStore


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "evaluation"))
from benchmark_semantic_retrieval import metrics  # noqa: E402
from quality_v3 import evaluate, summarize, paired  # noqa: E402


def read(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def files_in_repository():
    paths = (
        subprocess.check_output(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            cwd=ROOT,
        )
        .decode("utf-8")
        .split("\0")
    )
    return sorted({p for p in paths if p and (ROOT / p).is_file()})


def audit_integrity():
    baseline = read("evaluation/archive/cleanup-baseline.json")
    require(baseline["working_tree_initially_clean"], "Cleanup baseline was not clean")
    allowed_documentation = {"README.md", "evaluation/README.md"}
    unchanged = []
    modified = []
    for entry in baseline["files"]:
        relative = entry["path"]
        require((ROOT / relative).is_file(), f"Original file removed: {relative}")
        if sha256(ROOT / relative) == entry["sha256"]:
            unchanged.append(relative)
        else:
            require(
                relative in allowed_documentation, f"Unapproved byte change: {relative}"
            )
            modified.append(relative)
    protocol = read("evaluation/quality-v3/protocol.json")
    v2 = read("evaluation/retrieval_study_protocol_v2.json")
    for mapping in (protocol["baseline_sha256"], v2["frozen_baseline_sha256"]):
        for relative, expected in mapping.items():
            require(
                sha256(ROOT / relative) == expected,
                f"Frozen history changed: {relative}",
            )
    lock = read("evaluation/quality-v3/lock-r2.json")
    require(
        sha256(ROOT / "evaluation/quality-v3/protocol.json") == lock["protocol_sha256"],
        "Protocol lock mismatch",
    )
    require(
        sha256(ROOT / "evaluation/reviewed_corpus_v3.json")
        == lock["corpus_report_sha256"],
        "Corpus lock mismatch",
    )
    for relative, expected in lock["code_sha256"].items():
        snapshot = ROOT / "evaluation/quality-v3/locked-code" / relative
        require(sha256(snapshot) == expected, f"Locked snapshot changed: {relative}")
    require(
        sha256(ROOT / "evaluation/scope_candidate_v3.py")
        == lock["code_sha256"]["src/proyek_certan/knowledge/scope.py"],
        "Archived guard differs from measured code",
    )
    require(
        sha256(ROOT / "evaluation/retrieval_study_labels_v2.json")
        == v2["labels_sha256"],
        "v2 labels changed",
    )
    for split in ("development", "validation"):
        require(
            sha256(ROOT / f"evaluation/quality-v3/{split}.json")
            == protocol[f"{split}_sha256"],
            f"{split} labels changed",
        )
    final = read("evaluation/quality-v3/final_test_manifest.json")
    require(
        sha256(ROOT / "evaluation/quality-v3/final_test.json")
        == final["labels_sha256"],
        "Final labels changed",
    )
    require(
        sha256(ROOT / "evaluation/quality-v3/lock-r2.json") == final["lock_sha256"],
        "Final lock changed",
    )
    require(
        lock["locked_at_utc"] < final["frozen_at_utc"], "Final labels must follow lock"
    )
    require(
        len(list((ROOT / "data/corpus/raw").glob("*.pdf"))) == 15,
        "Original PDF count changed",
    )
    for path in (ROOT / "src").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            modules = (
                [a.name for a in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""]
                if isinstance(node, ast.ImportFrom)
                else []
            )
            require(
                not any(
                    any(
                        s in m
                        for s in (
                            "scope_candidate",
                            "title_candidate",
                            "metadata_intent_candidate",
                            "quality_v3",
                        )
                    )
                    for m in modules
                ),
                "Experimental code imported into runtime",
            )
    decision = read("evaluation/quality-v3/decision.json")
    require(
        not decision["guard_adopted"] and not decision["title_ranking_adopted"],
        "Rejected decision altered",
    )
    return dict(
        original_files=len(baseline["files"]),
        unchanged_original_files=len(unchanged),
        modified_original_documentation=modified,
        removed_original_files=0,
        v3_frozen_baseline=len(protocol["baseline_sha256"]),
        v2_frozen_baseline=len(v2["frozen_baseline_sha256"]),
        locked_snapshots=len(lock["code_sha256"]),
        original_pdfs=15,
        all_existing_algorithm_bytes_unchanged=True,
    )


def replay_saved_evaluations():
    lock = read("evaluation/quality-v3/lock-r2.json")
    summaries = {}
    final_manifest = read("evaluation/quality-v3/final_test_manifest.json")
    for split in ("development", "validation", "final_test"):
        relative = f"evaluation/quality-v3/observations_{split}.json"
        observations = read(relative)
        suffix = "_r2" if split == "development" else ""
        report = read(f"evaluation/quality-v3/results_{split}{suffix}.json")
        require(
            sha256(ROOT / relative) == report["observations_sha256"],
            "Saved observations changed",
        )
        require(
            sha256(ROOT / f"evaluation/quality-v3/{split}.json")
            == observations["labels_sha256"],
            "Observation label hash mismatch",
        )
        if split != "development":
            require(
                report["lock_sha256"] == final_manifest["lock_sha256"],
                "Report lock mismatch",
            )
            require(
                final_manifest["frozen_at_utc"] < observations["generated_at_utc"],
                "Observation preceded final label freeze",
            )
        arms = {
            "baseline": evaluate(observations),
            "guard": evaluate(observations, guard=lock["guard_config"]),
            "title": evaluate(observations, alpha=lock["title_alpha"]),
            "title_guard": evaluate(
                observations, guard=lock["guard_config"], alpha=lock["title_alpha"]
            ),
        }
        for arm, rows in arms.items():
            saved = report["arms"][arm]
            for row, previous in zip(rows, saved["queries"], strict=True):
                for key in (
                    "id",
                    "query",
                    "relevant_documents",
                    "status",
                    "reason_codes",
                    "ungated",
                    "gated",
                ):
                    require(
                        row[key] == previous[key],
                        f"Saved query changed: {split}/{arm}/{key}",
                    )
            for key, value in summarize(rows).items():
                if key != "latency_ms":
                    require(
                        value == saved["summary"][key],
                        f"Saved metric changed: {split}/{arm}/{key}",
                    )
            if arm != "baseline":
                require(
                    paired(arms["baseline"], rows) == report["comparisons"][arm],
                    "Saved paired comparison changed",
                )
        summaries[split] = {
            arm: data["summary"] for arm, data in report["arms"].items()
        }
    return dict(
        status="PASS",
        method="Arithmetic replay of frozen observations; no new validation/final retrieval or selection",
        summaries=summaries,
    )


def audit_links_and_secrets():
    files = files_in_repository()
    links = 0
    broken = []
    credential_matches = []
    patterns = (
        r"AKIA[0-9A-Z]{16}",
        r"gh[pousr]_[A-Za-z0-9]{36,}",
        r"sk-(?:proj-)?[A-Za-z0-9_-]{32,}",
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    )
    markdown_count = 0
    scanned_text_files = 0
    for relative in files:
        path = ROOT / relative
        require(
            not relative.endswith((".tmp", ".bak", ".orig", ".rej")),
            f"Temporary file in delivery: {relative}",
        )
        require(
            path.name != ".env" and not path.name.startswith(".env."),
            "Environment secret file in delivery",
        )
        if path.suffix not in {
            ".py",
            ".md",
            ".json",
            ".toml",
            ".txt",
            ".yml",
            ".yaml",
            ".csv",
        }:
            continue
        body = path.read_text(encoding="utf-8")
        scanned_text_files += 1
        if any(re.search(pattern, body) for pattern in patterns):
            credential_matches.append(relative)
        if path.suffix != ".md":
            continue
        markdown_count += 1
        for match in re.finditer(
            r"!?\[[^\]]*\]\((<[^>]+>|[^\s)]+)(?:\s+[^)]*)?\)", body
        ):
            target = match.group(1).strip("<>")
            if (
                not target
                or target.startswith("#")
                or re.match(r"^[a-zA-Z][\w+.-]*:", target)
            ):
                continue
            links += 1
            if not (path.parent / unquote(target.split("#")[0])).exists():
                broken.append(dict(file=relative, target=target))
    require(not broken, f"Broken local Markdown links: {broken}")
    require(
        not credential_matches, "Potential credential found; inspect filenames in audit"
    )
    return dict(
        markdown_files=markdown_count,
        local_links=links,
        broken_links=broken,
        scanned_text_files=scanned_text_files,
        high_confidence_credential_matches=credential_matches,
        scope="Git tracked and nonignored untracked files; cache/venv/git internals excluded. Credential scan is pattern-based.",
    )


def live_legacy_benchmark(corpus):
    labels = read("evaluation/semantic_retrieval_ground_truth.json")
    model = EmbeddingModel(cache_folder=corpus.model_cache)
    loaded = _load_model(model.model_name, model.cache_folder)
    lengths = [
        len(
            loaded.tokenizer(c.text, add_special_tokens=True, truncation=False)[
                "input_ids"
            ]
        )
        for c in corpus.chunks
    ]
    require(
        max(lengths) <= 96 and loaded.max_seq_length == 128,
        "Final token budget exceeded",
    )
    observed_lengths = dict(
        min=min(lengths),
        median=median(lengths),
        max=max(lengths),
        over_model_limit=sum(n > loaded.max_seq_length for n in lengths),
    )
    require(
        observed_lengths == corpus.manifest["chunking"]["token_lengths"],
        "Token statistics changed",
    )
    rows = []
    require(
        (corpus.database_path / "chroma.sqlite3").exists(), "Run final_cli index first"
    )
    with VectorStore(corpus.database_path) as store:
        persisted = verify_index(store, corpus)
        retriever = KnowledgeRetriever(store, model)
        for query in labels["queries"]:
            raw = retriever.search(query["query"], top_k=100)
            documents = distinct_documents(raw)
            ranking = [d.document_id for d in documents]
            require(len(ranking) >= 5, "Insufficient distinct candidates")
            rows.append(
                dict(
                    id=query["id"],
                    query=query["query"],
                    relevant_documents=query["relevant_documents"],
                    distinct_document_ranking=ranking,
                    raw_top1_similarity=raw[0].similarity,
                    metrics=metrics(ranking, set(query["relevant_documents"])),
                )
            )
    positive = [q for q in rows if q["relevant_documents"]]
    ood = [q for q in rows if not q["relevant_documents"]]
    summary = {
        key: sum(q["metrics"][key] for q in positive) / len(positive)
        for key in positive[0]["metrics"]
    }
    historical = read("evaluation/semantic_retrieval_benchmark.json")["profiles"][
        "t96_w10"
    ]["summary"]
    metric_deltas = {key: value - historical[key] for key, value in summary.items()}
    return dict(
        status="PASS",
        purpose="Cleanup regression on 15 legacy queries, never used for selection; no new validation/final-test retrieval",
        persisted_index=persisted,
        token_lengths=observed_lengths,
        positive_count=len(positive),
        ood_count=len(ood),
        raw_candidate_depth=100,
        summary=summary,
        top1_correct_count=sum(
            q["distinct_document_ranking"][0] in q["relevant_documents"]
            for q in positive
        ),
        delta_from_original_legacy_benchmark=metric_deltas,
        legacy_metrics_unchanged=all(
            abs(delta) < 1e-12 for delta in metric_deltas.values()
        ),
        historical_threshold_diagnostic=dict(
            threshold=0.5,
            deployed=False,
            false_acceptance_count=sum(q["raw_top1_similarity"] >= 0.5 for q in ood),
            false_rejection_count=sum(q["raw_top1_similarity"] < 0.5 for q in positive),
            false_acceptance_rate=sum(q["raw_top1_similarity"] >= 0.5 for q in ood)
            / len(ood),
            false_rejection_rate=sum(q["raw_top1_similarity"] < 0.5 for q in positive)
            / len(positive),
        ),
        queries=rows,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live",
        action="store_true",
        help="real model + final index + legacy15 regression",
    )
    parser.add_argument(
        "--output", type=Path, help="new receipt directly inside evaluation/results"
    )
    args = parser.parse_args()
    if args.output:
        output_path = args.output.resolve()
        require(
            output_path.parent == ROOT / "evaluation/results",
            "Receipts must be inside evaluation/results",
        )
        require(not output_path.exists(), "Receipt already exists; choose a new name")
    corpus = load_final_corpus(ROOT)
    result = dict(
        schema_version=1,
        verified_at_utc=datetime.now(UTC).isoformat(),
        integrity=audit_integrity(),
        final_corpus=dict(
            documents=15, chunks=len(corpus.chunks), profile=corpus.manifest["profile"]
        ),
        historical_replay=replay_saved_evaluations(),
        links_and_security=audit_links_and_secrets(),
    )
    if args.live:
        result["live_legacy_regression"] = live_legacy_benchmark(corpus)
    files = files_in_repository()
    if args.output:
        files.append(output_path.relative_to(ROOT).as_posix())
    result["repository_files"] = dict(
        count_basis="Git tracked plus nonignored untracked files; excludes generated local artifacts",
        before=read("evaluation/archive/cleanup-baseline.json")["tracked_file_count"],
        after=len(files),
        by_top_directory=dict(
            Counter(p.split("/")[0] if "/" in p else "(root)" for p in files)
        ),
    )
    if args.output:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    print(
        json.dumps(
            dict(
                status="PASS",
                integrity=result["integrity"],
                final_corpus=result["final_corpus"],
                links_and_security=result["links_and_security"],
                live_summary=result.get("live_legacy_regression", {}).get("summary"),
                repository_files=result["repository_files"],
            ),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
