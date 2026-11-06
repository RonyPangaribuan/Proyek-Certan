"""Independent T03 CLI; JSON input is already chunked by an upstream module."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import asdict
import json
from pathlib import Path
import sys

from proyek_certan.knowledge.embeddings import EmbeddingModel
from proyek_certan.knowledge.retrieval import KnowledgeRetriever
from proyek_certan.knowledge.vector_store import VectorStore
from proyek_certan.knowledge.scope import GuardConfig


def build_parser() -> argparse.ArgumentParser:
    """Build separate index and search commands without modifying the M1 CLI."""
    parser = argparse.ArgumentParser(description="CERTAN T03 semantic knowledge search")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("index", "search"):
        command = commands.add_parser(name)
        command.add_argument(
            "--db", type=Path, default=None, help="persistent database directory"
        )
        command.add_argument(
            "--model-cache", type=Path, default=None, help="model cache directory"
        )
        if name == "index":
            command.add_argument(
                "--input", type=Path, required=True, help="JSON array of chunks"
            )
        else:
            command.add_argument("--query", required=True)
            command.add_argument("--top-k", type=int, default=3)
            command.add_argument("--relevance-threshold", type=float, default=None)
            command.add_argument(
                "--document-level",
                action="store_true",
                help="return distinct documents instead of repeated chunks",
            )
            command.add_argument(
                "--scope-guard",
                action="store_true",
                help="explicit query-level ACCEPT/ABSTAIN/LOW_CONFIDENCE output",
            )
            command.add_argument("--candidate-depth", type=int, default=100)
            command.add_argument("--support-threshold", type=float, default=0.0)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Index chunks or print structured retrieval results as JSON."""
    args = build_parser().parse_args(argv)
    try:
        if (
            args.command == "search"
            and args.support_threshold != 0.0
            and not args.scope_guard
        ):
            raise ValueError("--support-threshold requires --scope-guard")
        with VectorStore(args.db) as store:
            retriever = KnowledgeRetriever(
                store, EmbeddingModel(cache_folder=args.model_cache)
            )
            if args.command == "index":
                chunks = json.loads(args.input.read_text(encoding="utf-8"))
                if not isinstance(chunks, list):
                    raise ValueError("input must be a JSON array of chunks")
                output = {
                    "indexed": retriever.index_chunks(chunks),
                    "collection_count": store.count(),
                }
            elif args.scope_guard:
                output = asdict(
                    retriever.search_scoped(
                        args.query,
                        top_k=args.top_k,
                        candidate_depth=args.candidate_depth,
                        config=GuardConfig(
                            0.5
                            if args.relevance_threshold is None
                            else args.relevance_threshold,
                            args.support_threshold,
                        ),
                    )
                )
            elif args.document_level:
                if args.relevance_threshold is not None:
                    raise ValueError(
                        "use --scope-guard for document-level query abstention"
                    )
                output = [
                    asdict(r)
                    for r in retriever.search_documents(
                        args.query,
                        top_k=args.top_k,
                        candidate_depth=args.candidate_depth,
                    )
                ]
            else:
                output = [
                    asdict(result)
                    for result in retriever.search(
                        args.query,
                        top_k=args.top_k,
                        relevance_threshold=args.relevance_threshold,
                    )
                ]
        print(json.dumps(output, ensure_ascii=False, indent=2))
    except (OSError, TypeError, ValueError, RuntimeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
