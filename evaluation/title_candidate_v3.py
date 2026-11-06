"""Source-title mixture; unrelated to the rejected v2 intent bonus.

Only source titles and raw embedding cosines are used. Scores remain separate.
The three alpha candidates are selected on NEW development queries only.
"""

from dataclasses import replace

from proyek_certan.knowledge.documents import DocumentResult


def rank_titles(
    results: list[DocumentResult], title_scores: dict[str, float], alpha: float
) -> list[DocumentResult]:
    if alpha not in (0.2, 0.4, 0.6):
        raise ValueError("alpha must be one of the preregistered candidates")
    updated = [
        replace(
            r,
            ranking_score=(1 - alpha) * r.similarity
            + alpha * title_scores[r.document_id],
            ranking_reason=f"(1-{alpha}) * best chunk cosine + {alpha} * source-title cosine; raw similarity unchanged.",
        )
        for r in results
    ]
    return sorted(updated, key=lambda r: r.ranking_score, reverse=True)
