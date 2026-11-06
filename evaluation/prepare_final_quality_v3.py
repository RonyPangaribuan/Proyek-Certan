"""Author the synthetic final test only AFTER the final implementation lock.

This authoring module does not import models or read observation/result files.
The same author knows the design: this is a tuning holdout, not a blind human study.
"""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/quality-v3"
POS = [
    (
        "Bagaimana mengisolasi perbedaan manual-connect dan auto-connect pada kegagalan WLAN?",
        "wifi",
        ["DOC01"],
        "Step 1 manual/auto connection.",
    ),
    (
        "Apa pemeriksaan driver NIC dan versi OS ketika hanya sebagian pengguna wireless yang terdampak?",
        "wifi",
        ["DOC01"],
        "Step 1 client common factors.",
    ),
    (
        "WLAN di Universitas Kencana sedang gagal; bagaimana prosedur umum diagnosis sambungan tanpa mengasumsikan SOP kampus?",
        "wifi",
        ["DOC01"],
        "Generic troubleshooting; no institution-specific policy requested.",
    ),
    (
        "Bagaimana langkah restart WlanSvc dan pengujian koneksi ulang untuk wireless Windows?",
        "wifi",
        ["DOC01"],
        "Step 2 restart WLAN Autoconfig.",
    ),
    (
        "Bagaimana menelusuri resolusi nama DNS dari sisi client dan sisi server?",
        "dns_dhcp",
        ["DOC02"],
        "Server-side/client-side checklist.",
    ),
    (
        "Apa penyebab catatan DNS hilang setelah IP host berganti?",
        "dns_dhcp",
        ["DOC02"],
        "DNS common issues, missing records/dynamic update.",
    ),
    (
        "Bagaimana prosedur mengumpulkan event log DHCP client untuk investigasi sewa alamat?",
        "dns_dhcp",
        ["DOC03", "DOC04"],
        "Both documents support client event logs.",
    ),
    (
        "Apa pemeriksaan scope dan layanan ketika server DHCP berhenti mengalokasikan IP?",
        "dns_dhcp",
        ["DOC03"],
        "Server troubleshooting checklist.",
    ),
    (
        "Mengapa VLAN trunk diperlukan untuk menghubungkan beberapa switch tanpa satu kabel per VLAN?",
        "vlan_switching",
        ["DOC06"],
        "VLAN/trunk FAQ explanation.",
    ),
    (
        "Bagaimana menyelidiki trafik VLAN bertag yang kembali tanpa tag ke port fisik OVS?",
        "vlan_switching",
        ["DOC06"],
        "Native VLAN return path FAQ.",
    ),
    (
        "Mengapa aturan flow kustom pada controller OpenFlow perlu menangani VLAN sendiri?",
        "vlan_switching",
        ["DOC06"],
        "Normal switching action and controller FAQ.",
    ),
    (
        "Bagaimana memeriksa perbedaan konektivitas loopback, IP host sendiri, dan default gateway?",
        "diagnosis_other",
        ["DOC05"],
        "TCP/IP ping checklist.",
    ),
    (
        "Bagaimana menafsirkan drop lokal Pktmon ketika tidak ada socket di port UDP tujuan?",
        "diagnosis_other",
        ["DOC07"],
        "Packet Monitor trace example and transport endpoint.",
    ),
    (
        "Bagaimana mengaktifkan pencatatan keberhasilan dan kegagalan Network Policy Server untuk 802.1X?",
        "diagnosis_other",
        ["DOC08"],
        "Audit policy section.",
    ),
    (
        "Menurut Oregon State University siapa yang menyetujui dan memasang access point yang terhubung ke jaringan universitas?",
        "network_policy",
        ["DOC13"],
        "5.3.1 UIT NOC approval and installation.",
    ),
    (
        "Menurut Oregon State University bagaimana pengecualian kebijakan perangkat jaringan diberikan?",
        "network_policy",
        ["DOC13"],
        "5.5.1 Vice Provost IT & CIO.",
    ),
    (
        "Apa larangan pemalsuan identitas pengguna pada kebijakan Western Michigan University?",
        "network_policy",
        ["DOC14"],
        "4.3.5 misrepresentation.",
    ),
    (
        "Menurut Western Michigan University apakah pelanggaran penggunaan Internet dapat menyebabkan pemutusan koneksi?",
        "network_policy",
        ["DOC14"],
        "Accountability: connection termination.",
    ),
    (
        "Menurut Indiana University Bloomington apa aturan memperluas sambungan layer 2 ke ruangan lain?",
        "network_policy",
        ["DOC15"],
        "Network Management requirement prohibits extending beyond room.",
    ),
    (
        "Dalam contoh draf service desk UHB apa informasi yang dicatat untuk melakukan handoff eskalasi?",
        "incident_management",
        ["DOC09"],
        "8.1 and 8.3; DRAFT topical support.",
    ),
    (
        "Dalam draf penanganan insiden layanan bagaimana workaround dan hotfix dikendalikan saat pemulihan?",
        "incident_management",
        ["DOC10"],
        "7.4 recovery and RFC for configuration/code changes.",
    ),
    (
        "Menurut UCF apakah prioritas Critical, High dan Normal harus ditetapkan ketika tiket dibuat?",
        "incident_management",
        ["DOC11"],
        "V.B incident categorization and prioritization.",
    ),
    (
        "Menurut University of Central Florida apakah email otomatis menghapus kewajiban assignee menghubungi pelanggan?",
        "incident_management",
        ["DOC11"],
        "V.G closure, automated email does not negate contacting customer.",
    ),
    (
        "Menurut University of Utah ke unit mana laporan dugaan insiden keamanan informasi diteruskan?",
        "incident_management",
        ["DOC12"],
        "Report through help desk/ISO and response team.",
    ),
]
NEG = [
    (
        "Berapa alamat IP notebook saya yang aktif sekarang?",
        "live_data",
        "No live endpoint state.",
    ),
    (
        "Tampilkan nama pemilik laptop yang sedang memakai jaringan kami.",
        "live_data",
        "No inventory or identity database.",
    ),
    (
        "Apakah tiket REQ773366 sudah ditutup oleh petugas?",
        "live_data",
        "No ticket records.",
    ),
    (
        "Siapa petugas jaringan yang sedang piket di kampus kami?",
        "live_data",
        "No staff roster.",
    ),
    (
        "Tolong berikan kata sandi terkini untuk akun WiFi milik saya.",
        "live_data",
        "No personal credentials.",
    ),
    (
        "Kapan koneksi ISP kampus kami akan pulih dari gangguan yang sedang terjadi?",
        "live_data",
        "No live outage/ETA.",
    ),
    (
        "Alamat default gateway yang dipakai laptop saya sekarang apa?",
        "live_data",
        "No live route/configuration data.",
    ),
    (
        "Berapa jumlah lease DHCP yang aktif di server kampus kami hari ini?",
        "live_data",
        "No live DHCP server telemetry.",
    ),
    (
        "Apa aturan pemasangan access point menurut Universitas Teratai?",
        "institution",
        "Institution not represented.",
    ),
    (
        "Siapa pemberi izin instalasi kabel jaringan di Institut Cendana?",
        "institution",
        "Institution not represented.",
    ),
    (
        "Berapa batas SLA insiden P1 yang resmi berlaku di Universitas Mandiri?",
        "institution",
        "No approved local SLA/source.",
    ),
    (
        "Apa kebijakan pembuatan jaringan nirkabel sendiri menurut Universitas Pusaka?",
        "institution",
        "Institution not represented.",
    ),
    (
        "Apa sanksi akses Internet terlarang menurut Universitas Kemuning?",
        "institution",
        "Institution not represented.",
    ),
    (
        "Menurut College Aurora siapa berhak memberi pengecualian aturan LAN?",
        "institution",
        "Institution not represented.",
    ),
    (
        "apa aturan penggunaan wifi di universitas melati?",
        "institution",
        "Institution not represented; lower-case name stress test.",
    ),
    (
        "siapa yang berwenang memasang switch di institut seruni?",
        "institution",
        "Institution not represented; lower-case name stress test.",
    ),
    (
        "Apa jadwal ujian akhir semester mahasiswa sistem informasi?",
        "outside_domain",
        "No academic schedules.",
    ),
    (
        "Bagaimana mengajukan cuti akademik satu semester?",
        "outside_domain",
        "No academic administration.",
    ),
    (
        "Bagaimana memilih pupuk untuk tanaman tomat?",
        "outside_domain",
        "No agriculture source.",
    ),
    (
        "Bagaimana prosedur fisioterapi setelah cedera lutut?",
        "outside_domain",
        "No medical source.",
    ),
    (
        "Bagaimana menyusun laporan neraca usaha tahunan?",
        "outside_domain",
        "No accounting source.",
    ),
    (
        "Bagaimana cara memesan kamar hotel untuk rombongan?",
        "outside_domain",
        "No hospitality booking source.",
    ),
    (
        "Apa command Cisco IOS untuk konfigurasi port-security pada switch Catalyst?",
        "outside_domain",
        "No Cisco IOS command reference; OVS FAQ is not direct support.",
    ),
    (
        "Bagaimana mendiagnosis ImagePullBackOff di Kubernetes?",
        "outside_domain",
        "No Kubernetes/container documentation.",
    ),
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_once(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write("\n")


def main():
    lock = OUT / "lock-r2.json"
    if not lock.exists():
        raise ValueError("Final candidate lock required first")
    if (OUT / "observations_validation.json").exists() or (
        OUT / "observations_final_test.json"
    ).exists():
        raise ValueError(
            "Author final labels before observing validation/final results"
        )
    known = set()
    for p in [
        ROOT / "evaluation/semantic_retrieval_ground_truth.json",
        ROOT / "evaluation/retrieval_study_labels_v2.json",
        OUT / "development.json",
        OUT / "validation.json",
    ]:
        known.update(
            q["query"] for q in json.loads(p.read_text(encoding="utf-8"))["queries"]
        )
    queries = []
    for i, (q, category, docs, evidence) in enumerate(POS, 1):
        queries.append(
            dict(
                id=f"final_p{i:02}",
                query=q,
                category=category,
                relevant_documents=docs,
                evidence=evidence,
            )
        )
    for i, (q, category, evidence) in enumerate(NEG, 1):
        queries.append(
            dict(
                id=f"final_o{i:02}",
                query=q,
                category=category,
                relevant_documents=[],
                evidence=evidence,
            )
        )
    for q in queries:
        if q["query"] in known:
            raise ValueError("Query duplicated from seen labels")
        known.add(q["query"])
    labels = OUT / "final_test.json"
    write_once(
        labels,
        dict(
            split="final_test",
            annotation="Post-lock synthetic source-grounded holdout; not independent human validation.",
            queries=queries,
        ),
    )
    write_once(
        OUT / "final_test_manifest.json",
        dict(
            frozen_at_utc=datetime.now(UTC).isoformat(),
            lock_file="lock-r2.json",
            lock_sha256=sha(lock),
            labels_sha256=sha(labels),
            authoring_code_sha256=sha(Path(__file__)),
            positive_count=24,
            ood_count=24,
            query_uniqueness_verified=True,
            ranking_outputs_read=False,
        ),
    )
    corpus = json.loads(
        (ROOT / "evaluation/reviewed_corpus_v3.json").read_text(encoding="utf-8")
    )
    sources = [
        dict(
            document_id=d["document_id"],
            title=d["title"],
            publisher=d["publisher"],
            source_url=d["verified_source_url"],
            original_pdf=f"data/corpus/raw/{d['filename']}",
            reviewed_text=d["revised_text_file"],
            publication_status=d.get("publication_status"),
        )
        for d in corpus["documents"]
    ]
    all_queries = []
    for split in ("development", "validation", "final_test"):
        for q in json.loads((OUT / f"{split}.json").read_text(encoding="utf-8"))[
            "queries"
        ]:
            all_queries.append(
                dict(
                    query_id=q["id"],
                    query=q["query"],
                    annotator_id=None,
                    status=None,
                    relevant_documents=None,
                    evidence=[
                        dict(document_id=None, section=None, page=None, reason=None)
                    ],
                    confidence=None,
                    annotated_at=None,
                )
            )
    write_once(
        OUT / "independent_annotation_template.json",
        dict(
            instructions="Read annotation-guide-v3.md. No ranking, predicted decision or author ground truth included. Blank means unannotated, NOT OOD.",
            sources=sources,
            annotations=all_queries,
        ),
    )
    write_once(
        OUT / "development_amendment.json",
        dict(
            reason="Development uncovered the generic noun University being parsed as a separate unsupported institution in full University of ... names. Fixed generic organizational noun handling and added regression test before validation/final observations. Removed unused title encoding when support threshold is zero.",
            first_lock_preserved="lock.json",
            first_results_preserved="results_development.json",
            active_lock="lock-r2.json",
            active_results="results_development_r2.json",
            no_validation_or_final_results_seen=True,
            old_75_labels_unchanged=True,
        ),
    )
    print(
        "Frozen 48 final test queries AFTER lock-r2, BEFORE validation/final observations; blank independent annotation template exported."
    )


if __name__ == "__main__":
    main()
