"""Author source-grounded query labels and freeze the protocol BEFORE retrieval.

This file contains no model/store imports. It never reads retrieval outputs.
Existing labels/protocol cannot be overwritten: use a new study version.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# (category, query, relevant document IDs, source evidence).
DEV = [
    (
        "diagnosis",
        "Sambungan WiFi gagal terbentuk pada beberapa laptop dengan SSID yang sama. Bagaimana diagnosis klien dan AP?",
        ["DOC01"],
        "Step 1: common NIC/OS, failed establishment versus drops, common SSID/AP.",
    ),
    (
        "synonym",
        "Koneksi nirkabel terputus sesudah tersambung. Apa yang perlu diperiksa untuk membedakan gangguan klien dan titik akses?",
        ["DOC01"],
        "Step 1 questions 1, 3 and 4 distinguish clients, connection drops and access points.",
    ),
    (
        "diagnosis",
        "Bagaimana troubleshooting cache DNS pada klien Windows ketika resolusi nama bermasalah?",
        ["DOC02"],
        "Common issues: Support policy for DNS client-side caching on DNS clients.",
    ),
    (
        "diagnosis",
        "DHCP server tidak memberikan lease. Apa checklist service, scope dan alamat yang tersedia?",
        ["DOC03"],
        "Troubleshoot DHCP servers: service, scope, address leases and availability.",
    ),
    (
        "synonym",
        "Klien gagal mendapat sewa alamat dinamis. Di mana event log DHCP client yang harus dikumpulkan?",
        ["DOC03", "DOC04"],
        "DOC03 Event logs and Troubleshoot DHCP clients; DOC04 Event logs and Data collection.",
    ),
    (
        "diagnosis",
        "Ping alamat lokal berhasil tetapi default gateway gagal. Bagaimana troubleshooting TCP/IP berikutnya?",
        ["DOC05"],
        "Checklist steps 3, 4 and 5: local IP, ping errors and default gateway.",
    ),
    (
        "diagnosis",
        "OVS menerima trafik balik tanpa tag pada native VLAN. Bagaimana cek native-tagged dan port switch fisik?",
        ["DOC06"],
        "FAQ: outgoing tagged traffic and incoming return traffic, native VLAN alternatives.",
    ),
    (
        "synonym",
        "Bagaimana memakai Pktmon untuk mencari paket yang drop lokal dan memeriksa counter discard NIC?",
        ["DOC07"],
        "Capture and diagnose packet loss; common causes of local packet loss.",
    ),
    (
        "diagnosis",
        "Autentikasi 802.1X gagal dengan event NPS 6273. Apa yang diperiksa pada sertifikat EAP?",
        ["DOC08"],
        "Troubleshooting: NPS events 6272/6273 and certificate issues.",
    ),
    (
        "incident",
        "Apa data minimum ketika agen service desk membuka tiket dan mengeskalasi dari L1 ke L2?",
        ["DOC09"],
        "OPS-01 8.1 recording and 8.3 escalation handoff; source DRAFT.",
    ),
    (
        "incident",
        "Dalam penanganan gangguan layanan, kapan membuat laporan pascainsiden P1 dan apa isinya?",
        ["DOC10"],
        "INC-02 7.6: timeline, impact, actions and lessons; deadline placeholder; DRAFT.",
    ),
    (
        "incident",
        "Menurut prosedur UCF, apakah eskalasi insiden mengubah kode prioritas tiket?",
        ["DOC11"],
        "V.B.a: Escalation of an incident DOES NOT change the Priority code.",
    ),
    (
        "incident",
        "Menurut P4-004N Utah, ke mana dugaan insiden keamanan informasi dilaporkan?",
        ["DOC12"],
        "Procedure: report suspected security incidents to help desk/ISO, escalation and IRT.",
    ),
    (
        "network_policy",
        "Menurut kebijakan Oregon State, apakah access point Wi-Fi pribadi boleh dipasang tanpa izin UIT?",
        ["DOC13"],
        "5.3.1: UIT NOC approval and installation; unauthorised APs prohibited.",
    ),
    (
        "network_policy",
        "Apakah kebijakan WMU melarang meneruskan akses Internet ke pengguna lain?",
        ["DOC14"],
        "Full Policy Details 4.3.3 prohibits retransmission inside or outside the community.",
    ),
    (
        "network_policy",
        "Menurut Network Management Indiana, bagaimana aturan inventaris alamat MAC dan nama DNS untuk IP statis?",
        ["DOC15"],
        "Requirement Statement: MAC inventory and primary DNS name for static IP devices.",
    ),
    (
        "network_policy",
        "Siapa berwenang melakukan instalasi dan maintenance perangkat jaringan kabel di Oregon State?",
        ["DOC13"],
        "5.2.3: UIT or UIT-approved Network Administrator.",
    ),
    (
        "synonym",
        "Layanan terganggu, ada solusi sementara dan akar masalah belum hilang. Bagaimana alur pemulihan dan penutupan insiden?",
        ["DOC09", "DOC10", "DOC11"],
        "OPS-01 8.4; INC-02 7.4/7.5; UCF work around, incident resolution and closure.",
    ),
]
EVAL = [
    (
        "diagnosis",
        "WiFi sudah tersambung namun koneksi sering drop pada satu access point. Bagaimana memeriksa SSID dan klien terdampak?",
        ["DOC01"],
        "Step 1: affected clients, establishment/drop distinction and shared SSID/AP.",
    ),
    (
        "synonym",
        "Jaringan nirkabel Windows gagal tersambung. Bagaimana cek WlanSvc, connection manager pihak ketiga dan group policy?",
        ["DOC01"],
        "Step 2: restart WLAN Autoconfig, remove connection managers and test group policy.",
    ),
    (
        "diagnosis",
        "Record A hilang dari zona DNS setelah perubahan IP. Bagaimana memeriksa scavenging dan dynamic update?",
        ["DOC02"],
        "DNS records missing: scavenging, changed IP and dynamic update issues.",
    ),
    (
        "diagnosis",
        "Bagaimana mengambil network trace DHCP dengan Wireshark secara bersamaan di server dan klien yang tidak mendapat IP?",
        ["DOC03", "DOC04"],
        "DOC03 Using network trace / steps; DOC04 Data collection with simultaneous Wireshark capture.",
    ),
    (
        "synonym",
        "Komunikasi TCP/IP ke host tujuan macet. Bagaimana mengumpulkan diagram jaringan dan trace sebelum eskalasi?",
        ["DOC05"],
        "Checklist steps 1/2 and connection-to-host-stopped discussion.",
    ),
    (
        "diagnosis",
        "VM di VLAN berbeda masih saling mengakses ketika OpenFlow controller aktif. Apa yang harus dicek pada normal switching?",
        ["DOC06"],
        "FAQ isolation with controller; VLAN DB applies to normal action, custom flows handle VLANs.",
    ),
    (
        "diagnosis",
        "Paket hilang di jaringan remote. Bagaimana menafsirkan retransmission TCP dan trace Packet Monitor?",
        ["DOC07"],
        "Common causes of remote packet loss; example traces show unacknowledged TCP and retransmission.",
    ),
    (
        "diagnosis",
        "Bagaimana mengaktifkan audit policy NPS untuk diagnosis penolakan autentikasi jaringan 802.1X?",
        ["DOC08"],
        "Audit policy: auditpol for Network Policy Server success/failure events.",
    ),
    (
        "incident",
        "Dalam SOP service desk, bagaimana triage membedakan permintaan layanan, insiden operasional dan insiden keamanan?",
        ["DOC09"],
        "8.1/8.2 route OPS-10, INC-02 and parallel INC-01; DRAFT.",
    ),
    (
        "incident",
        "Dalam pemulihan insiden P1, kapan hotfix perlu RFC dan siapa menyetujui penutupan?",
        ["DOC10"],
        "7.4.2 RFC for configuration/code; 7.5.1 incident manager/service owner approval; DRAFT.",
    ),
    (
        "incident",
        "Menurut UCF, ketika status Awaiting User Confirmation apakah email otomatis menggantikan kewajiban menghubungi pengguna?",
        ["DOC11"],
        "V.G incident closure: automated email DOES NOT negate assignee contacting customer to confirm resolution.",
    ),
    (
        "incident",
        "Siapa yang mengoordinasikan Incident Response Team dan komunikasi insiden keamanan pada prosedur Utah?",
        ["DOC12"],
        "CISO/ISO directs IRT response and coordinates communication.",
    ),
    (
        "network_policy",
        "Siapa berwenang memberi pengecualian kebijakan jaringan Oregon State dan dapatkah UIT memutus perangkat berisiko?",
        ["DOC13"],
        "5.4.2/5.4.3 disconnection and 5.5 exceptions by Vice Provost IT & CIO.",
    ),
    (
        "network_policy",
        "Menurut aturan WMU, apakah memalsukan identitas dan memakai alamat IP milik orang lain dilarang?",
        ["DOC14"],
        "4.3.4 interference/IP not registered and 4.3.5 identity misrepresentation.",
    ),
    (
        "network_policy",
        "Bagaimana persetujuan pengecualian jaringan untuk riset di College Indiana dan lewat sistem tiket apa?",
        ["DOC15"],
        "Exceptions: CITRIS, security/policy IT leaders and UITS; standard College IT ServiceNow.",
    ),
    (
        "network_policy",
        "Apa kebijakan Indiana mengenai memasang router, wireless network sendiri dan memperpanjang jaringan melewati ruang jack?",
        ["DOC15"],
        "Requirement Statement prohibits L2 extension beyond room, L3 routers and wireless deployment.",
    ),
    (
        "synonym",
        "Pengguna tak bisa membuka nama domain. Bagaimana cek DNS sisi server dan sisi client?",
        ["DOC02"],
        "Troubleshooting checklist, server-side and client-side issues.",
    ),
    (
        "network_policy",
        "Di WMU, apa sanksi pelanggaran penggunaan jaringan dan siapa memberi pengecualian kebijakan?",
        ["DOC14"],
        "Full Policy 4.5 exceptions and 5 Accountability: connection termination, suspension, legal action.",
    ),
]
OOD_DEV = [
    (
        "far",
        "Bagaimana resep membuat rendang untuk empat orang?",
        "No cooking instructions in any of the 15 documents.",
    ),
    (
        "far",
        "Siapa pencipta lagu Indonesia Raya dan tahun berapa diciptakan?",
        "No music history in the corpus.",
    ),
    (
        "far",
        "Apa jadwal ujian kalkulus kelas A minggu depan?",
        "No course/exam schedules in the corpus.",
    ),
    (
        "far",
        "Berapa nilai tukar rupiah terhadap yen saat ini?",
        "No live foreign-exchange data.",
    ),
    (
        "near",
        "Apa nama SSID dan kata sandi WiFi CERTAN yang berlaku hari ini?",
        "Generic diagnosis/policies contain no CERTAN deployed SSID or passwords.",
    ),
    (
        "near",
        "Berikan konfigurasi BGP peering dengan ASN ISP kampus CERTAN.",
        "No BGP peering configuration or local ASN in the corpus.",
    ),
    (
        "near",
        "Perintah konfigurasi VLAN pada Cisco IOS versi 17 untuk switch saya apa?",
        "VLAN instructions are Open vSwitch, no Cisco IOS configuration manual.",
    ),
    (
        "near",
        "Apa driver printer laboratorium CERTAN dan link unduh resminya?",
        "No local printer model or driver catalogue.",
    ),
    (
        "near",
        "Berapa bandwidth Internet kampus CERTAN yang terpakai sekarang?",
        "No live utilisation telemetry or local bandwidth capacity.",
    ),
    (
        "near",
        "Siapa petugas yang sedang menangani tiket CERTAN INC12345?",
        "No live ticket records or assignment data.",
    ),
    (
        "near",
        "Berapa subnet IP gedung rektorat CERTAN yang dipakai saat ini?",
        "No local network inventory; example addresses are not local deployment facts.",
    ),
    (
        "near",
        "Berapa SLA P1 resmi yang sudah disahkan untuk CERTAN?",
        "UHB DRAFT examples and UCF targets do not establish an approved CERTAN SLA.",
    ),
]
OOD_EVAL = [
    (
        "far",
        "Dokter gigi mana yang buka di dekat stasiun besok pagi?",
        "No healthcare directory or appointments.",
    ),
    ("far", "Berapa skor pertandingan sepak bola tadi malam?", "No sports results."),
    (
        "far",
        "Berapa harga tiket kereta Jakarta Surabaya untuk pekan depan?",
        "No travel booking or train prices.",
    ),
    (
        "far",
        "Apa persyaratan beasiswa mahasiswa CERTAN tahun ini?",
        "No scholarship admissions rules.",
    ),
    (
        "near",
        "Apakah ISP kampus CERTAN sedang outage sekarang dan kapan pulih?",
        "No real-time ISP monitoring or restoration estimates.",
    ),
    (
        "near",
        "Tolong tampilkan password terbaru akun eduroam milik saya.",
        "Policies mention eduroam but contain no personal credentials.",
    ),
    (
        "near",
        "Alamat IP laptop saya sekarang berapa dan siapa pemilik MAC AA:BB:CC:DD:EE:FF?",
        "No device inventory or live endpoint state.",
    ),
    (
        "near",
        "Apakah tiket gangguan CERTAN INC9988 sudah ditutup oleh teknisi?",
        "No actual incident database; procedures only.",
    ),
    (
        "near",
        "Bagaimana memperbaiki CrashLoopBackOff pada pod Kubernetes?",
        "No Kubernetes/container diagnosis documentation.",
    ),
    (
        "near",
        "Berapa biaya upgrade access point dan anggaran jaringan CERTAN tahun depan?",
        "No procurement prices or local budget.",
    ),
    (
        "near",
        "Siapa nama Kepala DTSI CERTAN dan nomor hotline resminya saat ini?",
        "External institutions' contacts and placeholders do not identify CERTAN personnel.",
    ),
    (
        "near",
        "Di channel radio berapa AP lantai tiga CERTAN beroperasi saat ini?",
        "No deployed AP radio/channel inventory or live measurements.",
    ),
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    label_path = ROOT / "evaluation/retrieval_study_labels_v2.json"
    protocol_path = ROOT / "evaluation/retrieval_study_protocol_v2.json"
    if label_path.exists() or protocol_path.exists():
        raise FileExistsError(
            "study already frozen; do not rewrite labels after retrieval"
        )
    manifest = json.loads(
        (ROOT / "data/corpus/corpus_manifest.json").read_text(encoding="utf-8")
    )
    queries = []
    for split, positives, negatives in (
        ("development", DEV, OOD_DEV),
        ("evaluation", EVAL, OOD_EVAL),
    ):
        for i, (category, query, docs, evidence) in enumerate(positives, 1):
            queries.append(
                {
                    "id": f"{split[:3]}_p{i:02d}",
                    "split": split,
                    "category": category,
                    "query": query,
                    "relevant_documents": docs,
                    "evidence": evidence,
                }
            )
        for i, (distance, query, evidence) in enumerate(negatives, 1):
            queries.append(
                {
                    "id": f"{split[:3]}_o{i:02d}",
                    "split": split,
                    "category": "out_of_domain",
                    "ood_distance": distance,
                    "query": query,
                    "relevant_documents": [],
                    "evidence": evidence,
                }
            )
    now = datetime.now(UTC).isoformat()
    labels = {
        "frozen_at_utc": now,
        "version": "v2",
        "unit": "document_id",
        "queries": queries,
        "annotation_method": "Authored from corpus text before retrieval; independent of ranking, not an independent human annotator. Synthetic source-grounded queries, no claim of population representativeness.",
        "relevance_policy": "Direct support for requested information; institution-specific requests must match named institution. Empty labels include adjacent but unsupported local/live facts. DRAFT topical support does not confer operational authority.",
        "source_text_sha256": {
            d["document_id"]: sha(ROOT / d["text_file"]) for d in manifest["documents"]
        },
    }
    label_path.write_text(
        json.dumps(labels, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    frozen_paths = [
        "evaluation/semantic_retrieval_ground_truth.json",
        "evaluation/semantic_retrieval_benchmark.json",
        "evaluation/token_chunking_comparison.json",
        "data/corpus/processed/knowledge_chunks.json",
        "data/corpus/processed/knowledge_chunks_t96_w10.json",
        "data/corpus/processed/knowledge_chunks_t120_w12.json",
    ]
    frozen_paths += [d["text_file"] for d in manifest["documents"]]
    protocol = {
        "frozen_at_utc": now,
        "labels_sha256": sha(label_path),
        "frozen_baseline_sha256": {p: sha(ROOT / p) for p in frozen_paths},
        "raw_depth": 100,
        "k_values": [1, 3, 5],
        "threshold_grid": [round(i / 100, 2) for i in range(0, 91, 5)],
        "threshold_selection": "Development only: minimise (false acceptance rate + false rejection rate)/2; ties minimise false acceptance, then choose lower threshold. Gate on selected document's RAW cosine, never the ranking bonus.",
        "profiles": ["v1_t96_w10", "v2_t96_w10", "v2_t120_w12", "v2_t96_w0"],
        "selected_profile": "v2_t96_w10 fixed in advance; other profiles are ablations, not selected on evaluation results",
        "candidate": {
            "name": "metadata_intent_bonus",
            "bonus": 0.10,
            "rules_file": "evaluation/metadata_intent_candidate.py",
            "rules_sha256": sha(ROOT / "evaluation/metadata_intent_candidate.py"),
            "metadata_rule_file": "src/proyek_certan/corpus/revision.py",
            "metadata_rule_sha256": sha(ROOT / "src/proyek_certan/corpus/revision.py"),
        },
        "adoption_rule": "Adopt only if development AND held-out evaluation paired bootstrap 95% lower bounds for both delta Recall@3 and delta MRR are >0, and OOD false acceptance and positive false rejection do not increase. Otherwise keep semantic default; retain experimental evidence only.",
        "uncertainty": "Paired query bootstrap, 10000 resamples, seed 20261105, positive queries only. Wilson 95% intervals for error rates. Synthetic same-author evaluation is not a blinded human study.",
    }
    protocol_path.write_text(
        json.dumps(protocol, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"Frozen {len(queries)} new labels ({len(DEV)}+{len(OOD_DEV)} development; {len(EVAL)}+{len(OOD_EVAL)} evaluation)"
    )


if __name__ == "__main__":
    main()
