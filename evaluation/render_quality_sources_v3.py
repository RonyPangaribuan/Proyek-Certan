"""Optional PDFium visual QA; does not alter PDFs, corpus text or retrieval.

Install QA-only renderer: uv pip install --python .venv/Scripts/python.exe pypdfium2==5.14.0
PNG encoding uses stdlib and numpy; Pillow is not needed.
"""

import hashlib
import json
import struct
import zlib
from datetime import UTC, datetime
from pathlib import Path

import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".local/quality-v3-visual"


def encode_png(a):
    def chunk(kind, data):
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    height, width, _ = a.shape
    raw = b"".join(b"\x00" + a[i, :, :3].tobytes() for i in range(height))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


def main():
    report = ROOT / "evaluation/quality-v3/visual_review.json"
    if report.exists():
        raise FileExistsError("Visual evidence already recorded")
    OUT.mkdir(parents=True, exist_ok=True)
    documents = []
    for doc_id, name, pages in [
        ("DOC11", "DOC11_Incident_Management_UCF", [1, 2, 5, 6, 9]),
        ("DOC13", "DOC13_Network_Administration", [1, 2, 3, 4, 5]),
    ]:
        path = ROOT / f"data/corpus/raw/{name}.pdf"
        doc = pdfium.PdfDocument(path)
        images = []
        for page in pages:
            data = encode_png(
                doc[page - 1].render(scale=1.35, rev_byteorder=True).to_numpy()
            )
            target = OUT / f"{name}-p{page}.png"
            if target.exists() and target.read_bytes() != data:
                raise ValueError("Previous render differs")
            if not target.exists():
                target.write_bytes(data)
            images.append(
                dict(
                    page=page,
                    image=target.relative_to(ROOT).as_posix(),
                    png_sha256=hashlib.sha256(data).hexdigest(),
                )
            )
        documents.append(
            dict(
                document_id=doc_id,
                source_pdf_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                inspected_pages=pages,
                images=images,
            )
        )
    value = dict(
        recorded_at_utc=datetime.now(UTC).isoformat(),
        renderer="pypdfium2 5.14.0",
        render_scale=1.35,
        reviewer="Assistant visual inspection, not independent human/source-owner approval.",
        documents=documents,
        findings=dict(
            DOC11="Legal notice, objectives and definitions reflow verified on pages 1/2. Tables Figure 1.1/1.2 and closure email inspected on pages 5/6/9. Flattened cell associations and diagrams remain unresolved; no semantic reconstruction attempted.",
            DOC13="All five pages inspected; front title, executive role and history reflow preserve source tokens, clause numbers and contact data. Current 2024 PDF provenance preserved.",
        ),
    )
    with report.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(
        "Recorded visual inspection and deterministic hashes of ten source page renders."
    )


if __name__ == "__main__":
    main()
