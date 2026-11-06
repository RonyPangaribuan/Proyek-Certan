"""Freeze historical evidence and source-labelled development/validation sets.

No model imports or ranking output reads. The final test is authored separately
only after candidate code, configuration and adoption rules have been locked.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/quality-v3"

# query, category, relevant documents, evidence. Labels refer to direct support.
DEV = [
    (
        "Apa langkah untuk mengisolasi kegagalan asosiasi WLAN berdasarkan klien yang terdampak?",
        "wifi",
        ["DOC01"],
        "Step 1: affected clients and shared SSID/AP.",
    ),
    (
        "Bagaimana teknisi menguji layanan WLAN AutoConfig saat koneksi wireless gagal?",
        "wifi",
        ["DOC01"],
        "Step 2: restart WlanSvc.",
    ),
    (
        "Bagaimana diagnosis catatan DNS yang terhapus akibat scavenging?",
        "dns_dhcp",
        ["DOC02"],
        "Common issues: DNS records missing.",
    ),
    (
        "Apa prosedur mengumpulkan log DHCP di komputer client Windows?",
        "dns_dhcp",
        ["DOC03", "DOC04"],
        "Both DHCP documents discuss client logs and collection.",
    ),
    (
        "Apa yang perlu diperiksa pada scope server DHCP sebelum investigasi network trace?",
        "dns_dhcp",
        ["DOC03"],
        "Server checklist: scope and available leases.",
    ),
    (
        "Mengapa native VLAN untagged dari switch fisik menyebabkan trafik balik OVS hilang?",
        "vlan_switching",
        ["DOC06"],
        "Native VLAN return-traffic FAQ.",
    ),
    (
        "Bagaimana OpenFlow menangani isolasi VLAN jika tidak memakai normal action?",
        "vlan_switching",
        ["DOC06"],
        "FAQ controller bypasses normal VLAN switching.",
    ),
    (
        "Bagaimana memulai investigasi paket terbuang memakai Packet Monitor?",
        "diagnosis_other",
        ["DOC07"],
        "Capture and diagnose packet loss.",
    ),
    (
        "Apa urutan ping loopback, IP lokal dan gateway dalam troubleshooting TCP/IP?",
        "diagnosis_other",
        ["DOC05"],
        "TCP/IP checklist.",
    ),
    (
        "Bagaimana audit log NPS membantu memeriksa kegagalan EAP 802.1X?",
        "diagnosis_other",
        ["DOC08"],
        "NPS audit policy and EAP certificates.",
    ),
    (
        "Menurut Western Michigan University apa larangan penggunaan alamat IP yang bukan milik pengguna?",
        "network_policy",
        ["DOC14"],
        "Full Policy 4.3.4.",
    ),
    (
        "Menurut Oregon State University apa persyaratan pemasangan infrastruktur Wi-Fi?",
        "network_policy",
        ["DOC13"],
        "Clause 5.3.1.",
    ),
    (
        "Menurut Indiana University bagaimana meminta pengecualian untuk keperluan penelitian?",
        "network_policy",
        ["DOC15"],
        "Exceptions, CITRIS and ServiceNow.",
    ),
    (
        "Dalam draf UHB bagaimana service desk mencatat laporan awal gangguan?",
        "incident_management",
        ["DOC09"],
        "OPS-01 8.1; DRAFT topical support.",
    ),
    (
        "Dalam draf prosedur insiden layanan apa isi laporan pascainsiden?",
        "incident_management",
        ["DOC10"],
        "INC-02 7.6; DRAFT.",
    ),
    (
        "Menurut University of Central Florida apa beda Incident dan Service Request?",
        "incident_management",
        ["DOC11"],
        "Definitions.",
    ),
    (
        "Dalam prosedur University of Utah siapa bertanggung jawab atas respons insiden keamanan?",
        "incident_management",
        ["DOC12"],
        "ISO/CISO and IRT.",
    ),
    (
        "WiFi saya putus sekarang; bagaimana langkah umum membedakan masalah AP dengan masalah klien?",
        "wifi",
        ["DOC01"],
        "Generic procedure is supported despite local/live context.",
    ),
]
DEV_OOD = [
    (
        "Berapa alamat IP aktif komputer saya saat ini?",
        "live_data",
        "No live endpoint state.",
    ),
    (
        "Tampilkan daftar pemilik perangkat yang sedang terkoneksi di jaringan saya.",
        "live_data",
        "No operational inventory.",
    ),
    (
        "Apakah tiket INC445501 sudah selesai ditangani sekarang?",
        "live_data",
        "No ticket database.",
    ),
    (
        "Siapa teknisi piket malam ini untuk kampus kami?",
        "live_data",
        "No personnel roster.",
    ),
    (
        "Berapa password WiFi saya yang berlaku sekarang?",
        "live_data",
        "No credentials.",
    ),
    (
        "Kapan layanan ISP kampus saya yang sedang mati akan pulih?",
        "live_data",
        "No monitoring or restoration estimate.",
    ),
    (
        "Apa kebijakan pemasangan router pribadi di Universitas Merdeka?",
        "institution",
        "Institution not represented.",
    ),
    (
        "Berapa SLA resmi yang telah disahkan kampus CERTAN?",
        "institution",
        "No approved CERTAN SOP.",
    ),
    (
        "Menurut Institut Sagara siapa menyetujui pengecualian kebijakan LAN?",
        "institution",
        "Institution not represented.",
    ),
    (
        "Apa sanksi penyalahgunaan Internet menurut Universitas Bintang?",
        "institution",
        "Institution not represented.",
    ),
    (
        "Apa aturan retensi log yang berlaku di Universitas Lazuardi?",
        "institution",
        "Institution not represented.",
    ),
    (
        "Apa persyaratan VPN untuk pegawai Universitas Angkasa?",
        "institution",
        "Institution not represented.",
    ),
    (
        "Bagaimana menghitung pajak penghasilan usaha kecil?",
        "outside_domain",
        "No taxation source.",
    ),
    ("Bagaimana cara membuat roti tanpa oven?", "outside_domain", "No cooking source."),
    (
        "Apa rekomendasi obat untuk sakit kepala?",
        "outside_domain",
        "No medical source.",
    ),
    (
        "Apa persyaratan pindah program studi mahasiswa?",
        "outside_domain",
        "No academic administration source.",
    ),
    (
        "Apa prosedur pendaftaran visa wisata Jepang?",
        "outside_domain",
        "No immigration source.",
    ),
    (
        "Bagaimana membetulkan error migrasi tabel pada PostgreSQL?",
        "outside_domain",
        "No database troubleshooting source.",
    ),
]
VAL = [
    (
        "Bagaimana mengelompokkan klien dengan NIC dan driver sama saat Wi-Fi tidak mau terhubung?",
        "wifi",
        ["DOC01"],
        "Step 1 common NIC/OS/drivers.",
    ),
    (
        "Apa pengujian umum untuk connection manager pihak ketiga dan group policy pada wireless Windows?",
        "wifi",
        ["DOC01"],
        "Step 2 causes and tests.",
    ),
    (
        "Bagaimana menelusuri kegagalan dynamic update DNS sesudah IP berubah?",
        "dns_dhcp",
        ["DOC02"],
        "DNS common issues.",
    ),
    (
        "Bagaimana mengambil capture DHCP serentak di server dan endpoint?",
        "dns_dhcp",
        ["DOC03", "DOC04"],
        "Simultaneous traces in both sources.",
    ),
    (
        "Bagaimana memeriksa ketersediaan lease dan status layanan server DHCP?",
        "dns_dhcp",
        ["DOC03"],
        "DHCP server checklist.",
    ),
    (
        "Kenapa port access OVS hanya meneruskan paket ke VLAN yang sama?",
        "vlan_switching",
        ["DOC06"],
        "VLAN FAQ access/trunk isolation.",
    ),
    (
        "Apa perbedaan native-tagged dan native-untagged untuk port fisik Open vSwitch?",
        "vlan_switching",
        ["DOC06"],
        "Native VLAN example.",
    ),
    (
        "Bagaimana counter discard NIC membantu menyelidiki local packet loss?",
        "diagnosis_other",
        ["DOC07"],
        "Get-NetAdapterStatistics discussion.",
    ),
    (
        "Bagaimana menyelidiki host TCP/IP yang berhenti merespons melalui ping dan trace?",
        "diagnosis_other",
        ["DOC05"],
        "Checklist and host-stopped scenario.",
    ),
    (
        "Bagaimana menafsirkan penolakan akses NPS dengan event 6273 dan rantai sertifikat?",
        "diagnosis_other",
        ["DOC08"],
        "Troubleshooting events and certificates.",
    ),
    (
        "Menurut Western Michigan University apakah sambungan boleh dibagikan ke pihak luar?",
        "network_policy",
        ["DOC14"],
        "Prohibition of retransmission.",
    ),
    (
        "Menurut Oregon State University siapa yang dapat menonaktifkan perangkat yang berisiko?",
        "network_policy",
        ["DOC13"],
        "5.4.2/5.4.3.",
    ),
    (
        "Apa kewajiban inventaris MAC dan DNS statis di Indiana University Bloomington?",
        "network_policy",
        ["DOC15"],
        "Network Management requirements.",
    ),
    (
        "Dalam draf service desk UHB bagaimana triage merutekan insiden keamanan?",
        "incident_management",
        ["DOC09"],
        "OPS-01 8.2, INC-01 parallel.",
    ),
    (
        "Dalam draf INC-02 siapa memberikan persetujuan closure untuk gangguan P1?",
        "incident_management",
        ["DOC10"],
        "7.5 approval.",
    ),
    (
        "Menurut UCF apakah eskalasi insiden otomatis mengganti prioritas?",
        "incident_management",
        ["DOC11"],
        "V.B.a explicitly no.",
    ),
    (
        "Menurut University of Utah bagaimana koordinasi komunikasi dugaan insiden keamanan?",
        "incident_management",
        ["DOC12"],
        "ISO coordinates response and communication.",
    ),
    (
        "Di kampus saya internet wireless gagal hari ini; bagaimana prosedur umum mengisolasi SSID yang terdampak?",
        "wifi",
        ["DOC01"],
        "Procedural request, not asking for a live measurement.",
    ),
]
VAL_OOD = [
    (
        "Apa alamat MAC perangkat saya yang tersambung saat ini?",
        "live_data",
        "No endpoint state.",
    ),
    (
        "Berapa trafik Internet yang sedang dipakai gedung kami sekarang?",
        "live_data",
        "No telemetry.",
    ),
    (
        "Tolong tampilkan status terbaru tiket INC887722.",
        "live_data",
        "No ticket records.",
    ),
    (
        "Siapa yang sedang mengelola access point di lantai dua kampus saya?",
        "live_data",
        "No local personnel inventory.",
    ),
    (
        "Tampilkan kata sandi terbaru akun jaringan milik saya.",
        "live_data",
        "No credentials.",
    ),
    (
        "Kapan gangguan jaringan kampus saya selesai diperbaiki?",
        "live_data",
        "No restoration ETA.",
    ),
    (
        "Menurut Universitas Nusantara siapa berwenang memasang switch?",
        "institution",
        "No named institution source.",
    ),
    (
        "Apa ketentuan resmi penggunaan Wi-Fi di Institut Purnama?",
        "institution",
        "No named institution source.",
    ),
    (
        "Berapa target pemulihan P1 yang berlaku resmi untuk CERTAN?",
        "institution",
        "No approved local SLA.",
    ),
    (
        "Apa aturan perangkat pribadi menurut Universitas Permata?",
        "institution",
        "No named institution source.",
    ),
    (
        "Siapa pemberi persetujuan pengecualian firewall di Universitas Samudra?",
        "institution",
        "No named institution source.",
    ),
    (
        "Apa SOP resminya Universitas Mentari untuk tiket keamanan?",
        "institution",
        "No named institution source.",
    ),
    (
        "Bagaimana mengurus penggantian kartu mahasiswa?",
        "outside_domain",
        "No student administration source.",
    ),
    ("Bagaimana menanam cabai di pot?", "outside_domain", "No agriculture source."),
    (
        "Bagaimana tata cara klaim asuransi kendaraan?",
        "outside_domain",
        "No insurance source.",
    ),
    (
        "Apa persyaratan membuka rekening bank mahasiswa?",
        "outside_domain",
        "No banking source.",
    ),
    (
        "Bagaimana menyusun jadwal latihan renang?",
        "outside_domain",
        "No sports training source.",
    ),
    (
        "Bagaimana mengoptimalkan query SQL dengan indeks B-tree?",
        "outside_domain",
        "No SQL performance source.",
    ),
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_once(path: Path, value) -> None:
    if path.exists():
        raise FileExistsError(f"Frozen artifact exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main():
    if OUT.exists():
        raise FileExistsError("Quality-v3 already prepared; never rewrite seen labels")
    known = {
        q["query"]
        for q in json.loads(
            (ROOT / "evaluation/retrieval_study_labels_v2.json").read_text(
                encoding="utf-8"
            )
        )["queries"]
    }
    known |= {
        q["query"]
        for q in json.loads(
            (ROOT / "evaluation/semantic_retrieval_ground_truth.json").read_text(
                encoding="utf-8"
            )
        )["queries"]
    }
    for split, pos, neg in (
        ("development", DEV, DEV_OOD),
        ("validation", VAL, VAL_OOD),
    ):
        queries = []
        for i, (q, c, docs, evidence) in enumerate(pos, 1):
            queries.append(
                dict(
                    id=f"{split}_p{i:02}",
                    query=q,
                    category=c,
                    relevant_documents=docs,
                    evidence=evidence,
                )
            )
        for i, (q, c, evidence) in enumerate(neg, 1):
            queries.append(
                dict(
                    id=f"{split}_o{i:02}",
                    query=q,
                    category=c,
                    relevant_documents=[],
                    evidence=evidence,
                )
            )
        for q in queries:
            if q["query"] in known:
                raise ValueError("Duplicate query across historical/new sets")
            known.add(q["query"])
        write_once(
            OUT / f"{split}.json",
            dict(
                split=split,
                annotation="Synthetic source-based labels, not independent human validation.",
                queries=queries,
            ),
        )
    frozen = (
        set((ROOT / "data/corpus").rglob("*.json"))
        | set((ROOT / "data/corpus").rglob("*.txt"))
        | set((ROOT / "data/corpus/raw").glob("*.pdf"))
    )
    frozen |= set((ROOT / "evaluation").glob("*.json"))
    frozen |= {
        ROOT / "evaluation/retrieval_study.py",
        ROOT / "evaluation/audit_retrieval_study.py",
    }
    protocol = dict(
        version="quality-v3",
        frozen_at_utc=datetime.now(UTC).isoformat(),
        base_commit=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        baseline_sha256={
            p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(frozen)
        },
        development_sha256=sha(OUT / "development.json"),
        validation_sha256=sha(OUT / "validation.json"),
        corpus_report="evaluation/reviewed_corpus_v2.json",
        profile="v2_t96_w10",
        raw_depth=100,
        baseline_threshold=0.5,
        threshold_grid=[0.4, 0.45, 0.5, 0.55, 0.6],
        support_grid=[0.0, 0.15, 0.2, 0.25, 0.3],
        selection="Development only: minimise balanced FAR/FRR, with FRR <= baseline FRR + 1/18; ties lower FAR, then lower thresholds. Validation may veto adoption but cannot tune thresholds.",
        ranking_candidate="Convex mixture of best chunk cosine and source-title cosine. Alphas 0.2,0.4,0.6 chosen on development only; semantic document max is baseline. No intent bonus, document IDs or query exceptions.",
        guard_adoption="On validation AND untouched final test: paired bootstrap 95% upper bound of FAR delta <0; FRR increase <=0.0556; gated P@1, Recall@3 and MRR drop <=0.0556. Otherwise archive guard, keep baseline runtime.",
        ranking_adoption="On validation AND untouched final test: paired bootstrap 95% lower bound of MRR delta >0; P@1 and Recall@3 do not decrease. Otherwise keep semantic document ranking; archive title mixture.",
        final_test="Not authored until candidate implementation/configuration is frozen. One evaluation only; no tuning or retries selected for score.",
        uncertainty="Paired query bootstrap 10000 draws seed 20261106; Wilson 95% rates. Synthetic same-author queries, no independent human claims.",
    )
    write_once(OUT / "protocol.json", protocol)
    print(
        "Frozen",
        len(frozen),
        "baseline artifacts; 36 development and 36 validation queries. Final test not yet authored.",
    )


if __name__ == "__main__":
    main()
