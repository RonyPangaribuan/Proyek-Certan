"""Official final-corpus entry point, delegating encoding and ranking unchanged."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import asdict
import json
from pathlib import Path
import sys

from proyek_certan.knowledge.embeddings import EmbeddingModel
from proyek_certan.knowledge.final_corpus import load_final_corpus, verify_index
from proyek_certan.knowledge.retrieval import KnowledgeRetriever
from proyek_certan.knowledge.vector_store import VectorStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CERTAN: one audited final corpus")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("verify", "index", "search"):
        command = commands.add_parser(name)
        command.add_argument("--db", type=Path, help="isolated database override")
        if name == "verify":
            command.add_argument(
                "--index", action="store_true", help="also verify persisted index"
            )
        if name == "search":
            command.add_argument("--query", required=True)
            command.add_argument("--top-k", type=int, default=3)
            command.add_argument("--document-level", action="store_true")
            command.add_argument("--candidate-depth", type=int, default=100)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        corpus = load_final_corpus()
        db = args.db.resolve() if args.db else corpus.database_path
        if args.command == "verify" and not args.index:
            output = {
                "corpus": "PASS",
                "documents": 15,
                "chunks": len(corpus.chunks),
                "profile": corpus.manifest["profile"],
            }
        else:
            if args.command != "index" and not (db / "chroma.sqlite3").is_file():
                raise ValueError("Final index is missing; run final_cli index first")
            with VectorStore(
                db, model_name=corpus.manifest["embedding"]["model_name"]
            ) as store:
                if args.command == "index":
                    # Upsert does not remove old IDs. Refuse a mixed index before encoding.
                    if store.count():
                        verify_index(store, corpus)
                    retriever = KnowledgeRetriever(
                        store, EmbeddingModel(cache_folder=corpus.model_cache)
                    )
                    indexed = retriever.index_chunks(corpus.chunks)
                    output = {
                        "indexed": indexed,
                        "verified": verify_index(store, corpus),
                    }
                else:
                    verified = verify_index(store, corpus)
                    if args.command == "verify":
                        output = {"corpus": "PASS", "index": "PASS", **verified}
                    else:
                        retriever = KnowledgeRetriever(
                            store, EmbeddingModel(cache_folder=corpus.model_cache)
                        )
                        if args.document_level:
                            found = retriever.search_documents(
                                args.query,
                                top_k=args.top_k,
                                candidate_depth=args.candidate_depth,
                            )
                        else:
                            found = retriever.search(args.query, top_k=args.top_k)
                        output = [asdict(item) for item in found]
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0
    except (OSError, KeyError, TypeError, ValueError, RuntimeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
