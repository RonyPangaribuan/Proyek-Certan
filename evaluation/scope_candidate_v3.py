"""Transparent query-level abstention for a STATIC document corpus.

Structural rules require a request type AND an unavailable data dependency.
Words such as 'sekarang', 'saya' or 'kampus' alone never trigger rejection.
The title evidence signal is a coverage heuristic, not answer verification.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Literal

from proyek_certan.knowledge.documents import CorpusCatalog, DocumentResult


@dataclass(frozen=True)
class GuardConfig:
    similarity_threshold: float = 0.5
    support_threshold: float = 0.0

    def __post_init__(self):
        for value in (self.similarity_threshold, self.support_threshold):
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or not -1 <= value <= 1
            ):
                raise ValueError("guard thresholds must be finite numbers in [-1, 1]")


@dataclass(frozen=True)
class ScopeDecision:
    status: Literal["ACCEPT", "ABSTAIN", "LOW_CONFIDENCE"]
    scope: str
    reason_codes: tuple[str, ...]
    reasons: tuple[str, ...]
    signals: dict
    warnings: tuple[str, ...] = ()
    results: tuple[DocumentResult, ...] = field(default_factory=tuple)


def unavailable_dependency(
    query: str, catalog: CorpusCatalog
) -> tuple[str, str] | None:
    """Conservative dependency checks; generic procedural help remains eligible."""
    q = query.casefold()
    procedural = bool(
        re.search(
            r"\b(cara|langkah|prosedur|panduan|troubleshooting|diagnosis|mendiagnosis)\b|"
            r"\bbagaimana\b.{0,65}\b(mem\w+|men\w+|meng\w+|mel\w+|mer\w+|cek)\b",
            q,
        )
    )
    request = bool(
        re.search(r"\b(apa|berapa|siapa|kapan|apakah|tampilkan|sebutkan|berikan)\b", q)
    )
    personal_or_live = bool(
        re.search(
            r"\b(saat ini|sekarang|sedang|terbaru|hari ini|malam ini|milik saya|kampus (saya|kami)|"
            r"(komputer|laptop|perangkat|gedung) (saya|kami))\b|\bakun\b.{0,30}\bsaya\b",
            q,
        )
    )
    factual_target = bool(
        re.search(
            r"\b(alamat (ip|mac)|ip aktif|ip (laptop|komputer|perangkat)|password|kata sandi|trafik|traffic|bandwidth|throughput|status|"
            r"tiket|teknisi|petugas|pemilik|piket|daftar pemilik)\b|"
            r"\bkapan\b.{0,90}\b(pulih|selesai|diperbaiki)\b|"
            r"\bsiapa\b.{0,70}\b(mengelola|menangani|bertugas)\b",
            q,
        )
    )
    record_lookup = bool(re.search(r"\b(?:INC|REQ|CHG|TKT)[-_]?\d{3,}\b", query, re.I))
    if (
        request
        and not procedural
        and ((personal_or_live and factual_target) or record_lookup)
    ):
        return (
            "operational_data",
            "Korpus berisi dokumen statis; permintaan ini memerlukan data perangkat, akun, tiket, petugas, atau status layanan aktual yang tidak tersedia.",
        )
    authority = bool(
        re.search(
            r"\b(aturan|kebijakan|ketentuan|sop|sla|resmi|menurut|berwenang|persetujuan)\b",
            q,
        )
    )
    if authority:
        names = re.findall(
            r"\b(?:[Uu]niversitas|[Ii]nstitut|[Kk]ampus|[Uu]niversity(?: of)?|[Cc]ollege)\s+"
            r"([A-Z][A-Za-z]*(?:\s+[A-Z][A-Za-z]*){0,3})",
            query,
        )
        names += re.findall(
            r"\b[Mm]enurut\s+([A-Z][A-Za-z]*(?:\s+[A-Z][A-Za-z]*){0,3})", query
        )
        if re.search(r"\b(resmi|disahkan|berlaku)\b", q):
            names += re.findall(
                r"\b(?:untuk|di|pada)\s+([A-Z][A-Za-z]*(?:\s+[A-Z][A-Za-z]*){0,3})",
                query,
            )
        for name in names:
            if name.casefold() in {
                "university",
                "universitas",
                "institut",
                "kampus",
                "college",
            }:
                continue  # Organizational noun; the actual name is captured above.
            if not catalog.supports_institution(name):
                return (
                    "unsupported_institution",
                    "Tidak ada sumber institusi yang diminta dalam inventaris korpus; kebijakan institusi lain tidak dapat dianggap berlaku untuk institusi tersebut.",
                )
    return None


class ScopeGuard:
    def __init__(self, config: GuardConfig | None = None):
        self.config = config or GuardConfig()

    def evaluate(
        self,
        query: str,
        results: list[DocumentResult],
        *,
        title_support: float | None,
        catalog: CorpusCatalog,
    ) -> ScopeDecision:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string")
        signal = {
            "raw_top_similarity": results[0].similarity if results else None,
            "title_support": title_support,
            "similarity_threshold": self.config.similarity_threshold,
            "support_threshold": self.config.support_threshold,
            "inventory_document_count": len(catalog.documents),
        }
        dependency = unavailable_dependency(query, catalog)
        if dependency:
            scope, reason = dependency
            return ScopeDecision("ABSTAIN", scope, (scope,), (reason,), signal)
        if not results:
            return ScopeDecision(
                "ABSTAIN",
                "no_evidence",
                ("empty_candidates",),
                ("Tidak ada kandidat sumber pada indeks ini.",),
                signal,
            )
        codes, reasons = [], []
        if results[0].similarity < self.config.similarity_threshold:
            codes.append("low_cosine")
            reasons.append(
                "Kemiripan kandidat tertinggi berada di bawah ambang yang dikalibrasi."
            )
        if self.config.support_threshold > 0 and (
            title_support is None or title_support < self.config.support_threshold
        ):
            codes.append("weak_source_coverage")
            reasons.append(
                "Kesesuaian kueri dengan judul sumber kandidat belum cukup kuat untuk memastikan cakupan pengetahuan."
            )
        if codes:
            return ScopeDecision(
                "LOW_CONFIDENCE",
                "insufficient_evidence",
                tuple(codes),
                tuple(reasons),
                signal,
            )
        warnings = []
        if str(results[0].metadata.get("publication_status", "")).upper() == "DRAFT":
            warnings.append(
                "Sumber teratas masih DRAFT; relevansi topik tidak berarti prosedurnya sudah disahkan."
            )
        if results[0].metadata.get("review_required"):
            warnings.append("Sumber teratas masih memiliki catatan review.")
        return ScopeDecision(
            "ACCEPT",
            "document_knowledge",
            ("supported_candidate",),
            (
                "Permintaan dapat diarahkan ke pengetahuan dokumen; hasil tetap perlu diperiksa terhadap sumber.",
            ),
            signal,
            tuple(warnings),
            tuple(results),
        )
