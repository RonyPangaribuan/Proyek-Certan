# T03 — final quality improvement v3

Tanggal: 5 November 2026. Branch pekerjaan: `feature/milestone-3-vector-db`.
Baseline awal: commit `bba914c`; working tree awal bersih.

**Keputusan finalisasi terhadap target rubrik 100: NOT READY.** Kualitas
preprocessing, keterlacakan dan evaluasi bertambah, tetapi kandidat guardrail
menolak terlalu banyak kueri relevan dan peningkatan ranking belum meyakinkan
pada final test. Keduanya tidak diaktifkan pada runtime akhir. Tidak ada klaim
production-ready, pengesahan SOP lokal, atau pencapaian nilai 100.

## A. Ringkasan perubahan kode

Runtime mempertahankan pencarian chunk semantik sebelumnya dan menambahkan
opsi eksplisit `--document-level`. Opsi ini memilih satu chunk terbaik per
dokumen berdasarkan cosine mentah, mempertahankan urutan stabil saat seri,
dan mengembalikan `document_id`, `chunk_id`, `source`, `section`, `similarity`,
`ranking_score`, metadata, alasan ranking dan jumlah kandidat chunk dokumen.
Ini menghindari duplikasi dokumen pada daftar hasil, **bukan klaim peningkatan
akurasi**: benchmark v2 sudah memakai deduplikasi pada tahap evaluasinya.

[Modul dokumen](../../src/proyek_certan/knowledge/documents.py) terpisah dari
[retriever](../../src/proyek_certan/knowledge/retrieval.py) dan
[CLI](../../src/proyek_certan/knowledge/cli.py). Inventory sumber serta cache
embedding judul dibatalkan setelah indexing agar metadata tidak tertinggal
ketika retriever itu sendiri memperbarui indeks. Encoder, cosine Chroma,
upsert dan path default tidak diganti.

[Guardrail modular](../../evaluation/scope_candidate_v3.py) menguji kebutuhan
data operasional, ketersediaan institusi pada inventory publisher, cosine dan
opsi kesesuaian judul sumber. Output eksperimen membedakan:

- `ACCEPT`: kandidat dapat ditampilkan; relevansi dan otoritas tetap perlu dicek.
- `ABSTAIN`: dependency informasi tidak tersedia, atau tidak ada kandidat.
- `LOW_CONFIDENCE`: bukti cosine/cakupan berada di bawah konfigurasi eksperimen.

Setiap keputusan mempunyai `reason_codes`, alasan Indonesia, sinyal yang
dipakai, serta peringatan DRAFT/review bila hasil diterima. Kata lokal/waktu
sendiri tidak langsung menyebabkan penolakan. Pemeriksaan struktur ini tetap
gagal pada negasi, beberapa bentuk nama institusi dan nama huruf kecil;
keterbatasan tersebut terbukti pada final test, sehingga guardrail diarsipkan.

Runtime akhir **tidak menyediakan `search_scoped` atau `--scope-guard`**.
[CLI kandidat riset](../../evaluation/guard_candidate_cli_v3.py) berada di luar
paket runtime dan selalu mencetak `experiment_only=true`, `adopted=false`.
Implementasi tetap dapat diperiksa dan diuji tanpa dianggap kebijakan operasional.

Kandidat ranking berbeda dari bonus intent v2: [campuran judul](../../evaluation/title_candidate_v3.py)
menggabungkan cosine chunk terbaik dan cosine judul sumber. Tidak ada ID
dokumen favorit, ID kueri, label jawaban, daftar kalimat benchmark, atau bonus
khusus WiFi. Cosine asli tidak diubah; `ranking_score` terpisah. Kandidat ini
juga tetap di luar runtime.

## B. Berkas dan artefak

[Daftar perubahan lengkap](./change-inventory-v3.md) mencantumkan semua berkas
baru/diubah. Kelompok utama:

| Kelompok | Berkas utama |
|---|---|
| Runtime dokumen | [documents.py](../../src/proyek_certan/knowledge/documents.py), [retrieval.py](../../src/proyek_certan/knowledge/retrieval.py), [cli.py](../../src/proyek_certan/knowledge/cli.py) |
| Preprocessing v3 | [review_v3.py](../../src/proyek_certan/corpus/review_v3.py), [builder](../../evaluation/build_reviewed_v3.py), [laporan korpus](../../evaluation/reviewed_corpus_v3.json), [TXT/chunk v3](../../data/corpus/processed/reviewed-v3/) |
| Eksperimen | [runner](../../evaluation/quality_v3.py), [guardrail arsip](../../evaluation/scope_candidate_v3.py), [kandidat judul](../../evaluation/title_candidate_v3.py), [CLI riset](../../evaluation/guard_candidate_cli_v3.py) |
| Evaluasi dan audit | [protokol](../../evaluation/quality-v3/protocol.json), [lock akhir](../../evaluation/quality-v3/lock-r2.json), [hasil validation](../../evaluation/quality-v3/results_validation.json), [hasil final test](../../evaluation/quality-v3/results_final_test.json), [verifikasi sumber/indeks](../../evaluation/quality-v3/verification.json) |
| Anotasi manusia | [panduan](./annotation-guide-v3.md), [template kosong](../../evaluation/quality-v3/independent_annotation_template.json) |
| Tes baru | [dokumen](../../tests/knowledge/test_document_search.py), [guardrail arsip](../../tests/knowledge/test_scope.py), [integrasi model](../../tests/knowledge/test_scope_integration.py), [aritmetika/freeze](../../tests/knowledge/test_quality_v3.py), [preprocessing](../../tests/corpus/test_review_v3.py) |

Enam berkas implementasi yang dipakai saat pengukuran tersimpan byte-identik
di [locked-code](../../evaluation/quality-v3/locked-code/). SHA-256 harus tetap
cocok dengan lock akhir. Runner aktif memiliki pemetaan lokasi arsip yang
eksplisit; pemindahan tidak memberi izin mengubah kode kandidat atau label.
Snapshot runner sebelum pengarsipan juga disimpan. Tidak ada kode kandidat
arsip yang diimpor oleh paket runtime.

## C. Audit preprocessing dan metadata

Seluruh 15 PDF asli, korpus v1/v2, tiga profil v2, 75 kueri/label lama serta
hasil audit/benchmark sebelumnya masuk pemeriksaan SHA-256 terhadap **70
artefak historis**. Berkas chunk lama yang dilampirkan pengguna tetap utuh;
130 chunk historis bukan profil final token-aware yang baru.

Renderer alternatif PDFium berhasil dipakai untuk inspeksi yang sebelumnya
terhambat. [Bukti visual](../../evaluation/quality-v3/visual_review.json)
merekam hash sepuluh render halaman dan hash PDF asli. Renderer adalah tool QA
opsional, bukan dependency runtime atau perubahan lockfile proyek. Inspeksi
dilakukan asisten; belum merupakan persetujuan pemilik sumber atau anggota tim
independen.

| Sumber | Halaman diperiksa | Koreksi terhadap v2 | Yang dipertahankan / tersisa |
|---|---|---|---|
| DOC-11 | 1, 2, 5, 6, 9 dari 16 | 25 pemenggalan baris digabung pada document-control notice, objectives dan definisi yang terverifikasi | Semua token tetap sama; Figure 1.1/1.2, daftar isi, tabel revisi, contoh email dan screenshot tidak dikarang atau direkonstruksi; hubungan sel tabel pada teks rata belum sepenuhnya aman |
| DOC-13 | Semua lima halaman revisi 2024 | Enam pemenggalan baris pada judul depan, jabatan eksekutif dan history | Klausul, butir huruf, istilah teknis, tautan dan kontak tetap sama; catatan kualitas layout yang diperiksa dapat ditutup |
| 13 sumber lainnya | Tidak mengubah teks v2 | Identik byte | DOC-09/10 tetap DRAFT, placeholder dan catatan pengesahan tetap dipertahankan |

Koreksi whitespace memverifikasi `before.split() == after.split()`; tidak ada
penghapusan, penambahan, penggantian atau pertukaran token substantif terhadap
v2. DOC-11 tetap `review_required`; DOC-09/10 tetap DRAFT dan berflag. DOC-13
menjadi `review_required=false` setelah seluruh halaman diperiksa. Ini menutup
masalah layout yang diketahui, bukan mengesahkan kebijakan Oregon State sebagai
SOP CERTAN.

| Profil v3 | Chunk | Token min / median / maksimum | Pelanggaran batas | Page span tepat / chunk dua PDF native |
|---|---:|---|---:|---:|
| `v3_t96_w10` | 487 | 19 / 84 / 96 | 0 | 126 / 127 |
| `v3_t120_w12` | 378 | 20 / 107,5 / 120 | 0 | 96 / 97 |
| `v3_t96_w0` | 413 | 6 / 84 / 96 | 0 | 105 / 108 |

Nomor halaman ditambahkan hanya jika seluruh urutan kata chunk mempunyai satu
pencocokan persis pada teks PDF setelah page furniture terverifikasi dibuang.
Metadata mencatat `page_start`, `page_end`, `source_word_start`,
`source_word_end_exclusive`, dan cara alignment. Offset kata merujuk stream
kata PDF yang telah dibersihkan, bukan byte PDF. Jika kecocokan ambigu/tidak
ditemukan, kolom halaman tidak diisi. Halaman untuk 13 sumber hasil ekstraksi
HTML dari PDF gambar juga tidak ditebak.

Metadata minimum setiap chunk: ID dokumen, judul, publisher, URL terverifikasi,
jenis dokumen, section, indeks chunk, versi korpus, flag review, hash PDF dan
hash teks. Revisi sumber ditambahkan bila tersedia: DOC-11 `2022-01-19` dan
DOC-13 `2024-08-06`. Status DRAFT tetap dicatat. URL historis DOC-13 dipertahankan
sebagai provenance terpisah; URL utama tetap menunjuk PDF 2024 yang telah
diverifikasi pada audit v2. Lisensi yang diketahui dipertahankan, yang tidak
diketahui tidak diisi dengan klaim buatan.

Justifikasi 96 token/10 kata overlap, model multilingual 384 dimensi, batas
128 token termasuk dua special token, coverage serta trade-off ablasinya tetap
merujuk [analisis konfigurasi v2](./directed-improvement-v2.md). Normalisasi
baru tidak membuktikan ukuran/overlap itu optimal. Windows dan Open vSwitch
masih dominan; tidak ada penambahan sumber, SOP lokal, inventaris atau telemetri.

## D. Audit retrieval dan perubahan ranking

Audit implementasi awal menunjukkan `search()` mengembalikan chunk, lalu
threshold opsional memfilter setiap chunk. Ia tidak mempunyai keputusan
abstention per kueri, pemeriksaan dependency data aktual, atau jaminan satu
dokumen per hasil. Runner v2 berbeda: mengambil 100 chunk, dedup dokumen,
kemudian memakai cosine dokumen pertama untuk gate kueri. Perbedaan semantik
API dan benchmark itu sekarang didokumentasikan secara eksplisit.

Opsi dokumen akhir menggunakan max cosine dari 100 kandidat chunk, tanpa
reranking. Karena identitas dokumen dan sumber dipertahankan, duplikasi chunk
tidak mengisi semua slot Top-k. Namun candidate depth tetap terbatas; ini
bukan pencarian exhaustive seluruh 15 dokumen dan bukan perbaikan otomatis
kegagalan Top-1 yang telah ada.

Kandidat judul memakai `(1-alpha) * best_chunk_cosine + alpha * title_cosine`.
Development memilih `alpha=0,2` dari 0,2/0,4/0,6. Judul menambah sinyal tujuan
dokumen secara umum tanpa mengulang bonus intent v2. Peningkatan pada validation
tidak bertahan meyakinkan pada final test: delta MRR tanpa gate final =
**+0,0237**, bootstrap CI95 **[-0,0409; +0,0911]**. Batas bawah tidak positif,
sehingga syarat adopsi gagal. Tidak ada penyesuaian alpha dari final test.

### Diagnosis kegagalan WiFi

[Regresi 75 kueri lama](../../evaluation/quality-v3/historical_75_comparison.json)
dijalankan setelah pemilihan parameter selesai dan tidak dipakai memilih kandidat.
Untuk kueri WiFi historis, v2 dan v3 tetap mempunyai DOC-13 Top-1 dengan cosine
0,7709 dan DOC-01 urutan 6 dengan cosine 0,5266. Kandidat judul hanya mengangkat
DOC-01 ke urutan 5. Tidak ada pengecualian yang memaksanya menjadi Top-1.

Dalam 100 kandidat v3, DOC-13 menyumbang 21 chunk dan DOC-01 delapan; DOC-05
bahkan 26. Dominasi chunk dapat membatasi keberagaman pool, tetapi DOC-01
sebenarnya sudah ditemukan. Setelah dedup, DOC-13 tetap mempunyai cosine
tertinggi: masalah tidak dapat dijelaskan hanya oleh duplikasi. Istilah WiFi,
Internet dan access point cocok secara semantik dengan kebijakan jaringan,
sementara kueri menghendaki langkah diagnosis. Batas chunk mengubah representasi
yang dibandingkan, tetapi koreksi whitespace v3 tidak menyelesaikan perbedaan
intent dan ambiguitas istilah tersebut. Threshold tinggi tidak dapat memilih
dokumen benar yang justru memiliki cosine lebih rendah.

Pada empat kueri WiFi final, baseline Top-1 relevan 0/4 dan kandidat judul 1/4;
MRR masing-masing 0,2896 dan 0,4315. Ini menunjukkan sebagian perbaikan lokal,
tetapi belum bukti penyelesaian kategori WiFi atau peningkatan keseluruhan yang
cukup untuk adopsi. Tidak ada tuning lanjutan pada empat kueri ini.

## E. Guardrail, false acceptance dan false rejection

Guardrail menggabungkan struktur permintaan dengan dependency yang tidak ada
dalam korpus statis. Contohnya lookup status tiket memerlukan rekaman aktual;
pertanyaan **cara** mengumpulkan log tidak otomatis ditolak. Institusi dicocokkan
dengan inventory publisher/alias yang berasal dari sumber, tanpa daftar dokumen
favorit. Kesesuaian judul dipertimbangkan sebagai sinyal cakupan, tetapi
development memilih cutoff `0,0`, sehingga sinyal judul **tidak dipakai** pada
guard akhir eksperimen. Ini bukan verifier yang membuktikan isi jawaban tersedia.

Grid development memilih cosine **0,6** dengan toleransi tambahan FRR maksimal
1/18 pada development. Balanced error yang seri dipecahkan dengan FAR lebih
kecil. Pilihan tersebut menghasilkan overfitting pada sampel development:
FAR 0/18 dan FRR 1/18, lalu FRR meningkat tajam pada dua split berikutnya.

| Split / kebijakan | FAR | FRR | OOD rejection | Penerimaan positif |
|---|---:|---:|---:|---:|
| Development baseline 0,5 | 7/18 = 38,89% | 0/18 | 61,11% | 100% |
| Development guard terpilih | 0/18 | 1/18 = 5,56% | 100% | 94,44% |
| Validation baseline 0,5 | 9/18 = 50% | 0/18 | 50% | 100% |
| Validation guard terpilih | 0/18 | 5/18 = 27,78% | 100% | 72,22% |
| Final baseline 0,5 | 18/24 = 75% | 0/24 | 25% | 100% |
| Final guard terpilih | 2/24 = 8,33% | 7/24 = 29,17% | 91,67% | 70,83% |

Final guard mempunyai Wilson CI95 FAR [2,32%; 25,85%] dan FRR
[14,91%; 49,17%]. Paired bootstrap delta FAR = -66,67 poin persentase,
CI95 [-83,33; -45,83]; delta FRR = +29,17 poin, CI95 [+12,50; +50,00].
Penurunan FAR didukung pada sampel sintetis ini, tetapi disertai regresi besar
pada kueri relevan. Kinerja keseluruhan tidak dinyatakan lebih baik.

### Analisis kesalahan final

- **Lima penolakan positif karena cosine <0,6:** diagnosis driver WiFi,
  restart WlanSvc, handoff service desk DRAFT, pemulihan insiden DRAFT, dan
  pelaporan keamanan Utah. Beberapa di antaranya sudah mempunyai dokumen Top-1
  yang benar. Threshold menolak sumber benar karena skor bukan probabilitas.
- **Dua penolakan positif karena parser institusi:** pertanyaan prosedur WLAN
  umum menyebut Universitas Kencana tetapi secara eksplisit tidak meminta SOP
  kampus; kata SOP yang dinegasikan masih memicu pemeriksaan otoritas. Nama
  lengkap Indiana University Bloomington juga menghasilkan fragmen nama kampus
  yang tidak dikenali. Keduanya menunjukkan struktur regex belum cukup kokoh.
- **Dua OOD diterima:** pertanyaan aturan WiFi dengan nama universitas seluruhnya
  huruf kecil (DOC-13, cosine 0,7012), dan prosedur neraca usaha tahunan
  (DOC-10, 0,6348). Parser proper-name tidak menangani huruf kecil; kesamaan
  bahasa administrasi dokumen memberi false acceptance lintas domain.
- **Delapan OOD data aktual ditolak**, tetapi sebagian ditolak karena cosine
  rendah, bukan karena dependency terdeteksi. Jadi keberhasilan 8/8 tidak
  membuktikan seluruh bentuk permintaan data aktual dikenali secara struktural.

Aturan tidak diperbaiki menggunakan final test tersebut. Hasil negatif tetap
disimpan. Guard tidak diselamatkan dengan memilih threshold lain setelah melihat
validation/final, dan tidak hanya mengambil komponen yang kebetulan berhasil.

### Contoh keluaran yang dapat diperiksa

| Jenis | Contoh dari final test | Hasil |
|---|---|---|
| True positive | `final_p05`, diagnosis resolusi nama DNS | ACCEPT; DOC-02 relevan |
| Wrong Top-1 | `final_p01`, manual/auto-connect WLAN | Diterima tetapi panduan WiFi bukan Top-1 |
| False negative | `final_p20`, handoff draf service desk | LOW_CONFIDENCE walaupun DOC-09 Top-1 relevan |
| Successful abstention | `final_o03`, lookup tiket tertentu | ABSTAIN; dependency rekaman tiket tidak tersedia |
| False positive / failed abstention | `final_o15`, kebijakan universitas yang tidak ada dalam korpus | ACCEPT dengan DOC-13 institusi lain |
| Failed abstention lintas domain | `final_o21`, neraca usaha | ACCEPT dengan DRAFT DOC-10 yang tidak mendukung pertanyaan |

## F. Protokol dan before/after pada benchmark yang sama

75 kueri historis beserta split dan ground truth tidak diubah. Studi baru
menambahkan 120 kueri: development 18 positif + 18 OOD, validation 18 + 18,
dan final test 24 + 24. Tidak ada kalimat kueri yang sama antarsplit atau dengan
75 kueri lama. Kedekatan pola/sumber tetap mungkin; ini bukan jaminan
independensi linguistik atau statistik penuh.

Parameter dan aturan adopsi dibekukan sebelum final test ditulis. Satu bug
parser nama lengkap ditemukan pada development dan diperbaiki **sebelum**
validation/final diobservasi. [Amendment](../../evaluation/quality-v3/development_amendment.json)
menghubungkan lock/results development pertama yang dipertahankan dengan
`lock-r2.json` dan `results_development_r2.json`. Final labels dibuat setelah
lock kedua, sebelum kedua observasi evaluation, lalu di-hash pada
[manifest final test](../../evaluation/quality-v3/final_test_manifest.json).
Tidak ada klaim validasi manusia independen. [Template anotasi](../../evaluation/quality-v3/independent_annotation_template.json)
berisi kueri, seluruh sumber dan kolom kosong, tanpa ranking, prediksi atau
label penulis. Belum ada anggota tim yang mengisinya.

Metrik berikut memakai ground truth yang sama pada setiap baris satu split.
Precision/Recall/MRR adalah makro atas kueri positif; penolakan memberi nilai
nol. FAR/FRR dinilai terpisah. `ABSTAIN` dan `LOW_CONFIDENCE` sama-sama dianggap
tidak menerima kueri. Benchmark menggunakan gate **per kueri**, berbeda dari
filter chunk pada CLI lama. MRR dibatasi kandidat 100 chunk.

| Split / arm | P@1 setelah gate | P@3 | R@3 | R@5 | MRR | FAR / FRR |
|---|---:|---:|---:|---:|---:|---|
| Validation semantic 0,5 | 0,7778 | 0,2963 | 0,8333 | 0,9444 | 0,8385 | 9/18; 0/18 |
| Validation guard 0,6 | 0,6111 | 0,2407 | 0,6667 | 0,7222 | 0,6528 | 0/18; 5/18 |
| Validation title 0,2 | 0,8333 | 0,3148 | 0,8889 | 1,0000 | 0,8889 | 9/18; 0/18 |
| Final semantic 0,5 | 0,7083 | 0,3194 | 0,9167 | 0,9583 | 0,8122 | 18/24; 0/24 |
| Final guard 0,6 | 0,5833 | 0,2500 | 0,7083 | 0,7083 | 0,6389 | 2/24; 7/24 |
| Final title 0,2 | 0,7500 | 0,3194 | 0,9167 | 0,9583 | 0,8358 | 18/24; 0/24 |
| Final title + guard | 0,5833 | 0,2500 | 0,7083 | 0,7083 | 0,6389 | 2/24; 7/24 |

`title` memakai gate cosine asli 0,5 pada dokumen terpilih, bukan ranking score.
Raw dan ranking score keduanya disimpan. Perbandingan title untuk adopsi
menggunakan MRR ranking tanpa gate, agar tidak mencampur efek ranking dan
abstention. CI95 final melintasi nol; kandidat tidak lolos. Guard juga tidak
lolos batas regresi maksimal 0,0556 yang ditetapkan sebelumnya.

Hasil 75 kueri historis untuk semantic v3 sama dengan v2 pada ketiga split
untuk P@1/P@3/R@3/R@5/MRR. Gate historis 0,5 juga tetap sama:

| Split historis | v2 → v3 R@3 | v2 → v3 MRR | v2 → v3 FAR | v2 → v3 FRR |
|---|---|---|---|---|
| Legacy 15 kueri | 0,8750 → 0,8750 | 0,8056 → 0,8056 | 0/3 → 0/3 | 0/12 → 0/12 |
| Development 30 kueri | 1 → 1 | 0,8426 → 0,8426 | 4/12 → 4/12 | 0/18 → 0/18 |
| Evaluation 30 kueri | 0,9444 → 0,9444 | 0,8750 → 0,8750 | 3/12 → 3/12 | 0/18 → 0/18 |

Angka final test baru tidak boleh dibandingkan langsung dengan angka evaluation
lama untuk mengklaim tren; distribusi dan tingkat kesulitan kuerinya berbeda.

### Per kategori pada final test

| Kategori | Positif | Semantic P@1 / R@3 / MRR | Guard P@1 / R@3 / MRR | Title P@1 / R@3 / MRR |
|---|---:|---|---|---|
| WiFi | 4 | 0 / 0,5000 / 0,2896 | 0 / 0,2500 / 0,0833 | 0,2500 / 0,5000 / 0,4315 |
| DNS/DHCP | 4 | 1 / 1 / 1 | 1 / 1 / 1 | 1 / 1 / 1 |
| VLAN/switching | 3 | 1 / 1 / 1 | 1 / 1 / 1 | 1 / 1 / 1 |
| Diagnosis lainnya | 3 | 0,6667 / 1 / 0,8333 | 0,6667 / 1 / 0,8333 | 0,6667 / 1 / 0,8333 |
| Network policy | 5 | 0,6000 / 1 / 0,7667 | 0,6000 / 0,8000 / 0,7000 | 0,6000 / 1 / 0,7667 |
| Incident management | 5 | 1 / 1 / 1 | 0,4000 / 0,4000 / 0,4000 | 1 / 1 / 1 |

OOD final terbagi delapan data aktual, delapan institusi, dan delapan di luar
domain; FAR guard masing-masing 0/8, 1/8, dan 1/8. Sinonim, singkatan teknis,
pertanyaan prosedural dengan konteks lokal, dan kasus ambigu dimasukkan dalam
kategori di atas. Ukuran tiap kategori sangat kecil.

### Latensi dan batas pengukuran

Final test mencatat median/P95 komponen semantic dokumen 198,31/365,87 ms;
guard 198,35/366,14 ms; title 322,74/625,27 ms. Waktu model load awal disimpan
terpisah. Cache model/judul dipanaskan sebelum kueri berlabel. Biaya arm disusun
dari waktu retrieval yang sama ditambah waktu komponen tiap strategi; ini
bukan pengulangan benchmark server terisolasi. Pengumpulan validation, final
dan tes model beriringan menambah contention CPU. Angka latensi bersifat
deskriptif; tidak digunakan untuk klaim keunggulan statistik performa.

## G. Pengujian, persistensi dan reproduksi

Suite akhir dengan `CERTAN_RUN_MODEL_TESTS=1` dan model cache asli menghasilkan
**220 passed**. Tes mencakup dedup/max/tie, validasi metadata, input invalid,
dependency query, pengecualian prosedural, tiga status keputusan arsip,
score cosine yang tidak berubah, cache invalidation, token-preservation,
alignment unik/ambigu, template arithmetic, baseline freeze dan hash arsip.
Integrasi model asli menguji encode ternormalisasi, upsert, pencarian,
penutupan/pembukaan ulang database serta kandidat abstention yang diarsipkan.

Audit proses terpisah membuka ketiga Chroma v3: 487, 378 dan 413 record.
Seluruh ID/teks/metadata cocok JSON; embedding berbentuk N×384, finite dan
bernorma satu. Chunk diregenerasi deterministik dari sumber v3; word coverage,
cap token, hash PDF/TXT serta halaman/offset dicek. Seluruh 70 artefak lama
tetap utuh. Config HNSW cosine dan model tetap mengacu konfigurasi terverifikasi
pada [audit v3](../../evaluation/quality-v3/verification.json) dan
[justifikasi v2](./directed-improvement-v2.md).

`uv lock --check` dan `git diff --check` lulus. Pemindaian pola token API,
GitHub/AWS dan private key tidak menemukan kecocokan kredensial berkeyakinan
tinggi pada berkas repository yang diperiksa. Pemindaian pola bukan bukti
ketiadaan semua jenis rahasia. File environment/model/database yang diabaikan
Git tidak dipromosikan sebagai deliverable.

Perintah yang dipertahankan pada runtime:

```powershell
uv run --frozen --no-sync python -m proyek_certan.knowledge.cli search --db .local/chroma-corpus-m3-v3_t96_w10 --document-level --candidate-depth 100 --top-k 5 --query "Bagaimana diagnosis DNS pada klien?"
```

Reproduksi guard yang **ditolak**, untuk memeriksa bentuk keputusan saja:

```powershell
uv run --frozen --no-sync python evaluation/guard_candidate_cli_v3.py --db .local/chroma-corpus-m3-v3_t96_w10 --query "Tampilkan status terbaru tiket TKT991122."
```

Output kedua selalu diberi label eksperimen/tidak diadopsi. Tidak ada opsi
guard otomatis pada CLI runtime. Threshold produksi tidak ditetapkan.

Data evaluation dan final test ditulis create-once. Skrip menolak penimpaan
label, observasi dan hasil. Jangan menjalankan ulang pemilihan atau membuat
retry final untuk mencari skor lebih baik. Pada checkout ini, gunakan hasil
yang disimpan dan audit/replay aritmetika. Untuk eksperimen lanjutan perlu
versi studi, protokol, dan final test baru yang belum dipakai untuk tuning.
Indeks/cache berada di direktori lokal terabaikan; path masing-masing ada
pada laporan korpus. Builder v3 memerlukan path indeks baru dan sengaja
menolak menimpa hasil final yang telah ada.

[Verifikasi akhir](../../evaluation/quality-v3/final_verification.json)
menghitung ulang keputusan, metrik dan confidence interval dari observasi yang
disimpan, tanpa mengulang retrieval final test. Tiga proses CLI smoke terpisah
memverifikasi hasil dokumen DNS, ABSTAIN atas lookup tiket, dan LOW_CONFIDENCE
atas pertanyaan memasak; [keluaran lengkap](../../evaluation/quality-v3/runtime_smoke.json)
mempertahankan label eksperimen untuk guard yang ditolak. Anotasi manusia yang
telah selesai masih nol.

## H. Known limitations

- Korpus tetap 15 sumber eksternal, 13 Inggris dan dua Indonesia; belum
  membuktikan representativitas insiden CERTAN/IT Del. Tidak ada dokumen baru.
- DOC-09/10 DRAFT; hubungan tabel dan diagram DOC-11 belum ditransformasikan
  seluruhnya menjadi teks yang aman. Tidak ada isi gambar/tabel yang dikarang.
- Benchmark sintetis satu penulis. Final test terpisah dari tuning, tetapi
  penulisnya mengetahui desain; template manusia masih kosong.
- Pemisahan semantik diagnosis/kebijakan dan ketepatan Top-1 WiFi belum selesai.
- Guard gagal pada negasi, variasi nama institusi dan generalisasi threshold.
  Menaikkan cosine tidak menghasilkan abstention yang sekaligus presisi dan
  mempertahankan cakupan kueri relevan.
- Kandidat judul belum memberi CI peningkatan MRR yang positif pada final.
  Banyak chunk dan candidate depth tetap dapat mempengaruhi hasil; HNSW
  bersifat aproksimasi dan urutan jauh dapat bervariasi.
- Tidak ada LLM, RAG agent, FastMCP, frontend, monitoring langsung atau
  pengesahan jawaban operasional.

## I. Kesesuaian terhadap rubrik T03

| Komponen | Bukti yang kini tersedia | Kekurangan terhadap deskriptor 100 |
|---|---|---|
| Korpus/preprocessing 25% | Audit visual terarah, v3 tanpa kehilangan token, provenance/hash, page span exact, tiga profil/token cap dan alasan overlap | Representativitas lokal belum dibuktikan; DRAFT dan sebagian tabel/diagram DOC-11 masih terbatas |
| Embedding/Chroma 45% | Encoder multilingual nyata, N×384/unit norm, metadata wajib konsisten, tiga indeks terisolasi/persisten, reopen proses baru, regenerasi deterministik | Kesesuaian model alternatif belum dibandingkan; halaman hanya ketika benar-benar dapat dipetakan; tidak mengklaim semua sumber telah disahkan |
| Retrieval/OOD/analisis 30% | API dokumen, 120 kueri baru + 75 historis, development/validation/final, before/after dan CI, error per kategori, template anotasi buta, penolakan adopsi yang jujur | OOD baseline masih tinggi pada challenge set; guard merugikan positif; Top-1 WiFi belum baik; validasi manusia belum dilakukan |

## J. Keputusan akhir

**NOT READY untuk finalisasi dengan klaim seluruh deskriptor 100 terpenuhi.**
Yang dipertahankan adalah pembersihan terverifikasi sebagai korpus v3 terpisah,
metadata/halaman yang dapat dibuktikan, API dokumen tanpa reranking, tes dan
paket evaluasi. Indeks final lama dan perilaku default semantik tetap utuh.
Guardrail dan reranking judul tidak diadopsi; implementasi serta hasil negatif
diarsipkan untuk review. Milestone 1/2 tidak diubah. Tidak ada commit, push,
merge atau pull request.

Langkah berikut yang memerlukan bukti baru adalah anotasi oleh anggota tim,
review domain/otoritas SOP dan evaluasi baru yang benar-benar belum dipakai
untuk desain. Temuan final test ini tidak dipakai untuk diam-diam memperbaiki
aturan dan menilai ulang pada kueri yang sama.
