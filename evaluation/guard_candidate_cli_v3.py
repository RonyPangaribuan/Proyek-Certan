"""Replay the REJECTED guard candidate explicitly for research only.

This module is outside the runtime package. It is not an adopted policy and
must not be presented as an operational OOD safety guarantee.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import sys

from scope_candidate_v3 import GuardConfig, ScopeGuard
from proyek_certan.knowledge.retrieval import KnowledgeRetriever
from proyek_certan.knowledge.vector_store import VectorStore


def evaluate_scoped(retriever, query, *, top_k=5, config=None):
    config = config or GuardConfig(0.6, 0.0)
    found = retriever.search_documents(query, top_k=top_k, candidate_depth=100)
    scores = (
        retriever.title_scores(query) if found and config.support_threshold > 0 else {}
    )
    support = (
        max((scores[r.document_id] for r in found[:3]), default=None)
        if scores
        else None
    )
    return ScopeGuard(config).evaluate(
        query, found, title_support=support, catalog=retriever.catalog()
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args(argv)
    try:
        with VectorStore(args.db) as store:
            decision = evaluate_scoped(
                KnowledgeRetriever(store), args.query, top_k=args.top_k
            )
        print(
            json.dumps(
                dict(experiment_only=True, adopted=False, **asdict(decision)),
                ensure_ascii=False,
                indent=2,
            )
        )
    except (OSError, ValueError, TypeError, RuntimeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
