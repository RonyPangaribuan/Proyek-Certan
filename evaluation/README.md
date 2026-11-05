# Hasil validasi dan persiapan korpus Milestone 3

## Studi terarah v2 (5 November 2026)

[Laporan before/after](../docs/milestone-3/directed-improvement-v2.md) menggabungkan
audit lima sumber, alasan konfigurasi, 75 kueri pada lima arm, evaluasi OOD,
ketidakpastian, dan alasan menolak kandidat intent. Default semantic dan indeks
final v1 tetap dipertahankan karena peningkatan belum meyakinkan.

- [Korpus v2](./reviewed_corpus_v2.json) dan [audit sumber](./source_review_v2.json)
  mencatat koreksi aman, DRAFT, hash, serta URL DOC-13 yang berbeda versi.
- [Label tambahan](./retrieval_study_labels_v2.json) dan
  [protokol beku](./retrieval_study_protocol_v2.json) memisahkan 30 kueri
  development dari 30 kueri evaluation; 15 kueri lama tetap baseline.
- [Hasil lengkap](./retrieval_study_results_v2.json) memuat ranking, Recall/Precision
  @1/3/5, MRR, FAR/FRR, kurva threshold development, dan paired bootstrap.
- [Verifikasi proses terpisah](./retrieval_study_verification_v2.json) memeriksa
  baseline, chunk deterministik, isi indeks, model, dan aritmetika evaluasi.

Reproduksi berurutan dari root: `build_reviewed_corpus.py`,
`audit_sources_v2.py --refresh`, `retrieval_study.py`, lalu
`audit_retrieval_study.py`, masing-masing dengan
`uv run --frozen --no-sync python evaluation/<skrip>`.
Jangan menulis ulang label/protokol setelah melihat hasil. Untuk mengulang
benchmark lama tanpa menimpa JSON historis, gunakan audit v2; ia memanggil
fungsi benchmark dalam memori. Perintah lama di bagian historis berikut
mendokumentasikan pembuatan artefak awal, bukan instruksi menimpa baseline beku.

## Arsip laporan awal

Validasi ulang pada branch `feature/milestone-3-vector-db` menggunakan environment
`uv` yang ada. Detail per halaman, SHA-256, dan waktu eksekusi tersedia di
[pdf_validation.json](./pdf_validation.json) dan [pdf_validation.csv](./pdf_validation.csv).
Laporan teks olahan ada di [corpus_processing.json](./corpus_processing.json),
dengan sumber pada [corpus_manifest.json](../data/corpus/corpus_manifest.json).

## Hasil validasi PDF

Seluruh 15 PDF dapat dibuka. Totalnya **68 halaman**, dengan **40.890 karakter**
yang dapat diekstraksi langsung oleh `pypdf` dan **47 halaman kosong secara
tekstual**. DOC-11 dan DOC-13 adalah dua PDF yang menghasilkan teks. Tiga belas
PDF lain tetap `no_text`; itu termasuk DOC-06 yang baru. Status `blocked` pada
validator berarti PDF itu sendiri tidak menyediakan teks untuk ekstraksi langsung,
bukan bahwa dokumen olahan HTML tidak tersedia.

| Dokumen | Halaman | Karakter `pypdf` | Halaman kosong | Status PDF |
|---|---:|---:|---:|---|
| DOC01_WiFi.pdf | 2 | 0 | 2 | `no_text` |
| DOC02_DNS.pdf | 6 | 0 | 6 | `no_text` |
| DOC03_DHCP_Server.pdf | 5 | 0 | 5 | `no_text` |
| DOC04_DHCP_Client.pdf | 1 | 0 | 1 | `no_text` |
| DOC05_TCP_IP.pdf | 6 | 0 | 6 | `no_text` |
| DOC06_LAN_Switch.pdf | 3 | 0 | 3 | `no_text` |
| DOC07_Packet_Loss.pdf | 3 | 0 | 3 | `no_text` |
| DOC08_Authentication.pdf | 6 | 0 | 6 | `no_text` |
| DOC09_Service_Desk.pdf | 4 | 0 | 4 | `no_text` |
| DOC10_Incident_Handling.pdf | 4 | 0 | 4 | `no_text` |
| DOC11_Incident_Management_UCF.pdf | 16 | 31.655 | 0 | `success` |
| DOC12_Security_Incident.pdf | 3 | 0 | 3 | `no_text` |
| DOC13_Network_Administration.pdf | 5 | 9.235 | 0 | `success` |
| DOC14_Acceptable_Use.pdf | 3 | 0 | 3 | `no_text` |
| DOC15_Network_Management.pdf | 1 | 0 | 1 | `no_text` |
| **Total** | **68** | **40.890** | **47** | **2 `success`, 13 `no_text`** |

DOC-06 sekarang berupa cetakan halaman *VLANs — Open vSwitch 4.0.0
documentation*: halaman pertama menampilkan logo Open vSwitch, judul VLANs,
dan tanya-jawab VLAN. Metadata PDF juga menyebut judul tersebut. SHA-256 PDF
barunya `970ae7af0b0dce2d78d7c73887b4a873d2064942d82bd70ca642317f67455222`.
`pypdf` menghasilkan 0 karakter pada ketiga halamannya. Tidak ada OCR.

## Hasil persiapan teks

Semua **15 file UTF-8** tersedia di [processed/](../data/corpus/processed/),
total **132.073 karakter**. Tiga belas dokumen memakai badan HTML resmi yang
dibersihkan, sedangkan DOC-11 dan DOC-13 memakai `pypdf`. Hasil DOC-06 dari
[FAQ VLAN resmi Open vSwitch](https://docs.openvswitch.org/en/stable/faq/vlan/)
memiliki 9.771 karakter, 10 pasangan tanya-jawab, dan instruksi `ovs-vsctl`.
Berkas teks DOC-06 memiliki SHA-256
`152557ef0e2c84a38aa790a1854f376d070d2d028dff55f644a45f859e7afd45`.
Sumber FAQ ditandai [Apache-2.0](https://github.com/openvswitch/ovs/blob/main/Documentation/faq/vlan.rst).

| ID | Karakter teks | Metode | Status |
|---|---:|---|---|
| DOC01 | 4.367 | HTML resmi | `processed` |
| DOC02 | 13.940 | HTML resmi | `processed` |
| DOC03 | 9.372 | HTML resmi | `processed` |
| DOC04 | 1.814 | HTML resmi | `processed` |
| DOC05 | 15.004 | HTML resmi | `processed` |
| DOC06 | 9.771 | HTML resmi Open vSwitch | `processed` |
| DOC07 | 8.103 | HTML resmi | `processed` |
| DOC08 | 5.766 | HTML resmi | `processed` |
| DOC09 | 7.611 | HTML resmi (DRAFT) | `processed` |
| DOC10 | 4.600 | HTML resmi (DRAFT) | `processed` |
| DOC11 | 30.280 | `pypdf` | `processed` |
| DOC12 | 4.178 | HTML resmi | `processed` |
| DOC13 | 8.996 | `pypdf` | `processed` |
| DOC14 | 5.712 | HTML resmi | `processed` |
| DOC15 | 2.559 | HTML resmi | `processed` |
| **Total** | **132.073** | | **15 `processed`** |

Empat belas hasil lama digunakan ulang setelah SHA-256 PDF sumber, URL sumber,
SHA-256 file teks, dan panjang UTF-8 cocok dengan laporan sebelumnya. DOC-06
diambil ulang dari HTML resmi setelah pemeriksaan `robots.txt`. Seluruh hash
15 PDF kini cocok dengan laporan validasi baru; baseline PDF Cisco lama tidak
digunakan sebagai acuan DOC-06. PDF sumber dan 14 teks lama tidak diubah.

Keberhasilan pembuatan file teks tidak memastikan semua informasi grafis pada
PDF sudah terwakili, ataupun bahwa urutan baca tabel kompleks sempurna.
DOC-09 dan DOC-10 masih bersumber dari halaman berlabel DRAFT. Tinjau isi
sebelum chunking atau indexing. Panduan metode dan pengujian terdapat pada
[dokumentasi validasi](../docs/milestone-3/corpus-validation.md) dan
[persiapan](../docs/milestone-3/corpus-preparation.md).

Pengujian ulang: `uv run --frozen --no-sync python -m pytest -q` menghasilkan
`157 passed, 2 skipped`; `uv lock --check` dan `git diff --check` lulus.
Validator PDF mengembalikan exit code `1` sesuai definisi karena masih ada
13 PDF `blocked/no_text`, sedangkan persiapan korpus mengembalikan exit code
`0` untuk 15 dokumen teks yang berhasil.

## Audit dan chunking

Ingestion dari manifest menghasilkan
[knowledge_chunks.json](../data/corpus/processed/knowledge_chunks.json)
dan [laporan audit](./corpus_chunking.json). Dengan parameter awal 250 kata,
overlap 40 kata, 15 TXT menghasilkan **130 chunk**. Median panjangnya
169 kata, maksimum 250 kata; 5 dokumen memerlukan review isi sebelum
indexing produksi. Temuan dan batas metode dijelaskan pada
[panduan ingestion](../docs/milestone-3/corpus-ingestion.md).
Pengujian penuh setelah tahap ini: `164 passed, 2 skipped`. Seluruh chunk
lulus kontrak metadata dan rekonstruksi urutan kata 15 dokumen.

## Indeks dan pencarian semantik eksperimen

Seluruh 130 chunk telah diindeks pada database Chroma persisten baru di
`.local/chroma-corpus-m3` dengan model multilingual berdimensi 384.
Pemeriksaan dari proses baru memastikan jumlah, ID, teks, metadata, dan
cakupan 15 dokumen. Lima kueri Indonesia serta hasil top-k tersedia di
[real_corpus_search.json](./real_corpus_search.json) dan dijelaskan pada
[panduan integrasi](../docs/milestone-3/real-corpus-search.md).

**Belum siap untuk indexing produksi:** 115 chunk melampaui batas input
128 token model, sehingga bagian akhir chunk dapat terpotong saat embedding.
DOC-06, DOC-09, DOC-10, DOC-11, dan DOC-13 juga masih membutuhkan review isi;
status DRAFT DOC-09/10 dipertahankan pada metadata indeks.
Suite penuh dengan model nyata setelah integrasi ini: **168 passed**.

## Eksperimen batas token

Tokenizer model memakai dua special token dalam batas 128 token. Dua profil
eksperimen menghasilkan 374 chunk (maksimum 120 token) dan 484 chunk (maksimum
96 token), masing-masing tanpa pelanggaran batas dan dengan cakupan seluruh
15 dokumen. Database eksperimen terpisah dari baseline 130 chunk; hasil
lengkap tersedia di [perbandingan token](./token_chunking_comparison.json),
[smoke test 120 token](./real_corpus_search_t120_w12.json), dan
[smoke test 96 token](./real_corpus_search_t96_w10.json). Interpretasi serta
catatan review ada pada [panduan eksperimen](../docs/milestone-3/token-aware-chunking.md).

## Benchmark retrieval berlabel

[Ground truth](./semantic_retrieval_ground_truth.json) memuat 15 kueri Indonesia,
label dokumen relevan, dan dasar penilaian dari teks sumber. [Hasil ranking dan
metrik](./semantic_retrieval_benchmark.json) berisi 100 chunk teratas per kueri
untuk kedua profil, ranking dokumen, Recall@1/3/5, Precision@1/3/5, MRR, dan
analisis threshold. [Skrip benchmark](./benchmark_semantic_retrieval.py) dapat
dijalankan ulang dengan model embedding asli dan kedua indeks persisten.
Interpretasi, keterbatasan DRAFT, serta rekomendasi profil ada dalam
[laporan benchmark](../docs/milestone-3/semantic-retrieval-benchmark.md).
Verifikasi akhir atas hash sumber, chunk deterministik, batas token, dan isi
indeks dapat dijalankan dengan [skrip audit](./audit_milestone3.py); hasil
serta catatan review ada di [laporan finalisasi](../docs/milestone-3/final-audit.md).
