# Laporan cleanup repository dan konsolidasi korpus final

Tanggal: 6 November 2026. Branch: `feature/milestone-3-vector-db`.
Baseline: commit `7d27d33bd76b8be0eb9c60108a98926feec422e3`, working tree awal bersih.

**READY untuk finalisasi laporan T03 sebagai prototipe akademik dengan hasil dan batasan yang dinyatakan. NOT READY untuk mengklaim seluruh deskriptor nilai 100 atau penggunaan produksi.** Cleanup menyatukan jalur penggunaan korpus; tidak memperbaiki ranking atau OOD secara algoritmik.

## 1. Inventaris dan keputusan organisasi

[Inventaris sebelum perubahan](../../evaluation/archive/cleanup-baseline.json) dibuat sebelum konsolidasi. Isinya mencakup SHA-256 seluruh 231 berkas Git, 633 import Python, 183 literal path, 246 tautan Markdown lokal yang saat itu valid, ringkasan cache lokal dan klasifikasi dependensi. Metadata internal Git serta dependency terpasang tidak dihitung sebagai berkas deliverable.

Pemeriksaan menemukan import antarskrip berbasis root evaluation, penggunaan `Path(__file__).parents[1]`, pemanggilan path langsung pada tes, manifest beku dan snapshot kode. Karena itu **tidak ada artefak lama yang dipindahkan secara fisik**. Pemetaan kompatibilitas mempertahankan path historis yang sama; pemisahan final/historical/rejected/generated disediakan oleh [navigasi evaluasi](../../evaluation/README.md). Ini menggunakan pengecualian pemindahan yang memang diizinkan dalam instruksi pengguna.

| Kategori | Sebelum | Sesudah | Peran |
|---|---:|---:|---|
| ACTIVE_RUNTIME | 34 | 36 | Runtime, fixture/config; dua modul orkestrasi final baru |
| ACTIVE_CORPUS | 15 | 32 | 15 PDF asli, 15 TXT aktif, satu chunk JSON dan satu manifest |
| ACTIVE_TESTS | 30 | 31 | Semua tes lama dan satu modul tes final baru |
| ACTIVE_EVALUATION | 0 | 2 | Evaluator resmi dan receipt verifikasi cleanup |
| DOCUMENTATION | 24 | 35 | README, lisensi, panduan dan navigasi |
| HISTORICAL_EVIDENCE | 128 | 129 | Semua bukti lama dan inventaris baseline cleanup |
| GENERATED_LOCAL_ARTIFACT | Di luar total | Di luar total | Venv, cache, database, render, pytest/ruff dan bytecode |
| REDUNDANT_VERIFIED | 0 | 0 | Tidak ada berkas yang terbukti tidak diperlukan |
| UNKNOWN_DEPENDENCY | 0 | 0 | Tidak ada berkas kategori ini yang dihapus |
| **Total deliverable** | **231** | **265** | **+34 baru, dua README lama diubah** |

Angka sesudah mencakup receipt `cleanup-verification.json` yang disimpan oleh evaluator dalam [direktori hasil](../../evaluation/results/). Semua 231 berkas lama tetap ada: 229 identik byte dan hanya README utama serta README evaluation diubah. File generated tidak dihapus; inventaris awal mencatat 32.897 berkas venv, 95 berkas `.local`, 19 berkas cache model, lima berkas pytest cache dan sepuluh berkas ruff cache. Angka cache bersifat lokal dan dapat berubah setelah pengujian; bytecode generated pada subdirektori juga dikecualikan dari total deliverable.

## 2. Struktur sebelum dan sesudah

Sebelum:

```text
README.md                              panduan panjang dengan beberapa jalur M3
src/proyek_certan/                     implementasi M1/M2/M3
data/corpus/
  raw/                                 15 PDF
  processed/                           v1 + reviewed-v2/ + reviewed-v3/
  corpus_manifest.json                 manifest sumber awal
docs/milestone-3/                      laporan tahapan, tanpa README utama
evaluation/                            skrip, hasil, eksperimen di root
  quality-v3/                          protokol, label, observasi, locked-code
tests/                                 30 berkas tes/fixture
```

Sesudah:

```text
README.md                              pintu masuk 15 bagian; satu rute final
src/proyek_certan/knowledge/
  final_corpus.py                      path/manifest/hash dan validasi indeks
  final_cli.py                         verify, index, search; delegasi runtime lama
data/corpus/
  README.md                            navigasi peran korpus
  raw/                                 15 PDF asli tetap
  final/                               SATU korpus aktif, 18 berkas
  processed/README.md                  penanda seluruh versi lama sebagai historis
  processed/                           seluruh isi lama tetap identik
docs/milestone-1/usage.md               detail M1 dari README lama
docs/milestone-2/usage.md               detail M2 dari README lama
docs/milestone-3/
  README.md                            dokumentasi utama M3
  repository-cleanup.md                 laporan ini
  ...                                  seluruh laporan riset lama tetap
evaluation/
  README.md                            navigasi final/historis/ditolak/generated
  benchmarks/                          evaluator resmi + petunjuk
  results/                             receipt baru + indeks hasil beku
  experiments/                         indeks kandidat ditolak
  archive/                             indeks sejarah + inventaris baseline
  quality-v3/                          tetap pada path dan bytes aslinya
  ...                                  skrip/hasil root lama untuk kompatibilitas
tests/knowledge/test_final_corpus.py    tes integritas dan batas CLI final
```

| Lokasi | Sebelum | Sesudah |
|---|---:|---:|
| Root | 6 | 6 |
| data | 73 | 93 |
| docs | 21 | 25 |
| evaluation | 66 | 73 |
| src | 35 | 37 |
| tests | 30 | 31 |

Total dihitung dari berkas tracked ditambah untracked yang tidak diabaikan Git; direktori `.git`, `.venv`, `.local`, `.cache` dan artefak generated dikecualikan. Bertambahnya berkas diperlukan untuk salinan final, provenance dan navigasi; bukan penambahan salinan aktif lain.

## 3. Berkas dipindahkan, dipertahankan dan dihapus

- **Dipindahkan secara fisik: 0.** Seluruh 231 path awal tetap tersedia. Penjelasan teknis M1/M2 dipindahkan secara editorial dari README utama ke [panduan M1](../milestone-1/usage.md) dan [panduan M2](../milestone-2/usage.md), tanpa mengubah implementasi.
- **Dihapus: 0.** Tidak ada penghapusan yang memerlukan pembuktian aman. UNKNOWN_DEPENDENCY tidak dihapus.
- **Dipertahankan:** seluruh 15 PDF; seluruh teks/chunk v1/v2/v3; hasil, label, ground truth, protokol, lock awal/r2 dan enam snapshot; kandidat intent/guard/title yang ditolak; seluruh kode dan tes lama.
- **Diubah:** [README utama](../../README.md) menjadi pintu masuk, dan [README evaluation](../../evaluation/README.md) menjadi indeks. Riwayat angka, kode eksperimen dan bytes artefak beku tidak ditulis ulang.
- **Duplikasi yang disengaja:** 15 TXT dan chunk 96/10 disalin identik ke lokasi final. Asal reviewed-v3 tetap diperlukan oleh manifest/protokol dan tes; ia berstatus bukti historis. Hanya salinan final dipakai CLI resmi. Tidak ada dua versi teks aktif per document_id.

Tidak ada perubahan pada pyproject, lockfile, algoritma UCS, CSP, AC-3, Backtracking, embedding, cosine atau ranking. Semua 35 berkas sumber lama identik dengan baseline cleanup. Tidak ada LLM, RAG agent, frontend atau FastMCP yang ditambahkan.

## 4. Korpus aktif final

[Manifest final](../../data/corpus/final/manifest.json) menyatakan `m3-reviewed-v3`, profil tunggal `v3_t96_w10`, 15 dokumen dan 487 chunk. [knowledge_chunks.json](../../data/corpus/final/knowledge_chunks.json) disalin dari profil v3 terpilih dengan SHA-256 identik:

```text
9abc951cbb6220ff00d4d604a1249a0ac228bf6ae0559a04f356257e679a9a7c
```

Tidak ada re-cleaning, re-chunking, penggantian ID atau perubahan metadata. Verifikasi tokenizer asli memperoleh minimum 19, median 84 dan maksimum 96 token termasuk special tokens; tidak ada chunk melampaui 128 token model. Overlap yang diminta adalah 10 kata. Cakupan sumber mengikuti hasil audited v3 yang bytes-nya dipertahankan.

| ID | TXT aktif |
|---|---|
| DOC01 | [DOC01_WiFi.txt](../../data/corpus/final/DOC01_WiFi.txt) |
| DOC02 | [DOC02_DNS.txt](../../data/corpus/final/DOC02_DNS.txt) |
| DOC03 | [DOC03_DHCP_Server.txt](../../data/corpus/final/DOC03_DHCP_Server.txt) |
| DOC04 | [DOC04_DHCP_Client.txt](../../data/corpus/final/DOC04_DHCP_Client.txt) |
| DOC05 | [DOC05_TCP_IP.txt](../../data/corpus/final/DOC05_TCP_IP.txt) |
| DOC06 | [DOC06_LAN_Switch.txt](../../data/corpus/final/DOC06_LAN_Switch.txt) |
| DOC07 | [DOC07_Packet_Loss.txt](../../data/corpus/final/DOC07_Packet_Loss.txt) |
| DOC08 | [DOC08_Authentication.txt](../../data/corpus/final/DOC08_Authentication.txt) |
| DOC09 | [DOC09_Service_Desk.txt](../../data/corpus/final/DOC09_Service_Desk.txt) |
| DOC10 | [DOC10_Incident_Handling.txt](../../data/corpus/final/DOC10_Incident_Handling.txt) |
| DOC11 | [DOC11_Incident_Management_UCF.txt](../../data/corpus/final/DOC11_Incident_Management_UCF.txt) |
| DOC12 | [DOC12_Security_Incident.txt](../../data/corpus/final/DOC12_Security_Incident.txt) |
| DOC13 | [DOC13_Network_Administration.txt](../../data/corpus/final/DOC13_Network_Administration.txt) |
| DOC14 | [DOC14_Acceptable_Use.txt](../../data/corpus/final/DOC14_Acceptable_Use.txt) |
| DOC15 | [DOC15_Network_Management.txt](../../data/corpus/final/DOC15_Network_Management.txt) |

Selain 15 TXT, direktori final hanya berisi [chunk JSON](../../data/corpus/final/knowledge_chunks.json), [manifest](../../data/corpus/final/manifest.json) dan [README penggunaan](../../data/corpus/final/README.md): total 18 berkas. SHA-256 lengkap per TXT/PDF dan provenance sumber berada dalam manifest.

`documents.active_text_file` menjadi path aktif. `metadata.text_file` pada chunk tetap menunjuk asal reviewed-v3 agar bytes penelitian sama. Provenance menyimpan pula path ekstraksi awal sebagai sejarah. URL DOC-13 yang dipakai chunk tetap URL revisi terverifikasi 2024; URL historis tidak dihapus. Status DRAFT DOC-09/10, hak sumber dan flag review DOC-11 dipertahankan. Konfigurasi 120/12 dan 96/0 tetap ablation historis dan tidak masuk CLI resmi.

## 5. Jalur index/search final

Jalankan dari root repository:

```bash
uv run --locked python -m proyek_certan.knowledge.final_cli verify
uv run --locked python -m proyek_certan.knowledge.final_cli index
uv run --locked python -m proyek_certan.knowledge.final_cli verify --index
uv run --locked python -m proyek_certan.knowledge.final_cli search --query "Bagaimana diagnosis resolusi nama DNS pada klien?" --top-k 5
uv run --locked python -m proyek_certan.knowledge.final_cli search --query "Bagaimana diagnosis resolusi nama DNS pada klien?" --document-level --top-k 5
```

Database resmi adalah `.local/chroma-corpus-final`, cache `.cache/models`, collection `certan_knowledge`, model multilingual MiniLM 384 dimensi ternormalisasi, cosine HNSW dan explicit embeddings. Tidak ada threshold abstention yang diadopsi. `--db` hanya override lokasi terisolasi untuk pengujian/recovery; input dan profil tetap final.

[Orkestrasi final](../../src/proyek_certan/knowledge/final_cli.py) memakai [konfigurasi/validasi terpusat](../../src/proyek_certan/knowledge/final_corpus.py), lalu mendelegasikan encoding, indexing dan retrieval kepada implementasi lama. Model, hitungan cosine, pemilihan chunk terbaik per dokumen dan urutan ranking tidak dimodifikasi. Database berisi data lain ditolak sebelum encoding; search pada indeks yang belum dibuat tidak diam-diam membuat database kosong. Tidak ada perintah menghapus indeks.

## 6. Pemeriksaan yang benar-benar dijalankan

| Pemeriksaan | Hasil aktual |
|---|---|
| Full pytest dengan CERTAN_RUN_MODEL_TESTS=1 | **231 passed, 0 skipped**, 56,21 detik; mencakup unit dan integration ketiga milestone |
| Tes final baru | 11 kasus: salinan/DRAFT, hash teks/PDF, traversal path, ID ganda, TXT tak terdaftar, indeks hilang/campuran, reopen dan content mismatch |
| Indexing final baru dengan model asli | PASS, 487 chunk; 15 dokumen; vektor 384 dimensi ternormalisasi |
| Reopen indeks dari proses baru | PASS; seluruh ID, teks, metadata, bentuk dan norma vektor sesuai |
| CLI chunk search dari proses baru | PASS; lima hasil DNS, Top-1 DOC02 |
| CLI document-level dari proses baru | PASS; lima document_id unik; Top-1 DOC02; ranking_score sama dengan cosine asli |
| CLI M1 | PASS; UCS 1412,5903, FIFO 1531,3458 |
| CLI M2 | PASS; solved, 12 assignment, validation passed |
| Sensitivity benchmark M2 --runs 10 | PASS; Small/Medium/Large solved |
| Benchmark final --live | PASS; tokenizer aktual, indeks persisten dan 15 kueri legacy |
| Replay observasi beku | PASS; development r2, validation dan final test; aritmetika per kueri, ringkasan dan paired bootstrap sama |
| Hash historis | PASS; 70 baseline v3, 21 baseline v2 (bertumpang-tindih), enam snapshot; semua 15 PDF sama |
| Markdown lokal | PASS; seluruh dokumen Markdown deliverable diperiksa, tanpa target lokal rusak |
| uv lock --check | PASS, 133 paket teresolusi tanpa perubahan lockfile |
| git diff --check | PASS |
| Ruff F dan format pada empat berkas Python baru | PASS |
| Diagnostics editor pada empat berkas Python baru | Tidak ada error |
| Kredensial/file sementara | Tidak ada pola kredensial berkeyakinan tinggi atau berkas sementara pada deliverable; pemeriksaan berbasis pola, bukan jaminan audit keamanan menyeluruh |

Tes model berjalan menggunakan cache lokal dengan HF_HUB_OFFLINE=1 dan TRANSFORMERS_OFFLINE=1. Ketersediaan cache cukup untuk uji; tidak dilakukan unduhan atau perubahan dependency. Uji unduhan/install di mesin bersih **NOT VERIFIED**. Waktu tes dipengaruhi eksekusi benchmark/model lain secara bersamaan; bukan klaim performa runtime.

[Evaluator resmi](../../evaluation/benchmarks/final_pipeline.py) dapat dijalankan lagi tanpa output untuk audit baca-saja. Receipt baru disimpan hanya di [results](../../evaluation/results/), tidak menimpa hasil penelitian. Tidak ada pemanggilan ulang skrip authoring/selection atau retrieval validation/final test create-once.

## 7. Before/after retrieval pada ground truth yang sama

Regresi menggunakan 15 kueri legacy yang sama, termasuk 12 kueri dengan dokumen relevan, tanpa pengubahan label. Ranking dokumen unik diambil dari 100 kandidat chunk. Kolom sebelum berasal dari benchmark v1 `t96_w10`; kolom sesudah berasal dari indeks baru salinan v3 96/10. Angka penuh disimpan dalam receipt baru, sedangkan laporan lama tetap identik.

| Metrik pada 12 kueri positif | Sebelum | Sesudah | Delta |
|---|---:|---:|---:|
| Precision@1 | 0,666667 | 0,666667 | 0 |
| Recall@1 | 0,486111 | 0,486111 | 0 |
| Precision@3 | 0,416667 | 0,416667 | 0 |
| Recall@3 | 0,875000 | 0,875000 | 0 |
| Precision@5 | 0,266667 | 0,266667 | 0 |
| Recall@5 | 0,916667 | 0,916667 | 0 |
| MRR | 0,805556 | 0,805556 | 0 |
| Top-1 relevan | 8/12 | 8/12 | 0 |

Hasil ini menunjukkan tidak ada regresi pada metrik tersebut; bukan peningkatan retrieval akibat cleanup. MRR dihitung pada daftar dokumen unik yang muncul dalam 100 kandidat chunk. Tiga OOD legacy tetap sampel kecil; threshold 0,5 hanya diagnosis historis dan tidak diaktifkan CLI final.

Pada final test v3 beku (24 relevan + 24 OOD), semantic baseline tetap R@3 0,916667 dan MRR 0,812153; diagnosis threshold 0,5 memiliki FAR 18/24 dan FRR 0/24. Guard tetap ditolak karena FRR 7/24, meski FAR menjadi 2/24. Delta MRR title +0,02366 memiliki CI [-0,04094; +0,09107] sehingga tetap ditolak. Tidak ada tuning dari label pengujian atau perubahan hasil negatif. Tanpa kebijakan abstention yang diadopsi, CLI dapat mengembalikan hasil untuk kueri OOD.

## 8. Risiko, keterbatasan dan pekerjaan berikutnya

- WiFi diagnosis masih menempatkan DOC-13 di atas DOC-01; query legacy menempatkan DOC-01 pada rank 6. Cleanup tidak mengklaim menyelesaikannya.
- Precision penolakan OOD belum memadai; tidak ada guardrail yang lolos kriteria adopsi. Penggunaan operasional otomatis belum layak.
- DOC-09/10 DRAFT; tabel/diagram DOC-11 dan otoritas SOP lokal masih membutuhkan review manusia. Penyalinan final tidak mengesahkan sumber.
- [Template anotasi independen](../../evaluation/quality-v3/independent_annotation_template.json) masih kosong. Ground truth baru belum mendapat penilaian manusia independen; label/split tidak diubah untuk menutupi batas ini.
- Nomor halaman exact hanya tersedia bila bukti pencocokan mendukungnya; tidak ditambahkan dengan perkiraan. Representativitas korpus dibatasi 15 sumber eksternal.
- Cache/database/render tetap generated lokal. Mesin baru harus memasang dependency dan mengunduh model sebelum index; transfer cache dan uji instalasi daring di lingkungan lain belum diverifikasi.
- Pemindahan fisik hasil lama memerlukan migrasi protokol/import yang terencana. Saat ini indeks navigasi menjaga integritas dan mengurangi risiko; tidak ada penghapusan spekulatif.

Pengguna dapat meninjau [README proyek](../../README.md), [panduan M3](README.md), [manifest final](../../data/corpus/final/manifest.json) dan [bukti evaluasi](../../evaluation/README.md) sebelum finalisasi. **Tidak ada commit, push, merge atau pull request yang dibuat.**

## 9. Daftar berkas baru

Seluruh berkas baru berikut memiliki fungsi eksplisit; daftar ini termasuk receipt hasil akhir. Berkas lama yang diubah hanya dua README yang disebutkan di atas.

- [data/corpus/README.md](../../data/corpus/README.md)
- [data/corpus/final/DOC01_WiFi.txt](../../data/corpus/final/DOC01_WiFi.txt)
- [data/corpus/final/DOC02_DNS.txt](../../data/corpus/final/DOC02_DNS.txt)
- [data/corpus/final/DOC03_DHCP_Server.txt](../../data/corpus/final/DOC03_DHCP_Server.txt)
- [data/corpus/final/DOC04_DHCP_Client.txt](../../data/corpus/final/DOC04_DHCP_Client.txt)
- [data/corpus/final/DOC05_TCP_IP.txt](../../data/corpus/final/DOC05_TCP_IP.txt)
- [data/corpus/final/DOC06_LAN_Switch.txt](../../data/corpus/final/DOC06_LAN_Switch.txt)
- [data/corpus/final/DOC07_Packet_Loss.txt](../../data/corpus/final/DOC07_Packet_Loss.txt)
- [data/corpus/final/DOC08_Authentication.txt](../../data/corpus/final/DOC08_Authentication.txt)
- [data/corpus/final/DOC09_Service_Desk.txt](../../data/corpus/final/DOC09_Service_Desk.txt)
- [data/corpus/final/DOC10_Incident_Handling.txt](../../data/corpus/final/DOC10_Incident_Handling.txt)
- [data/corpus/final/DOC11_Incident_Management_UCF.txt](../../data/corpus/final/DOC11_Incident_Management_UCF.txt)
- [data/corpus/final/DOC12_Security_Incident.txt](../../data/corpus/final/DOC12_Security_Incident.txt)
- [data/corpus/final/DOC13_Network_Administration.txt](../../data/corpus/final/DOC13_Network_Administration.txt)
- [data/corpus/final/DOC14_Acceptable_Use.txt](../../data/corpus/final/DOC14_Acceptable_Use.txt)
- [data/corpus/final/DOC15_Network_Management.txt](../../data/corpus/final/DOC15_Network_Management.txt)
- [data/corpus/final/README.md](../../data/corpus/final/README.md)
- [data/corpus/final/knowledge_chunks.json](../../data/corpus/final/knowledge_chunks.json)
- [data/corpus/final/manifest.json](../../data/corpus/final/manifest.json)
- [data/corpus/processed/README.md](../../data/corpus/processed/README.md)
- [docs/milestone-1/usage.md](../../docs/milestone-1/usage.md)
- [docs/milestone-2/usage.md](../../docs/milestone-2/usage.md)
- [docs/milestone-3/README.md](../../docs/milestone-3/README.md)
- [docs/milestone-3/repository-cleanup.md](../../docs/milestone-3/repository-cleanup.md)
- [evaluation/archive/README.md](../../evaluation/archive/README.md)
- [evaluation/archive/cleanup-baseline.json](../../evaluation/archive/cleanup-baseline.json)
- [evaluation/benchmarks/README.md](../../evaluation/benchmarks/README.md)
- [evaluation/benchmarks/final_pipeline.py](../../evaluation/benchmarks/final_pipeline.py)
- [evaluation/experiments/README.md](../../evaluation/experiments/README.md)
- [evaluation/results/README.md](../../evaluation/results/README.md)
- [src/proyek_certan/knowledge/final_cli.py](../../src/proyek_certan/knowledge/final_cli.py)
- [src/proyek_certan/knowledge/final_corpus.py](../../src/proyek_certan/knowledge/final_corpus.py)
- [tests/knowledge/test_final_corpus.py](../../tests/knowledge/test_final_corpus.py)
- Receipt `cleanup-verification.json` pada [results](../../evaluation/results/), dihasilkan setelah laporan ini selesai.
