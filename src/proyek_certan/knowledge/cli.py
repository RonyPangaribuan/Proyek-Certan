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


def build_parser() -> argparse.ArgumentParser:
    """Build separate index and search commands without modifying the M1 CLI."""
    parser = argparse.ArgumentParser(description="CERTAN T03 semantic knowledge search")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("index", "search"):
        command = commands.add_parser(name)
        command.add_argument("--db", type=Path, default=None, help="persistent database directory")
        command.add_argument("--model-cache", type=Path, default=None, help="model cache directory")
        if name == "index":
            command.add_argument("--input", type=Path, required=True, help="JSON array of chunks")
        else:
            command.add_argument("--query", required=True)
            command.add_argument("--top-k", type=int, default=3)
            command.add_argument("--relevance-threshold", type=float, default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Index chunks or print structured retrieval results as JSON."""
    args = build_parser().parse_args(argv)
    try:
        with VectorStore(args.db) as store:
            retriever = KnowledgeRetriever(
                store, EmbeddingModel(cache_folder=args.model_cache)
            )
            if args.command == "index":
                chunks = json.loads(args.input.read_text(encoding="utf-8"))
                if not isinstance(chunks, list):
                    raise ValueError("input must be a JSON array of chunks")
                output = {"indexed": retriever.index_chunks(chunks), "collection_count": store.count()}
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
