# T03: audit korpus dan evaluasi retrieval terarah v2

Tanggal verifikasi: 5 November 2026. Cakupan: Milestone 3 saja.

## Keputusan dan hasil utama

Bukti audit dan evaluasi diperkuat, tetapi **belum ada dasar untuk menyatakan
seluruh deskriptor nilai 100 sudah terpenuhi**. Lima sumber berflag diperiksa,
tiga teks diperbaiki secara konservatif, dan seluruh profil dihasilkan ulang
serta diverifikasi pada indeks terpisah. Benchmark bertambah dari 15 menjadi
75 kueri. Default semantic retrieval dan indeks final lama tetap dipertahankan.
Strategi intent tidak diadopsi karena tidak meningkatkan hasil development dan
evaluation. Tidak ada commit, push, merge, perubahan Milestone 1/2, maupun
penambahan LLM, agent RAG, frontend, atau FastMCP.

| Bukti | Sebelum | Sesudah |
|---|---|---|
| Dokumen | 15, lima catatan review | 15; DOC-06 selesai untuk masalah formatter yang diketahui; empat dokumen masih memerlukan review |
| Profil 96 token/10 kata overlap | 484 chunk | 486 chunk pada `m3-reviewed-v2`, indeks terpisah |
| Perubahan teks | Belum diperbaiki | DOC-06: tiga pemisah baris; DOC-11: 16 folio dihapus; DOC-13: empat running header dihapus, 74 baris prosa disambung |
| Benchmark tetap | 12 positif + 3 OOD | File, label, dan hasil lama tetap identik secara SHA-256 |
| Pengujian tambahan | Belum ada split terpisah | Development: 18 positif + 12 OOD; evaluation: 18 positif + 12 OOD |
| Recall@3 / MRR pada benchmark lama | 0,8750 / 0,8056 | 0,8750 / 0,8056 untuk korpus v2 |
| Top-1 relevan pada benchmark lama | 8/12 | 8/12 untuk korpus v2 |
| OOD threshold 0,5 | 0/3 salah diterima | Pada evaluation baru: v1 2/12, v2 3/12 salah diterima |
| Kandidat metadata/intent | Belum diuji | Ditolak menurut aturan adopsi yang dibekukan; kode hanya arsip eksperimen |

Angka lintas kumpulan kueri tidak boleh disebut peningkatan akurasi. Perbandingan
before/after di laporan ini selalu memakai kueri dan ground truth yang sama.

## 1. Audit korpus dan provenance

[Audit sumber](../../evaluation/source_review_v2.json) merekam SHA-256 teks
sebelum/sesudah, PDF lokal, snapshot HTML, pemeriksaan halaman, dan pemeriksaan
ulang URL resmi. [Skrip audit sumber](../../evaluation/audit_sources_v2.py)
menghitung ulang hasil ekstraksi; ia tidak sekadar mempercayai flag `verified`
pada laporan terdahulu. [Laporan korpus](../../evaluation/reviewed_corpus_v2.json)
menghubungkan setiap TXT, dokumen sumber, profil chunk, dan database.

| Dokumen | Pemeriksaan terhadap sumber | Tindakan aman | Masalah tersisa |
|---|---|---|---|
| DOC-06 | Isi HTML resmi Open vSwitch cocok dengan teks awal; contoh native VLAN diperiksa | Pisahkan pengantar, dua prompt `ovs-vsctl`, dan prosa berikutnya; urutan seluruh token identik | Ini FAQ VLAN Open vSwitch, bukan panduan semua merek switch fisik |
| DOC-09 | Ekstraksi ulang HTML resmi OPS-01 identik; DRAFT dan placeholder ada pada sumber | Tidak mengubah teks | SLA indikatif, placeholder institusi, dan otoritas pengesahan belum selesai |
| DOC-10 | Ekstraksi ulang HTML resmi INC-02 identik; DRAFT dan placeholder ada pada sumber | Tidak mengubah teks | Target/deadline indikatif dan pengesahan belum selesai |
| DOC-11 | PDF resmi unduhan ulang identik byte dengan PDF lokal; 16 halaman; TXT identik dengan ekstraksi awal | Hapus hanya angka folio 1 sampai 16 yang diverifikasi pada tiap halaman | Hard wrap, daftar isi, tabel Figure 1.1 halaman 5, workflow halaman 6, dan gambar antarmuka belum direkonstruksi |
| DOC-13 | PDF lokal lima halaman revisi 6 Agustus 2024 cocok dengan teks awal; header awal halaman diperiksa | Hapus empat running header, sambung 74 kelanjutan prosa tanpa mengganti urutan kata; nomor klausul tetap ada | Front matter/kontak dan ketepatan urutan baca visual belum disahkan; URL historis berbeda versi |

**Temuan provenance DOC-13:** URL PDF pada manifest lama saat diperiksa ulang
menyajikan revisi 2016, empat halaman. [Halaman kebijakan resmi](https://policy.oregonstate.edu/UPSM/08-010_university_network_administration)
mencantumkan revisi 2024 dan menautkan [PDF 2024](https://policy.oregonstate.edu/sites/policy.oregonstate.edu/files/08-010%20Network%20Admin%20080624.pdf).
Audit mengunduh tautan dari halaman resmi dan membuktikan hash byte cocok
dengan PDF lokal. Metadata chunk v2 sekarang menggunakan URL PDF 2024 sebagai
`source_url`, menyimpan URL lama pada `historical_source_url`, dan mencatat
`source_revision=2024-08-06`. [Koreksi provenance](../../evaluation/source_provenance_v2.json)
terikat pada hash PDF lokal. Manifest, metadata indeks, serta hasil benchmark
v1 tetap dipertahankan. Tidak ada penggantian teks 2024 dengan teks 2016 hanya
untuk menyamakan URL.

Koreksi URL dilakukan setelah audit lanjutan atas hasil awal v2; koreksi ini
hanya menyentuh provenance, tanpa mengganti teks, label, aturan intent atau
rumus ranking. Ketiga indeks dibangun ulang pada path bersufiks `-provenance`,
kemudian benchmark dijalankan kembali pada ground truth tetap. Indeks v2 awal
tidak ditimpa. Temuan versi URL tidak diperlakukan sebagai alasan tuning.

Audit akhir menemukan teks dan ID chunk sama dengan indeks v2 sebelum koreksi
URL; selisih absolut maksimum embedding tersimpan **0,0** pada ketiga profil.
Metrik setiap kueri, ringkasan tiap split, threshold, serta FAR/FRR kelima arm
juga sama sebelum dan sesudah koreksi provenance.

Penghapusan folio DOC-11 tidak menghapus pemberitahuan document control milik
UCF. Hasil normalisasi adalah turunan teks untuk eksperimen akademik, bukan
versi kebijakan baru yang disahkan UCF. Status `DRAFT` DOC-09/10 tetap ada pada
teks dan metadata setiap chunk terkait. Flag `review_required` tetap aktif
untuk DOC-09, DOC-10, DOC-11, dan DOC-13. DOC-06 dibersihkan hanya dari masalah
formatter yang telah diketahui; ini bukan sertifikasi visual seluruh dokumen.

[DOC-07 dalam korpus v2](../../data/corpus/processed/reviewed-v2/DOC07_Packet_Loss.txt)
tetap identik byte dengan teks baseline. Sebelas dari 15 TXT tidak berubah.
Lima belas PDF asli, TXT baseline, dan JSON chunk lama dipertahankan.

Tidak tersedia Poppler lokal; upaya renderer PyMuPDF sebelumnya terhalang
Windows Application Control. Pemeriksaan `pypdf` membuktikan kesesuaian teks
dan batas halaman, bukan ketepatan seluruh tata letak. Tabel/diagram ambigu
dipertahankan dan dilaporkan; tidak ada klaim audit visual menyeluruh.

### Representativitas yang dapat dipertanggungjawabkan

| Kelompok kebutuhan | Dokumen | Cakupan dan batas |
|---|---|---|
| Diagnosis jaringan | DOC-01 sampai DOC-08 | WiFi, DNS, DHCP server/client, TCP/IP, VLAN, packet loss, autentikasi; dominan Windows dan satu FAQ Open vSwitch |
| Penanganan insiden | DOC-09 sampai DOC-12 | Service desk, pemulihan, eskalasi, insiden keamanan; dua prosedur berbahasa Indonesia masih DRAFT |
| Kebijakan jaringan | DOC-13 sampai DOC-15 | Administrasi perangkat, penggunaan jaringan, pengecualian; berasal dari institusi berbeda |

Terdapat 13 dokumen Inggris dan dua Indonesia. Korpus cukup beragam untuk
demonstrasi topik T03, tetapi belum mewakili distribusi insiden CERTAN/IT Del.
Belum ada SOP lokal yang disahkan, log insiden nyata, inventaris perangkat,
telemetri, kredensial, harga, atau panduan konfigurasi semua vendor. Nama file
LAN switch tidak memperluas cakupan FAQ Open vSwitch menjadi Cisco IOS.
Kueri tentang keadaan langsung atau fakta institusi lokal diberi label OOD
meskipun istilahnya berdekatan dengan isi korpus.

## 2. Chunking, embedding, dan penyimpanan

[Model card resmi](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)
menyediakan representasi multilingual 384 dimensi dan batas masukan 128 token.
Pemilihannya sesuai kebutuhan kueri Indonesia terhadap sumber Inggris/Indonesia.
[Sentence-BERT](https://arxiv.org/abs/1908.10084) mendasari perbandingan embedding
kalimat menggunakan cosine; [distilasi multilingual](https://arxiv.org/abs/2004.09813)
mendukung pemetaan lintas bahasa. Referensi tersebut mendukung pendekatan,
bukan membuktikan bahwa model ini paling baik untuk insiden CERTAN. Tidak ada
perbandingan model alternatif pada studi ini.

Tokenizer asli menghitung dua special token, dengan `truncation=False`.
Profil 96 memiliki kapasitas isi maksimum 94 token dan margin 32 terhadap
batas model; profil 120 memiliki kapasitas isi 118 dan margin 8. Tujuan batas
tersebut adalah mencegah truncation dan menjaga fokus potongan. Seluruh chunk
akhir diperiksa ulang, bukan diperkirakan dari jumlah kata. Peringatan tokenizer
saat mencoba potongan sementara yang terlalu panjang bukan bukti chunk akhir
melampaui batas: maksimum akhir masing-masing 96 dan 120.

[Chunker](../../src/proyek_certan/corpus/chunking.py) mempertahankan heading,
mengelompokkan section pendek berdekatan, mengutamakan batas baris/paragraf,
lalu memilih batas kata yang muat. Overlap hanya di dalam kelompok section,
dikurangi bila diperlukan agar proses tetap maju. Kata tunggal yang tidak
muat menyebabkan error eksplisit. Rekonstruksi urutan kata memeriksa tidak ada
kata hilang atau tertukar. Grouping section dapat mencampur beberapa subtopik;
metadata section gabungan memperlihatkan hal tersebut.

| Profil v2 | Batas token termasuk special | Overlap kata | Chunk | Token min/median/maks | Pengulangan kata terhadap sumber |
|---|---:|---:|---:|---|---:|
| `v2_t96_w10` | 96 | 10 | 486 | 19 / 84 / 96 | 18,89% |
| `v2_t120_w12` | 120 | 12 | 378 | 20 / 107 / 120 | 16,38% |
| `v2_t96_w0` | 96 | 0 | 412 | 6 / 85 / 96 | 0% |

Overlap 10 **kata**, bukan 10 token, adalah hipotesis untuk mempertahankan
konteks di perbatasan potongan dengan biaya pengulangan yang terukur.
Pengulangan dihitung sebagai total kata di chunk / 20.592 kata sumber minus
satu; bukan persentase overlap token per batas. Profil 96/10 menambah 74 chunk
(17,96%) terhadap 96/0 dan 108 chunk (28,57%) terhadap 120/12. Ablasi di bagian
berikut tidak membuktikan overlap 10 atau ukuran 96 optimal secara universal.
Pilihan 96/10 dipertahankan dari keputusan sebelum evaluasi baru agar tidak
memilih konfigurasi setelah melihat label evaluasi.

Modul [embedding](../../src/proyek_certan/knowledge/embeddings.py),
[vector store](../../src/proyek_certan/knowledge/vector_store.py), dan
[retrieval](../../src/proyek_certan/knowledge/retrieval.py) tetap terpisah.
Dokumen dan kueri memakai encoder yang sama, vektor float32 ternormalisasi.
[Verifikasi independen](../../evaluation/retrieval_study_verification_v2.json)
merekam commit model cache, hash bobot/tokenizer/config, versi paket, dimensi,
norma vektor tersimpan, dan konfigurasi koleksi yang benar-benar dibuka.

ChromaDB 1.5.9 memakai `PersistentClient`, koleksi `certan_knowledge`,
`embedding_function=None`, dan HNSW `space=cosine`; embedding dihitung eksplisit
oleh aplikasi. Nilai aktual: `ef_construction=100`, `ef_search=100`,
`max_neighbors=16`, `resize_factor=1.2`, `sync_threshold=1000`; telemetry
anonim dinonaktifkan. [Dokumentasi Chroma](https://docs.trychroma.com/docs/collections/configure)
menjelaskan bahwa HNSW melakukan pencarian aproksimasi dan cosine distance
adalah satu dikurangi cosine similarity. Karena itu skor aplikasi
`1 - distance` adalah cosine, bukan probabilitas relevansi.

Setiap profil mempunyai path database sendiri yang tercantum pada laporan
korpus. Build mengisi hanya koleksi kosong, menolak isi lama yang berbeda,
lalu memeriksa seluruh ID, teks, dan metadata. Audit proses terpisah membuka
ulang indeks dan memeriksa dimensi/norma vektor. Upsert mencegah ID duplikat,
tetapi tidak otomatis membersihkan ID dari versi korpus berbeda; pemisahan
path/version diperlukan. Indeks final lama berisi 484 record tetap utuh.

Metadata v2 mencakup `document_id`, `source`, `title`, `section`, `chunk_index`,
`source_url`, `review_required`, `publication_status` bila dinyatakan sumber,
`corpus_version`, `document_kind`, `publisher`, `source_pdf_sha256`,
`text_sha256`, `extraction_method`, `text_file`, `chunk_profile`, `review_note`,
dan `license_url` bila tersedia. Status publikasi atau lisensi yang tidak
diketahui tidak diisi dengan klaim persetujuan buatan. Offset halaman sumber
per chunk belum tersedia; lokasi utama berupa section dan indeks chunk.
DOC-13 juga mempunyai `historical_source_url` dan `source_revision`; URL yang
aktif untuk versi 2024 direkam langsung pada metadata chunk serta audit sumber.

## 3. Protokol dan ground truth

[Benchmark lama](./semantic-retrieval-benchmark.md) tetap menjadi baseline
historis. [Protokol](../../evaluation/retrieval_study_protocol_v2.json)
membekukan hash 15 TXT, tiga file chunk lama, label dan hasil benchmark lama,
serta aturan kandidat. [Label tambahan](../../evaluation/retrieval_study_labels_v2.json)
memiliki alasan relevansi dari sumber dan hash sumber anotasi.
[Skrip persiapan](../../evaluation/prepare_retrieval_study.py) tidak mengimpor
model/store atau membaca hasil retrieval dan menolak menimpa label/protokol.
Label yang ditemukan pada awal pekerjaan ini dipertahankan, bukan ditulis
ulang setelah hasil terlihat.

Independensi di sini berarti label ditentukan dari isi sumber sebelum run
retrieval yang tercatat, **bukan anotator manusia independen**. Kueri sintetis
dan anotasi dibuat oleh penulis yang sama; belum ada uji buta, kesepakatan
antar-anotator, atau sampel pengguna nyata. Split mencegah pemilihan threshold
dari evaluation, tetapi tidak menghilangkan kemiripan pola bahasa antar-split.

| Split | Positif | OOD | Pemakaian |
|---|---:|---:|---|
| Legacy | 12 | 3 | Regresi historis, tidak dipakai untuk memilih threshold |
| Development | 18 | 12 (8 dekat, 4 jauh) | Memilih threshold dari grid yang dibekukan |
| Evaluation | 18 | 12 (8 dekat, 4 jauh) | Mengukur generalisasi dengan aturan tetap |

Setiap split baru mencakup 15 dokumen, diagnosis, sinonim/parafrasa, prosedur
insiden, dan kebijakan jaringan. Label relevan berarti dukungan langsung
terhadap informasi yang ditanyakan; permintaan institusi tertentu harus cocok
dengan institusi itu. Relevansi topik DRAFT tidak mengesahkan isinya.

Masing-masing arm mengambil 100 chunk, lalu menduplikasi dokumen dihapus dengan
memilih chunk berskor tertinggi per `document_id`. Semua kueri mempunyai paling
sedikit lima dokumen berbeda. Recall@k = dokumen relevan ditemukan / seluruh
dokumen relevan; Precision@k = dokumen relevan di k teratas / k; MRR = rata-rata
kebalikan urutan dokumen relevan pertama. Metrik makro hanya atas kueri positif.
Recall/MRR OOD tidak didefinisikan; OOD dinilai melalui false acceptance.
MRR dibatasi kandidat 100 chunk, bukan seluruh koleksi secara exhaustive.

Threshold dipilih hanya pada development: minimalkan rata-rata FAR dan FRR;
jika seri, pilih FAR lebih kecil, kemudian threshold lebih rendah. Grid 0,00
sampai 0,90 berlangkah 0,05. FAR = OOD diterima / OOD; FRR = positif ditolak /
positif. Ambang menggunakan **cosine mentah dokumen terpilih**, tidak termasuk
bonus ranking. Kueri positif yang ditolak mendapat nol pada metrik gated.

Gate studi adalah keputusan menerima/menolak keseluruhan kueri dari skor
dokumen pertama. Dokumen sisanya tetap dinilai sebagai daftar ranking bila
diterima. Parameter CLI `--relevance-threshold` memfilter setiap chunk; hasil
CLI itu tidak identik dengan metrik gate kueri pada studi. Threshold 0,5 tidak
diaktifkan otomatis pada runtime.

## 4. Hasil before/after pada ground truth yang sama

Sumber angka: [hasil lengkap lima arm](../../evaluation/retrieval_study_results_v2.json).
Tabel ini menggunakan ranking tanpa gate; ambang untuk ketiga arm 96/10 adalah
0,5 dan tidak menolak kueri positif pada ketiga split sehingga metrik gated
sama pada arm tersebut.

| Split / arm | Recall@1 | Recall@3 | Recall@5 | Precision@1 | Precision@3 | Precision@5 | MRR |
|---|---:|---:|---:|---:|---:|---:|---:|
| Legacy v1 | 0,4861 | 0,8750 | 0,9167 | 0,6667 | 0,4167 | 0,2667 | 0,8056 |
| Legacy v2 | 0,4861 | 0,8750 | 0,9167 | 0,6667 | 0,4167 | 0,2667 | 0,8056 |
| Legacy v2 + intent | 0,5694 | 0,8750 | 1,0000 | 0,7500 | 0,4167 | 0,2833 | 0,8500 |
| Development v1 | 0,7407 | 1,0000 | 1,0000 | 0,7778 | 0,3889 | 0,2333 | 0,8704 |
| Development v2 | 0,6852 | 1,0000 | 1,0000 | 0,7222 | 0,3889 | 0,2333 | 0,8426 |
| Development v2 + intent | 0,6852 | 1,0000 | 1,0000 | 0,7222 | 0,3889 | 0,2333 | 0,8426 |
| Evaluation v1 | 0,7500 | 0,9444 | 1,0000 | 0,7778 | 0,3333 | 0,2111 | 0,8750 |
| Evaluation v2 | 0,7500 | 0,9444 | 1,0000 | 0,7778 | 0,3333 | 0,2111 | 0,8750 |
| Evaluation v2 + intent | 0,7500 | 0,9444 | 1,0000 | 0,7778 | 0,3333 | 0,2111 | 0,8750 |

Pembersihan tidak meningkatkan Recall@3 atau MRR pada evaluation. Development
MRR turun 0,0278 karena `dev_p14` (izin access point Oregon State) beralih dari
DOC-13 ke DOC-14 pada Top-1. Paired bootstrap 10.000 resample, seed 20261105,
memberi CI95 delta MRR [-0,0833; 0,0000]. Pada evaluation, delta Recall@3 dan
MRR v2-v1 keduanya 0, dengan CI95 [0; 0]. Normalisasi yang benar secara teks
tetap dapat mengubah batas chunk dan merugikan ranking.

### Threshold dan OOD

| Split / arm | Threshold dari development | False acceptance | False rejection | Top-1 relevan / positif |
|---|---:|---:|---:|---:|
| Legacy v1 / v2 | 0,50 | 0/3 | 0/12 | 8/12 |
| Development v1 | 0,50 | 4/12 (33,33%) | 0/18 | 14/18 |
| Development v2 | 0,50 | 4/12 (33,33%) | 0/18 | 13/18 |
| Evaluation v1 | 0,50 | 2/12 (16,67%) | 0/18 | 14/18 |
| Evaluation v2 | 0,50 | 3/12 (25,00%) | 0/18 | 14/18 |

Untuk v2 pada evaluation, Wilson CI95 FAR adalah [8,89%; 53,23%]; FRR
[0%; 17,59%]. Nol penolakan positif bukan jaminan FRR populasi nol.
OOD dekat salah diterima 2/8, OOD jauh 1/4. Dari semua kueri evaluation yang
diterima, 14/21 memiliki Top-1 relevan (66,67%): empat positif salah ranking
dan tiga OOD tetap diterima. Ini menunjukkan perbedaan antara mengenali cakupan
dan memilih dokumen yang benar.

OOD evaluation yang masih diterima oleh v2:

| ID | Informasi yang diminta | Hasil Top-1 | Cosine |
|---|---|---|---:|
| `eva_o04` | Persyaratan beasiswa CERTAN | DOC-13 | 0,5233 |
| `eva_o07` | IP laptop saat ini dan pemilik MAC tertentu | DOC-15 | 0,5569 |
| `eva_o08` | Apakah tiket CERTAN tertentu sudah ditutup | DOC-11 | 0,6713 |

Pada v1 hanya dua kueri terakhir diterima. Tambahan false acceptance beasiswa
setelah pembersihan adalah regresi nyata pada sampel ini dan dicatat tanpa
mengubah label. Development juga salah menerima permintaan Cisco IOS, bandwidth
langsung, pemilik tiket, dan subnet lokal. Dokumen prosedur atau kebijakan
tidak menyediakan fakta operasional tersebut.

| Threshold v2 pada development | Salah terima /12 | Salah tolak /18 | Balanced error |
|---|---:|---:|---:|
| 0,45 | 7 | 0 | 0,2917 |
| 0,50 | 4 | 0 | 0,1667 |
| 0,55 | 4 | 2 | 0,2222 |
| 0,60 | 3 | 6 | 0,2917 |
| 0,65 | 0 | 8 | 0,2222 |

Threshold 0,5 tetap terpilih menurut tujuan development yang dibekukan,
tetapi jauh dari pemisah OOD presisi tinggi. Menaikkan threshold mengorbankan
kueri yang seharusnya didukung dan tidak menyelesaikan seluruh ranking salah.
Tidak ada penyesuaian threshold setelah membaca hasil evaluation.

### Kegagalan WiFi

Kueri historis: “WiFi kampus tersambung tetapi internet tidak dapat diakses.
Bagaimana memeriksa koneksi nirkabel dan access point?” Ground truth tetap
DOC-01.

| Arm | DOC-13 rank / cosine mentah | DOC-01 rank / cosine mentah |
|---|---|---|
| v1 96/10 | 1 / 0,7374 | 6 / 0,5266 |
| v2 96/10 | 1 / 0,7709 | 6 / 0,5266 |
| v2 96/10 + intent | 1 / 0,7709 | 5 / 0,5266 |

Pada v1, chunk pemenang DOC-13 terutama definisi Internet/University Network.
Pada v2, pemenang beralih ke bagian 5.3 tentang aturan Wi-Fi. Kata Wi-Fi,
Internet, dan access point memiliki kedekatan semantik tinggi dengan kueri,
meskipun tujuan kebijakan berbeda dari langkah diagnosis. DOC-01 tetap masuk
kandidat 100 chunk, sehingga kegagalannya bukan semata dokumen tidak masuk
candidate pool. Pembersihan mengubah representasi potongan DOC-13 dan menaikkan
skor yang salah; menaikkan ambang tidak dapat memilih DOC-01 yang berskor lebih
rendah.

Dedup dokumen sudah diterapkan pada kedua arm; banyak chunk DOC-13 bisa
mengurangi keberagaman kandidat di kedalaman tetap, tetapi dedup saja tidak
menghilangkan keunggulan cosine DOC-13. Kandidat bonus 0,10 mengangkat DOC-01
ke urutan 5, masih di bawah DOC-13 dan di luar Top-3. Tidak ada bonus lebih besar
atau pengecualian DOC-01 yang ditambahkan setelah melihat kegagalan ini.

Kegagalan tambahan pada evaluation: `eva_p01` diagnosis WiFi melewatkan DOC-01
dalam Top-3; `eva_p05` TCP/IP memilih packet loss, `eva_p07` packet loss memilih
TCP/IP, dan `eva_p16` kebijakan Indiana memilih kebijakan WMU. Ini menunjukkan
kebingungan intent, topik berdekatan, dan otoritas institusi, bukan hanya satu
kata WiFi. MRR diagnosis evaluation 0,7917 (enam kueri), sinonim 0,8333 (tiga),
kebijakan 0,9000 (lima), prosedur insiden 1,0000 (empat); sampel kecil membatasi
interpretasi tiap kategori.

## 5. Eksperimen dan keputusan adopsi

Satu strategi diuji: ranking dokumen memakai bonus tetap 0,10 jika intent kueri
cocok dengan jenis dokumen dari judul sumber. Aturan umum memisahkan kata
diagnosis dan kebijakan; intent campuran/tidak dikenal kembali ke semantic.
Aturan tidak memakai ID dokumen, label relevansi, daftar jawaban kueri, atau
pengecualian per kueri. Cosine mentah tidak diubah. Bonus ranking disimpan
terpisah dalam `ranking_score` dan tidak dipakai untuk gate threshold.

Hash aturan dan klasifikasi metadata ada pada protokol. File aturan pernah
berada di paket runtime; setelah kandidat gagal, byte yang sama diarsipkan
sebagai [kandidat evaluasi](../../evaluation/metadata_intent_candidate.py).
Pemetaan lokasi arsip eksplisit masih memverifikasi hash asli. Runtime tidak
mengimpor kode eksperimen tersebut.

Syarat adopsi: batas bawah paired bootstrap CI95 delta Recall@3 **dan** MRR
harus positif pada development **dan** evaluation, serta FAR/FRR tidak naik.
Kandidat mempunyai delta 0 untuk kedua metrik pada kedua split baru; CI95
semuanya [0; 0]. MRR legacy naik 0,0444, tetapi CI95 [0; 0,1278] dan tidak
digunakan untuk meloloskan kandidat. **Kandidat ditolak.** Tidak ada tuning
lanjutan pada evaluation yang sudah terlihat.

Ablasi chunking menggunakan label sama, tanpa dipilih ulang dari evaluation:

| Profil | Development Recall@3 / MRR tanpa gate | Evaluation Recall@3 / MRR tanpa gate | Threshold dev | Evaluation Recall@3 / MRR setelah gate | FA / FR evaluation |
|---|---|---|---:|---|---|
| v2 96/10 | 1,0000 / 0,8426 | 0,9444 / 0,8750 | 0,50 | 0,9444 / 0,8750 | 3/12; 0/18 |
| v2 120/12 | 0,9815 / 0,8611 | 0,9444 / 0,8657 | 0,55 | 0,9444 / 0,8657 | 2/12; 0/18 |
| v2 96/0 | 0,9815 / 0,8519 | 1,0000 / 0,9630 | 0,65 | 0,3333 / 0,3333 | 1/12; 12/18 |

96/0 lebih baik untuk ranking evaluation tanpa gate; delta MRR 96/10 minus
96/0 = -0,0880, CI95 [-0,1759; -0,0093]. Ini bukti yang berlawanan dengan
klaim overlap selalu membantu. Threshold 96/0 yang dipilih development juga
menolak 12/18 positif evaluation. Ukuran chunk, overlap, dan kalibrasi harus
dinilai bersama. Data ini tidak mendukung klaim 96/10 optimal universal atau
pemilihan 96/0 setelah melihat evaluation. Pilihan default lama dipertahankan,
korpus v2 dan ketiga indeks baru tetap artefak eksperimen untuk ditinjau.

## 6. Reproduksi dan verifikasi

Jalankan dari root repository dengan environment proyek. Model/indeks baseline
harus tersedia sesuai [panduan awal](./semantic-search.md) dan
[eksperimen token lama](./token-aware-chunking.md). Database dan cache model
diabaikan Git; JSON korpus/hasil tersedia untuk pemeriksaan.

```powershell
# Jangan jalankan kembali prepare_retrieval_study.py: label/protokol sudah beku.
uv run --frozen --no-sync python evaluation/build_reviewed_corpus.py
uv run --frozen --no-sync python evaluation/audit_sources_v2.py --refresh
uv run --frozen --no-sync python evaluation/retrieval_study.py
uv run --frozen --no-sync python evaluation/audit_retrieval_study.py
$env:CERTAN_RUN_MODEL_TESTS = '1'
uv run --frozen --no-sync python -m pytest -q
uv lock --check
git diff --check
```

Build v2 yang diulang memverifikasi isi indeks lama dan meregenerasi TXT/chunk
deterministik; database yang berbeda tidak ditimpa. Laporan timestamp/hash
korpus yang baru mengharuskan benchmark dan audit dijalankan kembali berurutan.
Jika sumber upstream berubah, build berhenti untuk review; jangan memaksa
menyamakan teks atau mengubah label. `--refresh` memperbarui laporan pemeriksaan
URL resmi tanpa mengganti input studi.

Benchmark lama dijalankan melalui fungsi `run()` oleh audit v2 dan dibandingkan
dengan hasil beku. **Jangan menjalankan entrypoint skrip benchmark lama untuk
verifikasi baseline tetap**, karena entrypoint itu menulis ulang JSON hasil
historis. Audit menggunakan hasil dalam memori dan tidak menulis file lama.
HNSW dapat mengubah urutan jauh pada hasil mentah; kesamaan seluruh 100 posisi
tidak diklaim. Audit mensyaratkan kesamaan ringkasan, metrik setiap kueri,
perilaku threshold, dan Top-5 dokumen benchmark lama. Variasi urutan dokumen di
luar Top-5 dicatat pada laporan verifikasi, tanpa menulis ulang baseline.

Pada audit akhir, variasi tersebut terjadi pada kueri OOD `ood_weather` profil
lama 96/10: urutan/ketercakupan beberapa dokumen jauh dalam 100 chunk berbeda.
Top-5, metrik per kueri, ringkasan, dan perilaku threshold tetap sama. Variasi
ini dibuka dalam laporan verifikasi, bukan dihilangkan dengan mengulang run
sampai seluruh ranking kebetulan identik.

| Pemeriksaan aktual | Hasil |
|---|---|
| Regenerasi v2 | 486 / 378 / 412 chunk; 15 dokumen tiap profil; tidak ada chunk melampaui batas token |
| Sumber lima dokumen | HTML DOC-06/09/10 cocok; PDF DOC-11 identik; provenance DOC-13 ditelusuri ke revisi 2024 |
| Benchmark lengkap | Lima arm × 75 kueri; kalibrasi development terpisah; seluruh label tetap |
| Audit proses terpisah | Baseline lama utuh; regenerasi chunk, metadata, model, dan isi indeks diverifikasi |
| Suite penuh dengan model asli | **186 passed** dalam 38,02 detik, termasuk integration test embedding, upsert, persistence, pencarian dan koreksi provenance |
| Verifikasi dependency/format | `uv lock --check` lulus (133 paket); `git diff --check` dan pemeriksaan tautan Markdown lokal lulus |
| Batas cakupan | Milestone 1/2 tidak diubah; tidak ada komponen di luar T03 |

## 7. Pemetaan terhadap fokus rubrik

| Fokus / bobot | Bukti yang diperkuat | Batas klaim nilai 100 |
|---|---|---|
| Korpus, cleaning, alasan chunking / 25% | Audit lima sumber, koreksi token-preserving, cakupan topik, margin tokenizer, overlap dan ablasi terukur | Representatif terhadap topik demonstrasi, belum terhadap insiden nyata; empat review tersisa; visual tabel/diagram belum tuntas |
| Embedding, Chroma modular/persisten, metadata / 45% | Encoder multilingual, 384 dimensi/norma terverifikasi, model/config hashes, path terisolasi, metadata/versi/provenance, URL DOC-13 dikoreksi dengan hash sumber, reopen proses baru | Model alternatif belum dibandingkan; halaman/offset per chunk belum tersedia |
| Target retrieval, OOD, analisis / 30% | Baseline tetap, 60 kueri tambahan, label sumber, split development/evaluation, Recall/Precision/MRR/FAR/FRR, CI95, analisis kegagalan dan keputusan menolak kandidat | WiFi belum selesai; FAR evaluation v2 25%; label sintetis satu penulis; belum membuktikan penanganan OOD presisi tinggi |

Hasil pekerjaan ini adalah paket bukti yang dapat direproduksi dan dikritisi.
Pemenuhan nilai 100 tetap keputusan penilai; laporan tidak menyembunyikan
regresi, mengesahkan DRAFT, atau menggunakan similarity tinggi sebagai bukti
kebenaran. Tindak lanjut yang memerlukan data baru adalah review visual,
validasi SOP dan representativitas oleh pemilik domain, serta evaluasi pengguna
dengan ground truth baru yang belum dipakai untuk tuning.
