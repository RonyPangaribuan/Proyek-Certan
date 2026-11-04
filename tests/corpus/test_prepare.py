"""Offline checks for provenance safeguards and structure-preserving HTML extraction."""

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from proyek_certan.corpus.prepare import (
    SourceUnavailable, _origin, _reusable_text, clean_text, extract_html_text,
    process_corpus, robots_allows,
)


def test_microsoft_body_keeps_headings_steps_code_and_table_without_chrome():
    html = b"""
    <main><nav>Site navigation</nav><div class="content"><h1>Network guide</h1></div>
      <div class="content"><h2>Troubleshooting</h2>
        <p>Check the switch and the server before continuing.</p>
        <ol><li>Check the link<ul><li>Inspect the port</li></ul></li><li>Run diagnostics</li></ol>
        <h3>Commands</h3><pre>netstat -anb\nping gateway</pre>
        <table><tr><th>Symptom</th><th>Action</th></tr><tr><td>Loss</td><td>Inspect cable</td></tr></table>
        <p>Record the observed error, affected interface, and time of failure. Compare the
        client and server traces before applying a configuration change, then retest the
        connection and document the result in the incident record.</p>
        <!-- SECTION HEADER -->
        <p>Try our Virtual Agent - help with wireless issues.</p>
        <aside>Related articles and cookie banner</aside><div class="feedback">Feedback widget</div>
      </div></main>
    """
    text = extract_html_text(html, "Microsoft Learn")
    assert "# Network guide" in text
    assert "## Troubleshooting" in text
    assert "1. Check the link" in text
    assert "  - Inspect the port" in text
    assert "2. Run diagnostics" in text
    assert "netstat -anb" in text and "ping gateway" in text
    assert "Symptom | Action" in text
    assert "Site navigation" not in text
    assert "cookie banner" not in text
    assert "Feedback widget" not in text
    assert "SECTION HEADER" not in text
    assert "Try our Virtual Agent" not in text


def test_dtsi_article_excludes_navigation_and_keeps_sop_table():
    html = b"""<main><nav>Beranda menu</nav><article class="md-content__inner">
        <h1>Insiden layanan</h1><h2>Prosedur penanganan</h2>
        <p>Catat insiden dan tentukan tingkat prioritas secara konsisten.</p>
        <table><tr><th>Prioritas</th><th>Aksi</th></tr><tr><td>P1</td><td>Eskalasi</td></tr></table>
        <ol><li>Buka tiket insiden</li><li>Verifikasi pemulihan</li></ol>
        <p>Dokumentasikan waktu deteksi, resolver, dan hasil uji.</p>
        <p>Setelah tindakan pemulihan, petugas menguji fungsi layanan dan memberi kabar
        kepada pelapor. Catat komunikasi, eskalasi, serta persetujuan penutupan tiket
        untuk mendukung penelusuran insiden berikutnya.</p>
      </article></main>"""
    text = extract_html_text(html, "DTSI Universitas Harapan Bangsa")
    assert "# Insiden layanan" in text
    assert "## Prosedur penanganan" in text
    assert "Prioritas | Aksi" in text
    assert "1. Buka tiket insiden" in text
    assert "Beranda menu" not in text


def test_openvswitch_faq_keeps_questions_answers_and_commands_without_navigation():
    html = b"""<main id="content"><nav>Navigation</nav><section id="vlans">
      <h1>VLANs<a class="headerlink" href="#vlans">&#182;</a></h1>
      <p>Q: Why is VLAN 9 not isolated?</p><blockquote><div>
      <p>A: Check the controller and whether NORMAL switching is active. Review
      the configured access port and trunk port before changing flows.</p>
      <pre>$ ovs-vsctl add-br br0\n$ ovs-vsctl add-port br0 tap0 tag=9</pre>
      <ul><li>Inspect port tags</li><li>Check OpenFlow actions</li></ul>
      <p>Compare the expected VLAN tag with the observed packet capture and
      document any mismatch. Repeat the connectivity test after the correction.</p>
      </div></blockquote></section><footer>Copyright banner</footer></main>"""
    text = extract_html_text(html, "Open vSwitch Project")
    assert text.startswith("# VLANs\n")
    assert "Q: Why is VLAN 9 not isolated?" in text
    assert "A: Check the controller" in text
    assert "$ ovs-vsctl add-port br0 tap0 tag=9" in text
    assert "- Inspect port tags" in text
    assert "Navigation" not in text and "Copyright banner" not in text and "¶" not in text


def test_existing_text_reused_only_with_matching_source_pdf_and_output_hash(tmp_path: Path):
    outfile = tmp_path / "DOC01_WiFi.txt"
    text = "# Existing output\n" + "Verified corpus text. " * 20
    outfile.write_text(text, encoding="utf-8")
    digest = hashlib.sha256(outfile.read_bytes()).hexdigest()
    previous = {
        "status": "processed", "source_url": "https://example.org/article",
        "source_pdf_sha256": "new-raw-hash", "text_file": f"data/corpus/processed/{outfile.name}",
        "sha256": digest, "character_count": len(text),
    }
    document = {"source_url": previous["source_url"]}
    assert _reusable_text(previous, document, "new-raw-hash", outfile) == text
    assert _reusable_text(previous, document, "old-raw-hash", outfile) is None
    assert _reusable_text(previous, {"source_url": "https://example.org/other"}, "new-raw-hash", outfile) is None
    outfile.write_text(text + "tampered", encoding="utf-8")
    assert _reusable_text(previous, document, "new-raw-hash", outfile) is None


def test_short_or_challenge_html_never_becomes_corpus_text():
    with pytest.raises(SourceUnavailable, match="terlalu pendek"):
        extract_html_text(b"<main><div class='content'><h1>Login</h1></div></main>", "Microsoft Learn")
    with pytest.raises(SourceUnavailable, match="challenge"):
        extract_html_text(
            b"<main><article><h1>Verify you are human</h1><p>" + b"Access denied. " * 40 +
            b"</p></article></main>", "Other publisher",
        )


def test_unapproved_http_or_host_is_rejected():
    with pytest.raises(SourceUnavailable):
        _origin("http://learn.microsoft.com/page")
    with pytest.raises(SourceUnavailable):
        _origin("https://example.invalid/page")
    with pytest.raises(SourceUnavailable):
        _origin("https://www.cisco.com/doc")


def test_invisible_template_characters_are_removed():
    assert clean_text("Incident\u200c response\u200b\n") == "Incident response\n"


def test_robots_disallow_is_respected_without_fetching_article():
    class Response:
        status_code = 200
        url = "https://learn.microsoft.com/robots.txt"
        encoding = "utf-8"
        headers = {"Content-Type": "text/plain"}

        def raise_for_status(self):
            return None

        def iter_content(self, chunk_size):
            yield b"User-agent: *\nDisallow: /en-us/troubleshoot/\n"

        def close(self):
            return None

    urls = []
    session = SimpleNamespace(get=lambda url, **kwargs: (urls.append(url), Response())[1])
    allowed, note = robots_allows(
        session, "https://learn.microsoft.com/en-us/troubleshoot/windows-server/networking/example", {}
    )
    assert allowed is False
    assert note == "robots.txt tersedia"
    assert urls == ["https://learn.microsoft.com/robots.txt"]


def test_manual_document_preserves_pdf_and_preexisting_text(tmp_path: Path):
    raw = tmp_path / "data/corpus/raw"
    raw.mkdir(parents=True)
    pdf = raw / "DOC06_LAN_Switch.pdf"
    pdf.write_bytes(b"original PDF bytes")
    original_hash = hashlib.sha256(pdf.read_bytes()).hexdigest()
    processed = tmp_path / "data/corpus/processed"
    processed.mkdir()
    existing = processed / "DOC06_LAN_Switch.txt"
    existing.write_text("manual work in progress", encoding="utf-8")
    evaluation = tmp_path / "evaluation"
    evaluation.mkdir()
    (evaluation / "pdf_validation.json").write_text(json.dumps({"documents": [{
        "filename": pdf.name, "sha256": original_hash, "extraction_status": "no_text",
    }]}), encoding="utf-8")
    (tmp_path / "data/corpus/corpus_manifest.json").write_text(json.dumps({"documents": [{
        "document_id": "DOC06", "filename": pdf.name, "source_url": "https://www.cisco.com/doc",
        "publisher": "Cisco", "automatic_extraction_allowed": False,
        "manual_reason": "permission must be checked", "source_status": "manual_required",
    }]}), encoding="utf-8")
    report = process_corpus(tmp_path)
    assert report["summary"] == {"document_count": 1, "processed_count": 0, "manual_required_count": 1}
    assert hashlib.sha256(pdf.read_bytes()).hexdigest() == original_hash
    assert existing.read_text(encoding="utf-8") == "manual work in progress"
    assert report["documents"][0]["text_file"] is None
