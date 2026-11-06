"""Verify archived code, saved evaluation arithmetic and the final CLI contract.

No final-test retrieval is repeated. Replays use frozen observations only.
CLI smoke queries are unscored interface checks, never used for selection.
"""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from datetime import UTC, datetime

from audit_quality_v3 import security_scan
from quality_v3 import (
    ROOT,
    OUT,
    read,
    sha,
    write_once,
    verify_baseline,
    locked_code_path,
    evaluate,
    summarize,
    paired,
)


def main():
    verify_baseline()
    lock = read(OUT / "lock-r2.json")
    archive = {}
    for file, expected in lock["code_sha256"].items():
        path = locked_code_path(file)
        assert sha(path) == expected, file
        archive[file] = dict(path=path.relative_to(ROOT).as_posix(), sha256=expected)
    assert (
        sha(ROOT / "evaluation/scope_candidate_v3.py")
        == lock["code_sha256"]["src/proyek_certan/knowledge/scope.py"]
    )
    manifest = read(OUT / "final_test_manifest.json")
    assert sha(OUT / "final_test.json") == manifest["labels_sha256"]
    assert sha(OUT / "lock-r2.json") == manifest["lock_sha256"]
    assert lock["locked_at_utc"] < manifest["frozen_at_utc"]
    assert (
        sha(ROOT / "evaluation/reviewed_corpus_v3.json") == lock["corpus_report_sha256"]
    )
    for split in ("development", "validation", "final_test"):
        obs = read(OUT / f"observations_{split}.json")
        suffix = "_r2" if split == "development" else ""
        report = read(OUT / f"results_{split}{suffix}.json")
        assert sha(OUT / f"observations_{split}.json") == report["observations_sha256"]
        assert sha(OUT / f"{split}.json") == obs["labels_sha256"]
        if split != "development":
            assert manifest["frozen_at_utc"] < obs["generated_at_utc"]
        arms = {
            "baseline": evaluate(obs),
            "guard": evaluate(obs, guard=lock["guard_config"]),
            "title": evaluate(obs, alpha=lock["title_alpha"]),
            "title_guard": evaluate(
                obs, guard=lock["guard_config"], alpha=lock["title_alpha"]
            ),
        }
        for arm, rows in arms.items():
            saved = report["arms"][arm]
            for a, b in zip(rows, saved["queries"], strict=True):
                for key in (
                    "id",
                    "query",
                    "relevant_documents",
                    "status",
                    "reason_codes",
                    "ungated",
                    "gated",
                ):
                    assert a[key] == b[key], (split, arm, key)
            actual = summarize(rows)
            for key in actual:
                if key != "latency_ms":
                    assert actual[key] == saved["summary"][key], (split, arm, key)
            if arm != "baseline":
                assert paired(arms["baseline"], rows) == report["comparisons"][arm]
    template = read(OUT / "independent_annotation_template.json")
    assert len(template["annotations"]) == 120 and len(template["sources"]) == 15
    assert all(
        q["annotator_id"] is None and q["relevant_documents"] is None
        for q in template["annotations"]
    )
    decision = read(OUT / "decision.json")
    assert (
        decision["guard_adopted"] is False
        and decision["title_ranking_adopted"] is False
    )
    assert not (ROOT / "src/proyek_certan/knowledge/scope.py").exists()
    for p in (ROOT / "src/proyek_certan/knowledge").glob("*.py"):
        tree = ast.parse(p.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert not any(
                    s in (node.module or "")
                    for s in ("scope_candidate", "title_candidate", "guard_candidate")
                )
    runtime = ROOT / "src/proyek_certan/knowledge/retrieval.py"
    assert "def search_scoped" not in runtime.read_text(encoding="utf-8")
    metadata = read(ROOT / "evaluation/reviewed_corpus_v3.json")["profiles"][
        "v3_t96_w10"
    ]
    cases = [
        (
            "runtime_documents",
            [
                "-m",
                "proyek_certan.knowledge.cli",
                "search",
                "--document-level",
                "--top-k",
                "5",
                "--db",
                metadata["database_path"],
                "--query",
                "Bagaimana diagnosis resolusi nama DNS pada klien?",
            ],
        ),
        (
            "archived_guard_ood",
            [
                "evaluation/guard_candidate_cli_v3.py",
                "--db",
                metadata["database_path"],
                "--query",
                "Tampilkan status terbaru tiket TKT991122.",
            ],
        ),
        (
            "archived_guard_low_confidence",
            [
                "evaluation/guard_candidate_cli_v3.py",
                "--db",
                metadata["database_path"],
                "--query",
                "Bagaimana membuat saus pasta dari tomat?",
            ],
        ),
    ]
    smoke = []
    for name, args in cases:
        result = subprocess.run(
            [sys.executable, *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        value = json.loads(result.stdout)
        if name == "runtime_documents":
            assert isinstance(value, list) and len(value) == 5
            assert len({d["document_id"] for d in value}) == 5
            assert value[0]["document_id"] == "DOC02"
            for d in value:
                assert d["similarity"] == d["ranking_score"]
                assert all(
                    k in d
                    for k in (
                        "chunk_id",
                        "source",
                        "section",
                        "metadata",
                        "ranking_reason",
                    )
                )
        else:
            assert value["experiment_only"] and not value["adopted"]
            assert (
                value["status"] in ("ABSTAIN", "LOW_CONFIDENCE")
                and value["reasons"]
                and not value["results"]
            )
        smoke.append(dict(name=name, command_arguments=args, output=value))
        print("CLI smoke:", name, "PASS", flush=True)
    write_once(
        OUT / "runtime_smoke.json",
        dict(
            generated_at_utc=datetime.now(UTC).isoformat(),
            purpose="Unscored interface/persistence checks; no tuning or final-test rerun.",
            checks=smoke,
        ),
    )
    security = security_scan()
    assert not security["high_confidence_token_matches"], (
        "Potential credential needs review"
    )
    receipt = dict(
        verified_at_utc=datetime.now(UTC).isoformat(),
        baseline_artifacts_unchanged=70,
        archived_code=archive,
        all_saved_decisions_and_metrics_replayed=True,
        bootstrap_comparisons_replayed=True,
        no_test_retrieval_repeated=True,
        final_labels_after_lock_before_observations=True,
        independent_human_annotations_completed=0,
        guard_deployed=False,
        title_reranking_deployed=False,
        document_semantic_option_available=True,
        final_runtime_code_sha256={
            p.relative_to(ROOT).as_posix(): sha(p)
            for p in (
                runtime,
                ROOT / "src/proyek_certan/knowledge/cli.py",
                ROOT / "src/proyek_certan/knowledge/documents.py",
            )
        },
        cli_smoke_passed=True,
        security=security,
        readiness="NOT READY for claiming all T03 score-100 descriptors",
        note="decision.json records the experimental decision; failed guard was subsequently removed from runtime. Exact measured bytes are preserved in locked-code.",
    )
    write_once(OUT / "final_verification.json", receipt)
    verify_baseline()
    print(
        "Final verification PASS; rejected candidates absent from runtime; 70 historical artifacts unchanged."
    )


if __name__ == "__main__":
    main()
