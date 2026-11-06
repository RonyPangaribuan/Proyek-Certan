"""Local source extraction preserves meaningful structure and refuses overwrites."""
import pytest
from proyek_certan.corpus.prepare import SourceUnavailable, clean_text, extract_html_text, main, exact_page_span


def test_page_span_requires_unique_exact_source_words():
    index = (["alpha", "beta", "gamma", "alpha"], [1, 1, 2, 2])
    assert exact_page_span("beta gamma", "Title", index)["page_end"] == 2
    assert exact_page_span("alpha", "Title", index) == {}
    assert exact_page_span("invented text", "Title", index) == {}


def test_local_ingestion_never_overwrites_existing_review(tmp_path):
    source = tmp_path / "source.txt"
    target = tmp_path / "review.txt"
    source.write_text("# Network\nCheck the port.\n", encoding="utf-8")
    args = ["--input", str(source), "--kind", "text", "--title", "Network", "--output", str(target)]
    assert main(args) == 0
    original = target.read_bytes()
    with pytest.raises(SystemExit):
        main(args)
    assert target.read_bytes() == original

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


def test_short_or_challenge_html_never_becomes_corpus_text():
    with pytest.raises(SourceUnavailable, match="terlalu pendek"):
        extract_html_text(b"<main><div class='content'><h1>Login</h1></div></main>", "Microsoft Learn")
    with pytest.raises(SourceUnavailable, match="challenge"):
        extract_html_text(
            b"<main><article><h1>Verify you are human</h1><p>" + b"Access denied. " * 40 +
            b"</p></article></main>", "Other publisher",
        )


def test_invisible_template_characters_are_removed():
    assert clean_text("Incident\u200c response\u200b\n") == "Incident response\n"
